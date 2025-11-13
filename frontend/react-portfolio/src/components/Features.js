import React from 'react';
import './Features.css';

const Features = () => {
  const features = [
    {
      icon: '🧠',
      title: 'Automatic Memory Extraction',
      description: 'LLM extracts memories from every conversation automatically. No manual input required.',
      color: '#6366f1'
    },
    {
      icon: '👋',
      title: 'Personalized Greetings',
      description: 'Returning callers get customized first messages based on their history.',
      color: '#8b5cf6'
    },
    {
      icon: '🔍',
      title: 'Real-Time Memory Search',
      description: 'Agents can search caller history during active calls in under 3 seconds.',
      color: '#ec4899'
    },
    {
      icon: '🤝',
      title: 'Multi-Agent Support',
      description: 'Share high-importance memories across different agents seamlessly.',
      color: '#14b8a6'
    },
    {
      icon: '🗄️',
      title: 'Zero Database Setup',
      description: 'Everything stored in OpenMemory with PostgreSQL backing. No complex setup.',
      color: '#f59e0b'
    },
    {
      icon: '🔐',
      title: 'HMAC-SHA256 Security',
      description: 'All webhooks validated using ElevenLabs HMAC signatures for security.',
      color: '#10b981'
    },
    {
      icon: '⚡',
      title: 'Background Processing',
      description: 'Memory extraction runs asynchronously without blocking webhook responses.',
      color: '#3b82f6'
    },
    {
      icon: '📊',
      title: 'Smart Deduplication',
      description: 'Automatically detects and prevents duplicate memories from being stored.',
      color: '#ef4444'
    }
  ];

  return (
    <section id="features" className="section features">
      <div className="container">
        <h2 className="section-title">Powerful Features</h2>
        <p className="section-subtitle">
          Everything you need to give your AI agents perfect memory and personalization
        </p>

        <div className="features-grid">
          {features.map((feature, index) => (
            <div
              key={index}
              className="feature-card"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="feature-icon" style={{ background: `${feature.color}20`, color: feature.color }}>
                {feature.icon}
              </div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-description">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
