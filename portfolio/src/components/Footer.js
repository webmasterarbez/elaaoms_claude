import React from 'react';
import './Footer.css';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  const footerLinks = {
    product: [
      { name: 'Features', link: '#features' },
      { name: 'How It Works', link: '#how-it-works' },
      { name: 'Pricing', link: '#pricing' },
      { name: 'Documentation', link: '#docs' }
    ],
    resources: [
      { name: 'Memory System Guide', link: 'https://github.com/webmasterarbez/elaaoms_claude/blob/main/MEMORY_SYSTEM_GUIDE.md' },
      { name: 'Deployment Guide', link: 'https://github.com/webmasterarbez/elaaoms_claude/blob/main/DEPLOYMENT.md' },
      { name: 'API Docs', link: 'http://localhost:8000/docs' },
      { name: 'GitHub', link: 'https://github.com/webmasterarbez/elaaoms_claude' }
    ],
    company: [
      { name: 'About', link: '#' },
      { name: 'Blog', link: '#' },
      { name: 'Contact', link: '#' },
      { name: 'Support', link: 'https://github.com/webmasterarbez/elaaoms_claude/issues' }
    ]
  };

  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-content">
          <div className="footer-brand">
            <div className="brand-logo">
              <span className="logo-text">ELAAOMS</span>
              <span className="logo-subtitle">Memory System</span>
            </div>
            <p className="brand-description">
              Universal memory system for ElevenLabs AI agents. Give your agents perfect memory.
            </p>
            <div className="social-links">
              <a href="https://github.com/webmasterarbez/elaaoms_claude" target="_blank" rel="noopener noreferrer" aria-label="GitHub">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
              </a>
              <a href="#" target="_blank" rel="noopener noreferrer" aria-label="Twitter">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M23 3a10.9 10.9 0 01-3.14 1.53 4.48 4.48 0 00-7.86 3v1A10.66 10.66 0 013 4s-4 9 5 13a11.64 11.64 0 01-7 2c9 5 20 0 20-11.5a4.5 4.5 0 00-.08-.83A7.72 7.72 0 0023 3z"/>
                </svg>
              </a>
              <a href="#" target="_blank" rel="noopener noreferrer" aria-label="Discord">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20.317 4.492c-1.53-.69-3.17-1.2-4.885-1.49a.075.075 0 0 0-.079.036c-.21.369-.444.85-.608 1.23a18.566 18.566 0 0 0-5.487 0 12.36 12.36 0 0 0-.617-1.23A.077.077 0 0 0 8.562 3c-1.714.29-3.354.8-4.885 1.491a.07.07 0 0 0-.032.027C.533 9.093-.32 13.555.099 17.961a.08.08 0 0 0 .031.055 20.03 20.03 0 0 0 5.993 2.98.078.078 0 0 0 .084-.026c.462-.62.874-1.275 1.226-1.963.021-.04.001-.088-.041-.104a13.201 13.201 0 0 1-1.872-.878.075.075 0 0 1-.008-.125c.126-.093.252-.19.372-.287a.075.075 0 0 1 .078-.01c3.927 1.764 8.18 1.764 12.061 0a.075.075 0 0 1 .079.009c.12.098.245.195.372.288a.075.075 0 0 1-.006.125c-.598.344-1.22.635-1.873.877a.075.075 0 0 0-.041.105c.36.687.772 1.341 1.225 1.962a.077.077 0 0 0 .084.028 19.963 19.963 0 0 0 6.002-2.981.076.076 0 0 0 .032-.054c.5-5.094-.838-9.52-3.549-13.442a.06.06 0 0 0-.031-.028zM8.02 15.278c-1.182 0-2.157-1.069-2.157-2.38 0-1.312.956-2.38 2.157-2.38 1.21 0 2.176 1.077 2.157 2.38 0 1.312-.956 2.38-2.157 2.38zm7.975 0c-1.183 0-2.157-1.069-2.157-2.38 0-1.312.955-2.38 2.157-2.38 1.21 0 2.176 1.077 2.157 2.38 0 1.312-.946 2.38-2.157 2.38z"/>
                </svg>
              </a>
            </div>
          </div>

          <div className="footer-links">
            <div className="footer-column">
              <h4 className="footer-heading">Product</h4>
              <ul>
                {footerLinks.product.map((link, index) => (
                  <li key={index}>
                    <a href={link.link}>{link.name}</a>
                  </li>
                ))}
              </ul>
            </div>

            <div className="footer-column">
              <h4 className="footer-heading">Resources</h4>
              <ul>
                {footerLinks.resources.map((link, index) => (
                  <li key={index}>
                    <a href={link.link} target="_blank" rel="noopener noreferrer">{link.name}</a>
                  </li>
                ))}
              </ul>
            </div>

            <div className="footer-column">
              <h4 className="footer-heading">Company</h4>
              <ul>
                {footerLinks.company.map((link, index) => (
                  <li key={index}>
                    <a href={link.link} target="_blank" rel="noopener noreferrer">{link.name}</a>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <p className="copyright">
            &copy; {currentYear} ELAAOMS. Released under MIT License.
          </p>
          <div className="footer-bottom-links">
            <a href="#">Privacy Policy</a>
            <a href="#">Terms of Service</a>
            <a href="https://github.com/webmasterarbez/elaaoms_claude/blob/main/LICENSE" target="_blank" rel="noopener noreferrer">License</a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
