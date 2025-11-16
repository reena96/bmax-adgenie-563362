# Authentication API Documentation

Complete API reference for authentication endpoints with examples.

## Table of Contents

1. [Authentication Flow](#authentication-flow)
2. [Endpoints](#endpoints)
   - [User Signup](#post-apiauthsignup)
   - [User Login](#post-apiauthlogin)
   - [Refresh Token](#post-apiauthrefresh)
   - [Get Current User](#get-apiauthme)
   - [Logout](#post-apiauthlogout)
   - [Request Password Reset](#post-apiauthrequest-password-reset)
   - [Reset Password](#post-apiauthreset-password)
   - [Google Sign-In](#post-apiauthgoogle-signin)
3. [Error Codes](#error-codes)
4. [Security Considerations](#security-considerations)

---

## Authentication Flow

```
1. User Signup/Login
   ↓
2. Receive access_token (15 min) + refresh_token (7 days)
   ↓
3. Use access_token in Authorization header for protected routes
   ↓
4. When access_token expires, use refresh_token to get new tokens
   ↓
5. Logout revokes all refresh tokens
```

---

## Endpoints

### POST /api/auth/signup

Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "John Doe"
}
```

**Password Requirements:**
- Minimum 8 characters
- Maximum 128 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

**Success Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "subscription_tier": "free"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "name": "John Doe"
  }'
```

**Error Responses:**
- `400 Bad Request`: Email already registered, weak password, or invalid email format
- `422 Unprocessable Entity`: Validation error

---

### POST /api/auth/login

Authenticate user and receive JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "John Doe",
    "subscription_tier": "free",
    "created_at": "2025-11-16T10:30:00Z",
    "updated_at": "2025-11-16T10:30:00Z"
  }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Rate Limiting:**
- Maximum 5 failed login attempts per IP per 15 minutes
- Returns `429 Too Many Requests` when limit exceeded

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `429 Too Many Requests`: Rate limit exceeded

---

### POST /api/auth/refresh

Exchange refresh token for new access and refresh tokens.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN_HERE"
  }'
```

**Token Rotation:**
- Old refresh token is revoked when new tokens are issued
- Prevents token theft/replay attacks

**Error Responses:**
- `401 Unauthorized`: Invalid, expired, or revoked refresh token

---

### GET /api/auth/me

Get current authenticated user information.

**Headers Required:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "subscription_tier": "free",
  "created_at": "2025-11-16T10:30:00Z",
  "updated_at": "2025-11-16T10:30:00Z"
}
```

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired access token, or user deleted

---

### POST /api/auth/logout

Logout user and revoke all refresh tokens.

**Headers Required:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Success Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Behavior:**
- Revokes all active refresh tokens for the user
- Forces re-login on all devices
- Access token remains valid until expiration (15 minutes)

**Error Responses:**
- `401 Unauthorized`: Invalid or expired access token

---

### POST /api/auth/request-password-reset

Request a password reset code.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200):**
```json
{
  "message": "If the email exists, a reset code has been sent"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/auth/request-password-reset \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

**Security Note:**
- Always returns success, even if email doesn't exist (prevents email enumeration)
- Reset code is 6 digits
- Code expires in 1 hour
- **MVP**: Code is logged to console (production will use email service)

---

### POST /api/auth/reset-password

Reset password using 6-digit code.

**Request Body:**
```json
{
  "email": "user@example.com",
  "reset_token": "123456",
  "new_password": "NewSecurePass123!"
}
```

**Success Response (200):**
```json
{
  "message": "Password reset successfully. Please login with your new password."
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "reset_token": "123456",
    "new_password": "NewSecurePass123!"
  }'
```

**Behavior:**
- Validates reset code (must be valid, not expired, not used)
- Validates new password strength
- Updates password
- Revokes all refresh tokens (forces re-login on all devices)
- Marks reset token as used (single-use)

**Error Responses:**
- `400 Bad Request`: Invalid or expired reset code, or weak password

---

### POST /api/auth/google-signin

Authenticate with Google OAuth (Phase 1 - Pending Implementation).

**Request Body:**
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE2NTY..."
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "John Doe",
    "subscription_tier": "free",
    "created_at": "2025-11-16T10:30:00Z",
    "updated_at": "2025-11-16T10:30:00Z"
  }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/auth/google-signin \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "GOOGLE_ID_TOKEN_FROM_CLIENT"
  }'
```

**Current Status:**
- Returns `501 Not Implemented` (placeholder for MVP)
- Full implementation requires `google-auth` library
- Will verify Google ID token signature
- Creates or links user account
- Returns same tokens as email/password login

---

## Error Codes

All error responses follow this format:

```json
{
  "error": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2025-11-16T10:30:00Z"
}
```

Common error codes:
- `INVALID_CREDENTIALS`: Wrong email or password
- `EMAIL_ALREADY_EXISTS`: Email is already registered
- `WEAK_PASSWORD`: Password doesn't meet requirements
- `INVALID_TOKEN`: JWT token is invalid or expired
- `TOKEN_EXPIRED`: Token has expired
- `RATE_LIMIT_EXCEEDED`: Too many failed login attempts
- `VALIDATION_ERROR`: Request body validation failed

---

## Security Considerations

### JWT Token Security
- **Access tokens**: 15-minute expiration (short-lived)
- **Refresh tokens**: 7-day expiration, stored hashed in database
- **Token rotation**: Refresh tokens are rotated on use
- **Revocation**: Logout revokes all refresh tokens

### Password Security
- **Bcrypt hashing**: 12 salt rounds
- **Never exposed**: Password hashes never returned in responses
- **Strength validation**: Enforced on signup and password reset

### Rate Limiting
- **Login attempts**: 5 failed attempts per IP per 15 minutes
- **Prevents brute force**: Automatic lockout after threshold

### Error Messages
- **No information leakage**: Generic "Invalid credentials" (doesn't reveal if email exists)
- **Consistent responses**: Password reset always returns success

### HTTPS
- **Production requirement**: All endpoints must use HTTPS
- **Secure cookies**: Use secure flag for cookies in production

### CORS
- **Configured origins**: Only allowed origins can access API
- **Credentials**: Allow credentials for cookie-based auth

### Headers
- **X-Content-Type-Options**: nosniff (prevent MIME sniffing)
- **X-Frame-Options**: DENY (prevent clickjacking)
- **X-XSS-Protection**: 1; mode=block (XSS filter)

---

## Swagger/OpenAPI Documentation

FastAPI auto-generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to test endpoints directly from the browser.
