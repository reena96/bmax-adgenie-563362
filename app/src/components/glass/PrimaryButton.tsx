import React from 'react';
import { Link } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

interface PrimaryButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  type?: 'button' | 'submit';
  icon?: React.ReactNode;
  to?: string;
  className?: string;
  ariaLabel?: string;
  isLoading?: boolean;
}

const PrimaryButton: React.FC<PrimaryButtonProps> = ({
  children,
  onClick,
  disabled,
  type = 'button',
  icon,
  to,
  className = '',
  ariaLabel,
  isLoading = false,
}) => {
  const isDisabled = disabled || isLoading;

  const buttonContent = (
    <>
      {isLoading ? (
        <Loader2 className="w-5 h-5 animate-spin" />
      ) : (
        <>
          {children}
          {icon && <span className="ml-2">{icon}</span>}
        </>
      )}
    </>
  );

  const buttonClass = `btn-primary flex items-center justify-center gap-2 ${className}`;

  if (to && !isDisabled) {
    return (
      <Link
        to={to}
        className={buttonClass}
        aria-label={ariaLabel || (typeof children === 'string' ? children : undefined)}
      >
        {buttonContent}
      </Link>
    );
  }

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={isDisabled}
      className={buttonClass}
      aria-label={ariaLabel || (typeof children === 'string' ? children : undefined)}
    >
      {buttonContent}
    </button>
  );
};

export default PrimaryButton;
