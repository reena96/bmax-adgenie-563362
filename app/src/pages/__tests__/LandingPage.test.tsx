import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import LandingPage from '../LandingPage';

describe('LandingPage', () => {
  const renderLandingPage = () => {
    return render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>
    );
  };

  it('renders the landing page without errors', () => {
    renderLandingPage();
    expect(screen.getByRole('main')).toBeInTheDocument();
  });

  it('displays the hero section with headline', () => {
    renderLandingPage();
    expect(screen.getByText(/Create Professional Video Ads/i)).toBeInTheDocument();
    expect(screen.getByText(/with AI/i)).toBeInTheDocument();
  });

  it('displays the subheading', () => {
    renderLandingPage();
    expect(screen.getByText(/in Minutes, Not Hours/i)).toBeInTheDocument();
  });

  it('displays the Get Started CTA button', () => {
    renderLandingPage();
    const ctaButton = screen.getByRole('link', { name: /Get started for free/i });
    expect(ctaButton).toBeInTheDocument();
    expect(ctaButton).toHaveAttribute('href', '/signup');
  });

  it('displays the TopBar with logo and login button', () => {
    renderLandingPage();
    const logo = screen.getByRole('link', { name: /AdGenie Home/i });
    expect(logo).toBeInTheDocument();
    const loginButton = screen.getByRole('link', { name: /Login to your account/i });
    expect(loginButton).toBeInTheDocument();
    expect(loginButton).toHaveAttribute('href', '/login');
  });

  it('displays all three feature cards', () => {
    renderLandingPage();
    expect(screen.getByText(/AI-Powered Script Generation/i)).toBeInTheDocument();
    expect(screen.getByText(/Professional Voiceover & Music/i)).toBeInTheDocument();
    expect(screen.getByText(/Brand-Specific Styling/i)).toBeInTheDocument();
  });

  it('displays the social proof section', () => {
    renderLandingPage();
    expect(screen.getByText(/Join 1,000\+ Businesses/i)).toBeInTheDocument();
  });

  it('displays the footer with links', () => {
    renderLandingPage();
    expect(screen.getByRole('contentinfo')).toBeInTheDocument();
    expect(screen.getByText(/Privacy/i)).toBeInTheDocument();
    expect(screen.getByText(/Terms/i)).toBeInTheDocument();
    expect(screen.getByText(/Contact/i)).toBeInTheDocument();
  });

  it('has proper navigation links in TopBar', () => {
    renderLandingPage();
    expect(screen.getByRole('link', { name: /View features/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /View pricing/i })).toBeInTheDocument();
  });
});
