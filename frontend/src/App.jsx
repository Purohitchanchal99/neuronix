import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import './styles/main.css';

function App() {
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [darkMode, setDarkMode] = useState(true);
  const [largeText, setLargeText] = useState(false);

  // Create new chat session
  const createNewSession = () => {
    const newSession = {
      id: Date.now(),
      title: `Chat ${sessions.length + 1}`,
      messages: [],
      createdAt: new Date().toLocaleString(),
      editable: false
    };
    setSessions([...sessions, newSession]);
    setCurrentSession(newSession.id);
  };

  // Rename session
  const renameSession = (sessionId, newTitle) => {
    setSessions(sessions.map(s =>
      s.id === sessionId ? { ...s, title: newTitle, editable: false } : s
    ));
  };

  // Export session as JSON
  const exportSession = (sessionId) => {
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      const dataStr = JSON.stringify(session, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${session.title.replace(/\s+/g, '-')}-${sessionId}.json`;
      link.click();
    }
  };

  // Delete session
  const deleteSession = (sessionId) => {
    const newSessions = sessions.filter(s => s.id !== sessionId);
    setSessions(newSessions);
    if (currentSession === sessionId) {
      setCurrentSession(newSessions[0]?.id || null);
    }
  };

  // Initialize first session
  useEffect(() => {
    if (sessions.length === 0) {
      createNewSession();
    }
  }, []);

  // Get current session data
  const activeSession = sessions.find(s => s.id === currentSession);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.body.classList.toggle('dark-mode');
  };

  const toggleLargeText = () => {
    setLargeText(!largeText);
    document.body.classList.toggle('large-text');
  };

  return (
    <div className={`app-container ${darkMode ? 'dark-mode' : 'light-mode'} ${largeText ? 'large-text' : ''}`}>
      <header className="app-header">
        <h1>🧠 NEURONIX</h1>
        <p>Mental Health Support System</p>
        <div className="header-controls">
          <button className="theme-toggle" onClick={toggleDarkMode} title="Toggle dark/light mode">
            {darkMode ? '☀️' : '🌙'}
          </button>
          <button className="text-size-toggle" onClick={toggleLargeText} title="Toggle large text">
            {largeText ? 'A' : 'A+'}
          </button>
        </div>
      </header>

      <div className="main-layout">
        <Sidebar
          sessions={sessions}
          currentSession={currentSession}
          onSelectSession={setCurrentSession}
          onNewChat={createNewSession}
          onRenameSession={renameSession}
          onExportSession={exportSession}
          onDeleteSession={deleteSession}
        />
        
        {activeSession && (
          <ChatWindow
            session={activeSession}
            allSessions={sessions}
            setAllSessions={setSessions}
            currentSessionId={currentSession}
          />
        )}
      </div>

      <footer className="app-footer">
        <p>⚠️ This system provides educational information. Always consult with a mental health professional for personal concerns.</p>
      </footer>
    </div>
  );
}

export default App;
