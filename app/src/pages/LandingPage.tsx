import React from 'react';
import TopBar from '../components/shared/TopBar';
import HeroSection from '../components/landing/HeroSection';
import FeaturesGrid from '../components/landing/FeaturesGrid';
import SocialProof from '../components/landing/SocialProof';
import Footer from '../components/shared/Footer';

const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen cosmic-gradient">
      <TopBar />
      <main>
        <HeroSection />
        <FeaturesGrid />
        <SocialProof />
      </main>
      <Footer />
    </div>
  );
};

export default LandingPage;
