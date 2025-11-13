import React from 'react';
import './Documentation.css';

const Documentation = () => {
  const docs = [
    {
      icon: '📖',
      title: 'Complete Memory System Guide',
      description: 'Full implementation details, configuration, and best practices for the memory system',
      link: 'https://github.com/webmasterarbez/elaaoms_claude/blob/main/MEMORY_SYSTEM_GUIDE.md',
      color: '#6366f1'
    },
    {
      icon: '🚀',
      title: 'Deployment Guide',
      description: 'Production deployment instructions with Docker, cloud providers, and monitoring',
      link: 'https://github.com/webmasterarbez/elaaoms_claude/blob/main/DEPLOYMENT.md',
      color: '#8b5cf6'
    },
    {
      icon: '🛠️',
      title: 'API Documentation',
      description: 'Interactive API docs with Swagger UI showing all endpoints and schemas',
      link: 'http://localhost:8000/docs',
      color: '#ec4899'
    },
    {
      icon: '📝',
      title: 'Quick Start Guide',
      description: 'Get up and running in minutes with our step-by-step installation guide',
      link: 'https://github.com/webmasterarbez/elaaoms_claude#-quick-start',
      color: '#14b8a6'
    },
    {
      icon: '🔧',
      title: 'Utility Scripts',
      description: 'Helper tools and scripts for development and testing',
      link: 'https://github.com/webmasterarbez/elaaoms_claude/blob/main/utility/README.md',
      color: '#f59e0b'
    },
    {
      icon: '🔍',
      title: 'Code Analysis',
      description: 'Technical deep-dive into code-documentation alignment',
      link: 'https://github.com/webmasterarbez/elaaoms_claude/blob/main/CODE_DOCUMENTATION_ALIGNMENT.md',
      color: '#10b981'
    }
  ];

  return (
    <section id="docs" className="section documentation">
      <div className="container">
        <h2 className="section-title">Documentation</h2>
        <p className="section-subtitle">
          Everything you need to get started, deploy, and maintain ELAAOMS
        </p>

        <div className="docs-grid">
          {docs.map((doc, index) => (
            <a
              key={index}
              href={doc.link}
              target="_blank"
              rel="noopener noreferrer"
              className="doc-card"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="doc-icon" style={{ background: `${doc.color}20`, color: doc.color }}>
                {doc.icon}
              </div>
              <h3 className="doc-title">{doc.title}</h3>
              <p className="doc-description">{doc.description}</p>
              <span className="doc-link">
                Read More →
              </span>
            </a>
          ))}
        </div>

        <div className="support-section">
          <div className="support-card">
            <h3 className="support-title">Need Help?</h3>
            <p className="support-description">
              Join our community on GitHub for support, discussions, and updates.
            </p>
            <div className="support-buttons">
              <a
                href="https://github.com/webmasterarbez/elaaoms_claude/issues"
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-secondary"
              >
                Report Issue
              </a>
              <a
                href="https://github.com/webmasterarbez/elaaoms_claude/discussions"
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-secondary"
              >
                Join Discussion
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Documentation;
