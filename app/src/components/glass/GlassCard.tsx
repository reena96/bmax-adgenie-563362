import React from 'react';

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  padding?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
}

const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className = '',
  padding = 'md',
  onClick,
  ...rest
}) => {
  const paddingClasses = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <div
      className={`glass-card ${paddingClasses[padding]} ${className}`}
      onClick={onClick}
      {...rest}
    >
      {children}
    </div>
  );
};

export default GlassCard;
