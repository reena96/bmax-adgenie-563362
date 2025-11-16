import React from 'react';
import { Link } from 'react-router-dom';
import { Zap } from 'lucide-react';
import PrimaryButton from '../glass/PrimaryButton';

const TopBar: React.FC = () => {
  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 bg-cosmic-dark/80 backdrop-blur-md border-b border-white/10"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        {/* Logo */}
        <Link
          to="/"
          className="flex items-center gap-2 text-white hover:text-lightning-yellow transition-colors"
          aria-label="AdGenie Home"
        >
          <Zap className="w-6 h-6 text-lightning-yellow" aria-hidden="true" />
          <span className="text-xl font-bold">AdGenie</span>
        </Link>

        {/* Navigation Links */}
        <div className="hidden md:flex items-center gap-8">
          <Link
            to="#features"
            className="text-white/80 hover:text-white transition-colors"
            aria-label="View features"
          >
            Features
          </Link>
          <Link
            to="#pricing"
            className="text-white/80 hover:text-white transition-colors"
            aria-label="View pricing"
          >
            Pricing
          </Link>
        </div>

        {/* Login Button */}
        <PrimaryButton to="/login" ariaLabel="Login to your account">
          Login
        </PrimaryButton>
      </div>
    </nav>
  );
};

export default TopBar;
