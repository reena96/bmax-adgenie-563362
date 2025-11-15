"""
OAuth integration utilities for Google authentication.
Provides Google OAuth 2.0 client and helper functions.
"""
from typing import Optional, Dict, Any
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, status

from app.config import settings

# Initialize OAuth client
oauth = OAuth()

# Register Google OAuth provider
if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )


def get_google_authorization_url(redirect_uri: str) -> str:
    """
    Generate Google OAuth authorization URL.

    Args:
        redirect_uri: URI to redirect to after authorization

    Returns:
        Authorization URL string

    Raises:
        HTTPException: If Google OAuth is not configured
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured"
        )

    # Build authorization URL manually for better control
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }

    # Build query string
    query_parts = [f"{key}={value}" for key, value in params.items()]
    query_string = "&".join(query_parts)

    return f"{base_url}?{query_string}"


async def exchange_google_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
    """
    Exchange Google authorization code for access token and user info.

    Args:
        code: Authorization code from Google
        redirect_uri: Redirect URI used in authorization request

    Returns:
        Dictionary containing 'token' and 'userinfo' from Google

    Raises:
        HTTPException: If code exchange fails or Google OAuth is not configured
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured"
        )

    try:
        # Exchange code for token using authlib
        google_client = oauth.create_client('google')

        token = await google_client.authorize_access_token(code=code, redirect_uri=redirect_uri)

        # Get user info from Google
        userinfo = token.get('userinfo')

        if not userinfo:
            # If userinfo not in token, fetch it separately
            resp = await google_client.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
            userinfo = resp.json()

        return {
            'token': token,
            'userinfo': userinfo
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to exchange authorization code: {str(e)}"
        )
