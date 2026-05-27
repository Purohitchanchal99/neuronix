import React, { useState } from 'react';

function MessageBubble({ message }) {
  const [showSources, setShowSources] = useState(false);
  const [saved, setSaved] = useState(false);
  const isBot = message.type === 'bot';

  const handleSave = () => {
    const saved_responses = JSON.parse(localStorage.getItem('saved_responses') || '[]');
    saved_responses.push({ ...message, saved_at: new Date().toLocaleString() });
    localStorage.setItem('saved_responses', JSON.stringify(saved_responses));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  // Format source for display
  const formatSource = (source) => {
    if (typeof source === 'string') {
      return source;
    }
    if (typeof source === 'object' && source.title) {
      return `${source.title} (${source.relevance || 'standard'})`;
    }
    return String(source);
  };

  return (
    <div className={`message-bubble ${message.type}`}>
      <div className="message-icon">
        {isBot ? '🤖' : '👤'}
      </div>
      
      <div className="message-content">
        <div className="message-text">
          {/* Support for simple markdown-like formatting */}
          {message.content.split('\n').map((line, i) => (
            <div key={i} className="message-line">
              {line.startsWith('•') && <span className="bullet">{line}</span>}
              {line.startsWith('**') && <strong>{line.replace(/\*\*/g, '')}</strong>}
              {!line.startsWith('•') && !line.startsWith('**') && <span>{line}</span>}
            </div>
          ))}
        </div>
        
        <div className="message-footer">
          {isBot && message.sources && message.sources.length > 0 && (
            <div className="message-sources">
              <button
                className="sources-toggle"
                onClick={() => setShowSources(!showSources)}
                title="Toggle sources"
              >
                📚 {message.sources.length} source{message.sources.length !== 1 ? 's' : ''}
                <span className="toggle-arrow">{showSources ? '▼' : '▶'}</span>
              </button>
              
              {showSources && (
                <div className="sources-list">
                  {message.sources.map((source, idx) => (
                    <div key={idx} className="source-item">
                      <span className="source-icon">📖</span>
                      <span className="source-text">{formatSource(source)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {isBot && message.suggestions && message.suggestions.length > 0 && (
            <div className="message-suggestions">
              <div className="suggestions-label">💡 Next questions:</div>
              <div className="suggestions-list">
                {message.suggestions.map((suggestion, idx) => (
                  <button key={idx} className="suggestion-btn">
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="message-actions">
            <time className="message-time">{message.timestamp}</time>
            {isBot && (
              <button
                className={`save-btn ${saved ? 'saved' : ''}`}
                onClick={handleSave}
                title="Save response to library"
              >
                {saved ? '✅ Saved' : '💾'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default MessageBubble;
