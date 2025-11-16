import React from 'react';
import { useAuthStore } from '../store/authStore';
import PrimaryButton from '../components/glass/PrimaryButton';

const BrandsPage: React.FC = () => {
  const { user, logout } = useAuthStore();

  return (
    <div className="min-h-screen cosmic-gradient">
      <div className="container mx-auto px-6 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-white">Brands Dashboard</h1>
          <PrimaryButton onClick={logout}>
            Logout
          </PrimaryButton>
        </div>

        <div className="glass-card p-8">
          <h2 className="text-2xl font-bold text-white mb-4">Welcome, {user?.email}!</h2>
          <p className="text-white/70 mb-4">
            This is your brands dashboard. Brand management features coming soon.
          </p>
          <div className="mt-6 space-y-2 text-white/60">
            <p><strong>Account Details:</strong></p>
            <p>Email: {user?.email}</p>
            <p>Subscription: {user?.subscription_tier}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BrandsPage;
