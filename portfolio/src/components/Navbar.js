import React, { useState } from 'react';
import './Navbar.css';

const Navbar = ({ scrolled }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const scrollToSection = (id) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      setMobileMenuOpen(false);
    }
  };

  return (
    <nav className={`navbar ${scrolled ? 'scrolled' : ''}`}>
      <div className="container navbar-container">
        <div className="navbar-brand">
          <span className="logo-text">ELAAOMS</span>
          <span className="logo-subtitle">Memory System</span>
        </div>

        <button
          className="mobile-menu-toggle"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle menu"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>

        <ul className={`navbar-menu ${mobileMenuOpen ? 'active' : ''}`}>
          <li><a onClick={() => scrollToSection('hero')}>Home</a></li>
          <li><a onClick={() => scrollToSection('features')}>Features</a></li>
          <li><a onClick={() => scrollToSection('how-it-works')}>How It Works</a></li>
          <li><a onClick={() => scrollToSection('code-example')}>Demo</a></li>
          <li><a onClick={() => scrollToSection('pricing')}>Pricing</a></li>
          <li><a onClick={() => scrollToSection('docs')}>Docs</a></li>
          <li>
            <a
              href="https://github.com/webmasterarbez/elaaoms_claude"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-primary btn-small"
            >
              Get Started
            </a>
          </li>
        </ul>
      </div>
    </nav>
  );
};

export default Navbar;
