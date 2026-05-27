# NEURONIX Frontend - Backend API Connection Guide

## Startup Instructions

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Frontend Development Server
```bash
npm run dev
```
The frontend will open at `http://localhost:3000`

### 3. Start Backend API Server
The frontend expects the backend to be running on `http://localhost:8000` with these endpoints:

#### Required Endpoints:

**POST /api/chat**
```json
Request:
{
  "message": "User question here"
}

Response:
{
  "response": "Bot response text",
  "sources": ["Source 1", "Source 2", "Source 3"]
}
```

## Features

✅ **Real-time Chat Interface**
- Message history with timestamps
- Auto-scroll to latest messages
- Typing indicators while waiting for response

✅ **Session Management**
- Create multiple chat sessions
- Chat history sidebar
- Session persistence

✅ **Response Display**
- Bot responses with formatting
- Source citations from RAG system
- Expandable source details

✅ **Dark/Light Mode**
- Toggle theme button in header
- Persistent across sessions

✅ **Mobile Responsive**
- Desktop optimized layout
- Tablet-friendly sidebar
- Mobile chat view

✅ **Clinical Features**
- Educational disclaimers
- Crisis help resources
- Professional referral buttons

## Component Structure

```
frontend/
├── src/
│   ├── App.jsx              (Main app component)
│   ├── index.jsx            (React entry point)
│   ├── components/
│   │   ├── Sidebar.jsx      (Chat history + new chat)
│   │   ├── ChatWindow.jsx   (Main chat area)
│   │   ├── MessageBubble.jsx(Message display)
│   │   └── InputArea.jsx    (User input + buttons)
│   └── styles/
│       └── main.css         (All styling)
├── index.html               (HTML template)
├── package.json
├── vite.config.js
└── README.md               (This file)
```

## Customization

### Colors (in main.css)
```css
--primary-color: #6366f1      (Purple)
--secondary-color: #8b5cf6    (Violet)
--accent: #10b981             (Green)
```

### Quick Replies
Edit in `InputArea.jsx`:
```javascript
const quickReplies = [
  'More details',
  'Similar topics',
  'Professional help',
  'Save response'
];
```

### Welcome Message
Edit in `ChatWindow.jsx` welcome-message section

## Production Build

```bash
npm run build
```

Outputs to `dist/` folder - ready for deployment.

## API Integration

The frontend connects to your NEURONIX backend API. Ensure your backend:

1. **Accepts POST requests** at `/api/chat`
2. **Returns JSON** with `response` and `sources` fields
3. **Runs on port 8000** (configurable in vite.config.js)
4. **Supports CORS** from localhost:3000 (and your domain)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Cannot connect to backend" | Ensure backend is running on port 8000 |
| Styling looks broken | Clear browser cache, restart dev server |
| Messages not loading | Check browser console for connection errors |
| Slow responses | Backend may be processing large queries |

## Next Steps (Tomorrow)

- [ ] Connect real NEURONIX RAG backend
- [ ] Add authentication/user accounts
- [ ] Implement session export/save
- [ ] Add conversation search
- [ ] Deploy to production server
- [ ] Configure CORS properly
- [ ] Add analytics tracking
