import React from 'react';
import { Link } from 'react-router-dom';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer
      className="bg-cosmic-dark border-t border-white/10 py-8"
      role="contentinfo"
      aria-label="Site footer"
    >
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Copyright */}
          <p className="text-white/60 text-sm">
            &copy; {currentYear} AdGenie. All rights reserved.
          </p>

          {/* Links */}
          <div className="flex items-center gap-6">
            <Link
              to="/privacy"
              className="text-white/60 hover:text-white text-sm transition-colors"
              aria-label="Privacy Policy"
            >
              Privacy
            </Link>
            <Link
              to="/terms"
              className="text-white/60 hover:text-white text-sm transition-colors"
              aria-label="Terms of Service"
            >
              Terms
            </Link>
            <Link
              to="/contact"
              className="text-white/60 hover:text-white text-sm transition-colors"
              aria-label="Contact Us"
            >
              Contact
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
