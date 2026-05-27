import React, { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import InputArea from './InputArea';
import axios from 'axios';

function ChatWindow({ session, allSessions, setAllSessions, currentSessionId }) {
  const [isLoading, setIsLoading] = useState(false);
  const [userId] = useState(() => {
    // Generate or retrieve persistent user ID
    let id = localStorage.getItem('neuronix_user_id');
    if (!id) {
      id = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('neuronix_user_id', id);
    }
    return id;
  });
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [session.messages]);

  const handleSendMessage = async (userMessage) => {
    // Add user message to chat
    const newMessage = {
      id: Date.now(),
      type: 'user',
      content: userMessage,
      timestamp: new Date().toLocaleTimeString()
    };

    const updatedSession = {
      ...session,
      messages: [...session.messages, newMessage]
    };

    // Update session locally
    const updatedSessions = allSessions.map(s =>
      s.id === currentSessionId ? updatedSession : s
    );
    setAllSessions(updatedSessions);

    // Get bot response
    setIsLoading(true);
    try {
      // Call NEURONIX backend API with correct payload format
      const payload = {
        user_id: userId,
        session_id: String(session.id),  // Convert to string
        message: userMessage,
        country: 'India',
        chunks: 6
      };

      console.log('📤 Sending payload:', JSON.stringify(payload, null, 2));

      const response = await axios.post(
        'http://localhost:8000/api/chat',
        payload
      );

      // Check for crisis response
      if (response.data.is_crisis) {
        const crisisMessage = {
          id: Date.now() + 1,
          type: 'bot',
          content: `🚨 ${response.data.response}\n\n📞 ${response.data.crisis_resources?.hotline}\n📋 ${response.data.crisis_resources?.resources}`,
          sources: response.data.sources || [],
          suggestions: response.data.suggestions || [],
          timestamp: new Date().toLocaleTimeString(),
          is_crisis: true
        };

        const sessionWithCrisis = {
          ...updatedSession,
          messages: [...updatedSession.messages, crisisMessage]
        };

        const finalSessions = allSessions.map(s =>
          s.id === currentSessionId ? sessionWithCrisis : s
        );
        setAllSessions(finalSessions);
      } else {
        const botMessage = {
          id: Date.now() + 1,
          type: 'bot',
          content: response.data.response,
          sources: response.data.sources || [],
          suggestions: response.data.suggestions || [],
          timestamp: new Date().toLocaleTimeString()
        };

        const sessionWithBotMessage = {
          ...updatedSession,
          messages: [...updatedSession.messages, botMessage]
        };

        const finalSessions = allSessions.map(s =>
          s.id === currentSessionId ? sessionWithBotMessage : s
        );
        setAllSessions(finalSessions);
      }

    } catch (error) {
      // DETAILED DEBUG LOGGING
      console.error('❌ FULL ERROR OBJECT:', error);
      console.error('Response status:', error.response?.status);
      console.error('Response data:', JSON.stringify(error.response?.data, null, 2));
      console.error('Error message:', error.message);
      console.error('Error stack:', error.stack);
      
      // Parse error details properly
      let errorDetail = 'Please check if the backend server is running on port 8000.';
      
      if (error.response?.data?.detail) {
        // Handle different detail formats
        if (typeof error.response.data.detail === 'string') {
          errorDetail = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          errorDetail = error.response.data.detail.map(d => 
            typeof d === 'string' ? d : JSON.stringify(d)
          ).join('\n');
        } else {
          errorDetail = JSON.stringify(error.response.data.detail);
        }
      } else if (error.response?.data?.message) {
        errorDetail = error.response.data.message;
      } else if (error.message) {
        errorDetail = error.message;
      }
      
      // Add error message with proper formatting
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: `❌ Error processing request:\n\n${errorDetail}\n\n📋 DEBUG: Status ${error.response?.status || 'N/A'}`,
        timestamp: new Date().toLocaleTimeString(),
        isError: true
      };

      const sessionWithError = {
        ...updatedSession,
        messages: [...updatedSession.messages, errorMessage]
      };

      const finalSessions = allSessions.map(s =>
        s.id === currentSessionId ? sessionWithError : s
      );
      setAllSessions(finalSessions);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-window">
      <div className="chat-header">
        <h2>{session.title}</h2>
        <span className="message-count">{session.messages.length} messages</span>
      </div>

      <div className="messages-container">
        {session.messages.length === 0 ? (
          <div className="welcome-message">
            <h3>👋 Welcome to NEURONIX</h3>
            <p>Ask me anything about mental health, wellness, anxiety, depression, sleep, stress management, and more.</p>
            <div className="quick-starters">
              <button className="quick-btn">What helps with anxiety?</button>
              <button className="quick-btn">How to improve sleep?</button>
              <button className="quick-btn">Stress management tips</button>
              <button className="quick-btn">Find professional help</button>
            </div>
          </div>
        ) : (
          session.messages.map(msg => (
            <MessageBubble key={msg.id} message={msg} />
          ))
        )}

        {isLoading && (
          <div className="message-bubble bot">
            <div className="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <InputArea
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
      />
    </div>
  );
}

export default ChatWindow;
