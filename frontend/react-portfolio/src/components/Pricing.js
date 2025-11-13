import React from 'react';
import './Pricing.css';

const Pricing = () => {
  const plans = [
    {
      name: 'Open Source',
      price: 'Free',
      period: 'Forever',
      description: 'Self-hosted solution with full source code access',
      features: [
        'Complete source code',
        'Self-hosted deployment',
        'Unlimited agents',
        'Unlimited memories',
        'All memory types',
        'Community support',
        'MIT License'
      ],
      popular: false,
      cta: 'Get Started',
      link: 'https://github.com/webmasterarbez/elaaoms_claude'
    },
    {
      name: 'Managed Hosting',
      price: 'Contact',
      period: 'Custom',
      description: 'We handle hosting, updates, and maintenance for you',
      features: [
        'Fully managed infrastructure',
        'Automatic updates',
        'Priority support',
        'Custom integrations',
        'SLA guarantees',
        'Dedicated resources',
        'Professional setup'
      ],
      popular: true,
      cta: 'Contact Sales',
      link: 'mailto:sales@example.com'
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: 'Tailored',
      description: 'Custom solutions for large-scale deployments',
      features: [
        'Dedicated infrastructure',
        'Custom features',
        'White-label options',
        'On-premise deployment',
        '24/7 support',
        'Training & onboarding',
        'SLA & compliance'
      ],
      popular: false,
      cta: 'Contact Us',
      link: 'mailto:enterprise@example.com'
    }
  ];

  return (
    <section id="pricing" className="section pricing">
      <div className="gradient-blob gradient-blob-1"></div>

      <div className="container">
        <h2 className="section-title">Choose Your Plan</h2>
        <p className="section-subtitle">
          Start free with open source or let us handle everything for you
        </p>

        <div className="pricing-grid">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`pricing-card ${plan.popular ? 'popular' : ''}`}
            >
              {plan.popular && <div className="popular-badge">Most Popular</div>}

              <div className="plan-header">
                <h3 className="plan-name">{plan.name}</h3>
                <div className="plan-price">
                  <span className="price">{plan.price}</span>
                  <span className="period">/{plan.period}</span>
                </div>
                <p className="plan-description">{plan.description}</p>
              </div>

              <ul className="plan-features">
                {plan.features.map((feature, i) => (
                  <li key={i}>
                    <span className="check-icon">✓</span>
                    {feature}
                  </li>
                ))}
              </ul>

              <a
                href={plan.link}
                target="_blank"
                rel="noopener noreferrer"
                className={`btn ${plan.popular ? 'btn-primary' : 'btn-secondary'} btn-block`}
              >
                {plan.cta}
              </a>
            </div>
          ))}
        </div>

        <div className="pricing-note">
          <p>
            💡 <strong>Usage Costs:</strong> ELAAOMS is free, but you'll need API keys for:
            ElevenLabs (for agents), OpenAI/Anthropic (for memory extraction), and OpenMemory (free self-hosted or paid cloud).
          </p>
        </div>
      </div>
    </section>
  );
};

export default Pricing;
