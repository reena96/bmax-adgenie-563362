import React from 'react';

interface GlassInputProps {
  type?: 'text' | 'email' | 'password';
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  icon?: React.ReactNode;
  disabled?: boolean;
  autoComplete?: string;
  id?: string;
  name?: string;
  required?: boolean;
  ariaLabel?: string;
}

const GlassInput: React.FC<GlassInputProps> = ({
  type = 'text',
  placeholder,
  value,
  onChange,
  error,
  icon,
  disabled = false,
  autoComplete,
  id,
  name,
  required = false,
  ariaLabel,
}) => {
  return (
    <div className="w-full">
      <div className="relative">
        {icon && (
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-white/50">
            {icon}
          </div>
        )}
        <input
          id={id}
          name={name}
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          autoComplete={autoComplete}
          required={required}
          aria-label={ariaLabel || placeholder}
          aria-invalid={!!error}
          aria-describedby={error ? `${id}-error` : undefined}
          className={`glass-input w-full ${icon ? 'pl-12' : ''} ${
            error ? 'border-red-500' : ''
          } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        />
      </div>
      {error && (
        <p
          id={`${id}-error`}
          className="mt-1 text-sm text-red-400"
          role="alert"
        >
          {error}
        </p>
      )}
    </div>
  );
};

export default GlassInput;
