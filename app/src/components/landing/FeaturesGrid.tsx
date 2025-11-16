import React from 'react';
import { Sparkles, Music, Palette } from 'lucide-react';
import GlassCard from '../glass/GlassCard';

interface Feature {
  icon: React.ReactNode;
  title: string;
  description: string;
}

const features: Feature[] = [
  {
    icon: <Sparkles className="w-10 h-10 text-lightning-yellow" aria-hidden="true" />,
    title: 'AI-Powered Script Generation',
    description:
      'Our AI analyzes your brand and creates compelling storylines that resonate with your target audience.',
  },
  {
    icon: <Music className="w-10 h-10 text-light-blue" aria-hidden="true" />,
    title: 'Professional Voiceover & Music',
    description:
      'High-quality AI voiceovers and royalty-free music tracks perfectly matched to your brand tone.',
  },
  {
    icon: <Palette className="w-10 h-10 text-lightning-yellow" aria-hidden="true" />,
    title: 'Brand-Specific Styling',
    description:
      'Custom visual styles trained on your product images ensure consistent brand identity across all videos.',
  },
];

const FeaturesGrid: React.FC = () => {
  return (
    <section
      className="py-24 px-6 cosmic-gradient"
      aria-labelledby="features-heading"
    >
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2
            id="features-heading"
            className="text-4xl md:text-5xl font-bold text-white mb-4"
          >
            Everything You Need to{' '}
            <span className="text-lightning-yellow">Create Ads</span>
          </h2>
          <p className="text-lg text-white/70 max-w-2xl mx-auto">
            Powerful AI tools that transform your ideas into professional video ads
          </p>
        </div>

        {/* Features Grid */}
        <div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
          role="list"
          aria-label="Product features"
        >
          {features.map((feature, index) => (
            <GlassCard
              key={index}
              className="hover:scale-105 transition-transform duration-300 hover:border-lightning-yellow/30"
              role="listitem"
            >
              <div className="flex flex-col items-center text-center">
                {/* Icon */}
                <div className="mb-4">{feature.icon}</div>

                {/* Title */}
                <h3 className="text-xl font-semibold text-white mb-3">
                  {feature.title}
                </h3>

                {/* Description */}
                <p className="text-white/70 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </GlassCard>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeaturesGrid;
