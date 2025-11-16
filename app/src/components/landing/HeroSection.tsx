import React from 'react';
import { ArrowRight } from 'lucide-react';
import PrimaryButton from '../glass/PrimaryButton';

const HeroSection: React.FC = () => {
  return (
    <section
      className="min-h-screen flex items-center justify-center cosmic-gradient relative overflow-hidden pt-20"
      aria-labelledby="hero-heading"
    >
      {/* Decorative background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-lightning-yellow/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-light-blue/10 rounded-full blur-3xl" />
      </div>

      <div className="max-w-5xl mx-auto px-6 text-center relative z-10">
        {/* Headline */}
        <h1
          id="hero-heading"
          className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-6 leading-tight"
        >
          Create Professional Video Ads{' '}
          <span className="text-lightning-yellow">with AI</span>
        </h1>

        {/* Subheading */}
        <p className="text-xl md:text-2xl text-white/80 mb-10 max-w-3xl mx-auto">
          in Minutes, Not Hours
        </p>

        {/* CTA Button */}
        <PrimaryButton
          to="/signup"
          icon={<ArrowRight className="w-5 h-5" aria-hidden="true" />}
          className="text-lg px-8 py-4 inline-flex"
          ariaLabel="Get started for free"
        >
          Get Started Free
        </PrimaryButton>

        {/* Trust Signal */}
        <p className="text-white/50 text-sm mt-6">
          No credit card required • 2 free videos
        </p>
      </div>
    </section>
  );
};

export default HeroSection;
