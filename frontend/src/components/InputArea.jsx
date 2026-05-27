import React, { useState, useRef, useEffect } from 'react';

function InputArea({ onSendMessage, isLoading }) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);
  const [showQuickActions, setShowQuickActions] = useState(true);

  // Auto-expand textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [input]);

  const handleSend = () => {
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
    // Escape to toggle quick actions
    if (e.key === 'Escape') {
      setShowQuickActions(!showQuickActions);
    }
  };

  const quickActionCategories = {
    'Self-Help': [
      { text: '🧘 Breathing Exercise', action: 'How can I practice breathing exercises?' },
      { text: '😴 Sleep Hygiene', action: 'What are good sleep hygiene tips?' },
      { text: '🚶 Daily Walk', action: 'How does exercise help mental health?' },
      { text: '📝 Journaling', action: 'How to start journaling?' }
    ],
    'Resources': [
      { text: '👨‍⚕️ Find Therapist', action: 'How do I find a mental health professional?' },
      { text: '🆘 Crisis Helpline', action: 'What are crisis support numbers?' },
      { text: '📱 Mental Health Apps', action: 'What are recommended mental health apps?' },
      { text: '💪 Support Groups', action: 'Where can I find support groups?' }
    ],
    'Learn More': [
      { text: '🎯 CBT Basics', action: 'What is Cognitive Behavioral Therapy?' },
      { text: '🧠 Mindfulness', action: 'What is mindfulness and how do I practice it?' },
      { text: '😰 Anxiety Management', action: 'What are evidence-based anxiety treatments?' },
      { text: '😔 Depression Support', action: 'What helps with depression?' }
    ]
  };

  return (
    <div className="input-area">
      <div className="input-container">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your question or describe how you're feeling... (Shift+Enter for new line, Esc to hide quick actions)"
          disabled={isLoading}
          rows={1}
          aria-label="Message input"
        />
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
          title="Send message (Enter)"
        >
          {isLoading ? '⏳' : '📤'} Send
        </button>
      </div>

      {showQuickActions && (
        <div className="quick-actions-panel">
          <button
            className="collapse-btn"
            onClick={() => setShowQuickActions(false)}
            title="Hide quick actions (Esc)"
          >
            ▼ Quick Actions (Press Esc to hide)
          </button>
          {Object.entries(quickActionCategories).map(([category, actions]) => (
            <div key={category} className="quick-action-category">
              <h4>{category}</h4>
              <div className="action-buttons">
                {actions.map((action, idx) => (
                  <button
                    key={idx}
                    className="quick-action-btn"
                    disabled={isLoading}
                    onClick={() => {
                      onSendMessage(action.action);
                      setInput('');
                    }}
                    title={action.action}
                  >
                    {action.text}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {!showQuickActions && (
        <button
          className="expand-btn"
          onClick={() => setShowQuickActions(true)}
          title="Show quick actions"
        >
          ▲ Show Quick Actions
        </button>
      )}

      <div className="input-disclaimer">
        ⚠️ This is not a substitute for professional mental health care.
      </div>
    </div>
  );
}

export default InputArea;
