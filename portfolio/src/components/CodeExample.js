import React, { useState } from 'react';
import './CodeExample.css';

const CodeExample = () => {
  const [activeTab, setActiveTab] = useState('setup');

  const codeExamples = {
    setup: `# 1. Clone the repository
git clone https://github.com/webmasterarbez/elaaoms_claude.git
cd elaaoms_claude

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Start with Docker Compose
docker-compose up -d

# Service running on http://localhost:8000`,

    webhook: `# Configure ElevenLabs webhook
POST /webhook/client-data
{
  "agent_id": "agent_abc123",
  "conversation_id": "conv_xyz789",
  "dynamic_variables": {
    "system__caller_id": "+15551234567"
  }
}

# Response with personalized greeting
{
  "first_message": "Hi again! I hope your order XYZ-789 arrived safely. How can I help you today?"
}`,

    search: `# Real-time memory search during call
POST /webhook/search-memory
{
  "query": "What was my last order number?",
  "caller_id": "+15551234567",
  "agent_id": "agent_abc123",
  "conversation_id": "conv_current123"
}

# Returns relevant memories
{
  "results": [{
    "memory": "Customer ordered product XYZ-789",
    "relevance": 0.92,
    "timestamp": "2025-11-10T14:30:00Z"
  }],
  "summary": "Most recent order: XYZ-789"
}`,

    extraction: `# Post-call memory extraction
POST /webhook/post-call
{
  "type": "post_call_transcription",
  "data": {
    "conversation_id": "conv_abc123",
    "transcript": [...],
    "agent_id": "agent_abc123"
  }
}

# Automatic background processing:
# 1. Validates HMAC signature
# 2. Saves payload to disk
# 3. Extracts 5 memory types (LLM)
# 4. Deduplicates memories
# 5. Stores in OpenMemory`
  };

  const tabs = [
    { id: 'setup', label: 'Quick Setup', icon: '🚀' },
    { id: 'webhook', label: 'Personalized Greeting', icon: '👋' },
    { id: 'search', label: 'Memory Search', icon: '🔍' },
    { id: 'extraction', label: 'Auto Extraction', icon: '🧠' }
  ];

  return (
    <section id="code-example" className="section code-example">
      <div className="container">
        <h2 className="section-title">See It In Action</h2>
        <p className="section-subtitle">
          Real code examples showing how easy it is to integrate ELAAOMS
        </p>

        <div className="code-demo">
          <div className="code-tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                className={`code-tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <span className="tab-icon">{tab.icon}</span>
                <span className="tab-label">{tab.label}</span>
              </button>
            ))}
          </div>

          <div className="code-display">
            <div className="code-header">
              <div className="code-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span className="code-title">example.sh</span>
              <button className="copy-button">Copy</button>
            </div>
            <div className="code-body">
              <pre>
                <code>{codeExamples[activeTab]}</code>
              </pre>
            </div>
          </div>

          <div className="code-features">
            <div className="code-feature">
              <span className="feature-badge">✓</span>
              <span>No complex configuration</span>
            </div>
            <div className="code-feature">
              <span className="feature-badge">✓</span>
              <span>Works out of the box</span>
            </div>
            <div className="code-feature">
              <span className="feature-badge">✓</span>
              <span>Full API documentation</span>
            </div>
            <div className="code-feature">
              <span className="feature-badge">✓</span>
              <span>Open source & free</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CodeExample;
