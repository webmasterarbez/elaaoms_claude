import React from 'react';
import './Hero.css';

const Hero = () => {
  return (
    <section id="hero" className="hero">
      <div className="gradient-blob gradient-blob-1"></div>
      <div className="gradient-blob gradient-blob-3"></div>

      <div className="container hero-container">
        <div className="hero-content">
          <div className="hero-badge">
            <span className="badge-icon">🚀</span>
            <span>Universal Memory System for AI Agents</span>
          </div>

          <h1 className="hero-title">
            Give Your <span className="gradient-text">ElevenLabs Agents</span>
            <br />Perfect Memory
          </h1>

          <p className="hero-description">
            ELAAOMS automatically extracts, stores, and retrieves conversation memories
            across all your agents. Provide personalized greetings for returning callers
            and real-time memory search during calls.
          </p>

          <div className="hero-buttons">
            <a
              href="https://github.com/webmasterarbez/elaaoms_claude"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-primary btn-large"
            >
              Get Started Free
            </a>
            <a
              href="#how-it-works"
              className="btn btn-secondary btn-large"
            >
              See How It Works
            </a>
          </div>

          <div className="hero-stats">
            <div className="stat">
              <div className="stat-number">100%</div>
              <div className="stat-label">Automatic</div>
            </div>
            <div className="stat">
              <div className="stat-number">&lt;2s</div>
              <div className="stat-label">Response Time</div>
            </div>
            <div className="stat">
              <div className="stat-number">∞</div>
              <div className="stat-label">Agents Supported</div>
            </div>
          </div>
        </div>

        <div className="hero-visual">
          <div className="code-preview">
            <div className="code-header">
              <div className="code-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span className="code-title">memory_extraction.py</span>
            </div>
            <div className="code-body">
              <code>
                <span className="code-comment"># Automatic memory extraction</span><br/>
                <span className="code-keyword">from</span> elaaoms <span className="code-keyword">import</span> MemorySystem<br/>
                <br/>
                <span className="code-comment"># Initialize memory system</span><br/>
                memory = MemorySystem()<br/>
                <br/>
                <span className="code-comment"># Webhook handles everything</span><br/>
                @app.post(<span className="code-string">"/webhook/post-call"</span>)<br/>
                <span className="code-keyword">async def</span> <span className="code-function">process_call</span>(data):<br/>
                &nbsp;&nbsp;&nbsp;&nbsp;<span className="code-comment"># Extracts memories automatically</span><br/>
                &nbsp;&nbsp;&nbsp;&nbsp;<span className="code-keyword">await</span> memory.extract(data)<br/>
                &nbsp;&nbsp;&nbsp;&nbsp;<span className="code-keyword">return</span> {<span className="code-string">"status"</span>: <span className="code-string">"success"</span>}
              </code>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
