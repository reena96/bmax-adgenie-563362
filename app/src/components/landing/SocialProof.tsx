import React from 'react';
import { Users } from 'lucide-react';

const SocialProof: React.FC = () => {
  return (
    <section
      className="py-16 px-6 cosmic-gradient"
      aria-label="Social proof"
    >
      <div className="max-w-4xl mx-auto">
        <div className="glass-card p-8 text-center">
          <div className="flex items-center justify-center gap-3 mb-3">
            <Users className="w-8 h-8 text-lightning-yellow" aria-hidden="true" />
            <h2 className="text-2xl md:text-3xl font-bold text-white">
              Join 1,000+ Businesses
            </h2>
          </div>
          <p className="text-lg text-white/70">
            Creating professional video ads in minutes with AdGenie's AI-powered platform
          </p>

          {/* Optional: User avatars/logos could be added here */}
          <div className="mt-6 flex items-center justify-center gap-2">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="w-10 h-10 rounded-full bg-gradient-to-br from-lightning-yellow/30 to-light-blue/30 border border-white/20"
                aria-hidden="true"
              />
            ))}
            <span className="text-white/50 text-sm ml-2">and many more...</span>
          </div>
        </div>
      </div>
    </section>
  );
};

export default SocialProof;
