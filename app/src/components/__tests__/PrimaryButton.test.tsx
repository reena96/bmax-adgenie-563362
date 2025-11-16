import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import PrimaryButton from '../glass/PrimaryButton';

describe('PrimaryButton', () => {
  it('renders button with children', () => {
    render(<PrimaryButton>Click me</PrimaryButton>);
    expect(screen.getByRole('button', { name: /Click me/i })).toBeInTheDocument();
  });

  it('calls onClick handler when clicked', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(<PrimaryButton onClick={handleClick}>Click me</PrimaryButton>);

    await user.click(screen.getByRole('button', { name: /Click me/i }));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('renders as link when "to" prop is provided', () => {
    render(
      <BrowserRouter>
        <PrimaryButton to="/test">Go somewhere</PrimaryButton>
      </BrowserRouter>
    );

    const link = screen.getByRole('link', { name: /Go somewhere/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/test');
  });

  it('disables button when disabled prop is true', () => {
    render(<PrimaryButton disabled>Disabled</PrimaryButton>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('renders icon when provided', () => {
    const TestIcon = () => <span data-testid="test-icon">→</span>;
    render(
      <PrimaryButton icon={<TestIcon />}>
        With icon
      </PrimaryButton>
    );

    expect(screen.getByTestId('test-icon')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<PrimaryButton className="custom-class">Button</PrimaryButton>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('custom-class');
  });

  it('uses aria-label when provided', () => {
    render(<PrimaryButton ariaLabel="Custom label">Button</PrimaryButton>);
    expect(screen.getByRole('button', { name: /Custom label/i })).toBeInTheDocument();
  });
});
