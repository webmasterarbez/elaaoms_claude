import React from 'react';
import './HowItWorks.css';

const HowItWorks = () => {
  const steps = [
    {
      number: '01',
      title: 'Pre-Call: Personalized Greeting',
      description: 'ElevenLabs calls /webhook/client-data → ELAAOMS retrieves memories → Generates personalized greeting',
      details: [
        'Caller ID identified',
        'Memory search in OpenMemory',
        'Custom first message generated',
        'Response in <2 seconds'
      ],
      color: '#6366f1'
    },
    {
      number: '02',
      title: 'During Call: Memory Search',
      description: 'Agent uses Server Tool → Calls /webhook/search-memory → Returns relevant memories',
      details: [
        'Real-time memory queries',
        'Semantic search with relevance scoring',
        'Multi-agent memory access',
        'Response in <3 seconds'
      ],
      color: '#8b5cf6'
    },
    {
      number: '03',
      title: 'Post-Call: Memory Extraction',
      description: 'ElevenLabs calls /webhook/post-call → Saves payload → Background job extracts & stores memories',
      details: [
        'HMAC signature validation',
        'LLM extracts 5 memory types',
        'Smart deduplication',
        'Stored in OpenMemory'
      ],
      color: '#ec4899'
    }
  ];

  return (
    <section id="how-it-works" className="section how-it-works">
      <div className="gradient-blob gradient-blob-2"></div>

      <div className="container">
        <h2 className="section-title">How It Works</h2>
        <p className="section-subtitle">
          Three simple webhook flows that handle everything automatically
        </p>

        <div className="steps-container">
          {steps.map((step, index) => (
            <div key={index} className="step-card">
              <div className="step-number" style={{ color: step.color }}>
                {step.number}
              </div>
              <div className="step-content">
                <h3 className="step-title">{step.title}</h3>
                <p className="step-description">{step.description}</p>
                <ul className="step-details">
                  {step.details.map((detail, i) => (
                    <li key={i}>
                      <span className="check-icon" style={{ color: step.color }}>✓</span>
                      {detail}
                    </li>
                  ))}
                </ul>
              </div>
              {index < steps.length - 1 && (
                <div className="step-connector"></div>
              )}
            </div>
          ))}
        </div>

        <div className="architecture-diagram">
          <h3 className="diagram-title">System Architecture</h3>
          <div className="diagram-content">
            <div className="diagram-row">
              <div className="diagram-box elevenlabs">
                <span className="box-icon">📞</span>
                <span>ElevenLabs</span>
              </div>
              <div className="arrow">→</div>
              <div className="diagram-box fastapi">
                <span className="box-icon">⚡</span>
                <span>FastAPI</span>
              </div>
              <div className="arrow">→</div>
              <div className="diagram-box llm">
                <span className="box-icon">🤖</span>
                <span>LLM</span>
              </div>
              <div className="arrow">→</div>
              <div className="diagram-box openmemory">
                <span className="box-icon">🗄️</span>
                <span>OpenMemory</span>
              </div>
            </div>
            <div className="diagram-labels">
              <span>Webhooks</span>
              <span>Processing</span>
              <span>Extraction</span>
              <span>Storage</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
