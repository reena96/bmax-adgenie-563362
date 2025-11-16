# AdGenie Frontend

Modern React TypeScript application with glassmorphism design system for AI-powered video ad generation.

## Tech Stack

- **React 18+** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Utility-first CSS
- **React Router DOM** - Client-side routing
- **Lucide React** - Icon library
- **Vitest** - Testing framework
- **React Testing Library** - Component testing

## Getting Started

### Install Dependencies

```bash
npm install
```

### Development

```bash
npm run dev
```

Runs the app at `http://localhost:3000`

### Build

```bash
npm run build
```

Builds the app for production to `dist/` folder.

### Test

```bash
npm run test
```

Runs all unit tests with Vitest.

### Lint

```bash
npm run lint
```

Runs ESLint on TypeScript files.

## Project Structure

```
app/
├── src/
│   ├── components/
│   │   ├── glass/           # Glassmorphism components
│   │   │   ├── GlassCard.tsx
│   │   │   ├── PrimaryButton.tsx
│   │   │   └── SecondaryButton.tsx
│   │   ├── landing/         # Landing page sections
│   │   │   ├── HeroSection.tsx
│   │   │   ├── FeaturesGrid.tsx
│   │   │   └── SocialProof.tsx
│   │   └── shared/          # Shared components
│   │       ├── TopBar.tsx
│   │       └── Footer.tsx
│   ├── pages/
│   │   ├── LandingPage.tsx
│   │   ├── LoginPage.tsx
│   │   └── SignupPage.tsx
│   ├── styles/
│   │   └── globals.css      # Global styles + glassmorphism
│   ├── test/
│   │   └── setup.ts         # Test setup
│   ├── App.tsx              # Main app with routing
│   └── main.tsx             # Entry point
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Design System

### Colors

- **Lightning Yellow** (`#FFEB3B`) - Primary CTA
- **Cosmic Dark** (`#0A0E27`) - Background
- **Mid Navy** (`#1A2332`) - Secondary background
- **Light Blue** (`#4FC3F7`) - Accent
- **White** (`#FFFFFF`) - Text

### Glassmorphism Components

All glass components use:
- `backdrop-filter: blur(10px)`
- Semi-transparent backgrounds
- Subtle borders with white/10 opacity
- Smooth transitions and hover effects

### Button States

- **Hover**: Lift effect (`translateY(-2px)`) + enhanced shadow
- **Active**: Return to baseline
- **Disabled**: 50% opacity, no transform

## Routes

- `/` - Landing page
- `/login` - Login page (placeholder)
- `/signup` - Signup page (placeholder)

## Performance

- Bundle size: ~60 kB gzipped
- Optimized for <2s load time
- Lighthouse score target: >80

## Accessibility

- Semantic HTML
- ARIA labels on interactive elements
- Keyboard navigation support
- Screen reader friendly

## Tests

All components have unit tests with React Testing Library. Tests cover:
- Component rendering
- User interactions
- Navigation
- Accessibility

Run tests with `npm run test`.
