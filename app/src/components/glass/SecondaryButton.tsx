import React from 'react';
import { Link } from 'react-router-dom';

interface SecondaryButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  type?: 'button' | 'submit';
  icon?: React.ReactNode;
  to?: string;
  className?: string;
  ariaLabel?: string;
}

const SecondaryButton: React.FC<SecondaryButtonProps> = ({
  children,
  onClick,
  disabled,
  type = 'button',
  icon,
  to,
  className = '',
  ariaLabel,
}) => {
  const buttonContent = (
    <>
      {children}
      {icon && <span className="ml-2">{icon}</span>}
    </>
  );

  const buttonClass = `btn-secondary flex items-center justify-center gap-2 ${className}`;

  if (to) {
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
      disabled={disabled}
      className={buttonClass}
      aria-label={ariaLabel || (typeof children === 'string' ? children : undefined)}
    >
      {buttonContent}
    </button>
  );
};

export default SecondaryButton;
