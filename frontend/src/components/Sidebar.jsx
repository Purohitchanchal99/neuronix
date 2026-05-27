import React, { useState } from 'react';

function Sidebar({ sessions, currentSession, onSelectSession, onNewChat, onRenameSession, onExportSession, onDeleteSession }) {
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState('');

  const startEdit = (session) => {
    setEditingId(session.id);
    setEditValue(session.title);
  };

  const saveEdit = (sessionId) => {
    if (editValue.trim()) {
      onRenameSession(sessionId, editValue);
    }
    setEditingId(null);
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <button className="new-chat-btn" onClick={onNewChat}>
          ➕ New Chat
        </button>
      </div>

      <div className="session-list">
        <h3>Chat History</h3>
        {sessions.length === 0 ? (
          <p className="empty-message">No sessions yet</p>
        ) : (
          sessions.map(session => (
            <div
              key={session.id}
              className={`session-item ${currentSession === session.id ? 'active' : ''}`}
            >
              {editingId === session.id ? (
                <input
                  type="text"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onBlur={() => saveEdit(session.id)}
                  onKeyPress={(e) => e.key === 'Enter' && saveEdit(session.id)}
                  autoFocus
                  className="session-edit-input"
                />
              ) : (
                <>
                  <div
                    className="session-title"
                    onClick={() => onSelectSession(session.id)}
                    title="Click to select"
                  >
                    {session.title}
                  </div>
                  <div className="session-meta">
                    {session.messages.length} messages
                  </div>
                  <div className="session-date">{session.createdAt}</div>
                  <div className="session-actions">
                    <button
                      className="action-btn"
                      onClick={() => startEdit(session)}
                      title="Rename session"
                    >
                      ✏️
                    </button>
                    <button
                      className="action-btn"
                      onClick={() => onExportSession(session.id)}
                      title="Export as JSON"
                    >
                      💾
                    </button>
                    <button
                      className="action-btn delete"
                      onClick={() => { if (window.confirm('Delete session?')) onDeleteSession(session.id); }}
                      title="Delete session"
                    >
                      🗑️
                    </button>
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </div>

      <div className="sidebar-footer">
        <div className="quick-links">
          <h4>Resources</h4>
          <a href="#" className="resource-link">📚 Knowledge Base</a>
          <a href="#" className="resource-link">🆘 Crisis Help</a>
          <a href="#" className="resource-link">📞 Get Professional Help</a>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
