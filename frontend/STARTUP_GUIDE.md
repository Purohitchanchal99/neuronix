# Frontend Startup Guide

## 🚀 Quick Start

### Step 1: Install Node.js (if not already installed)
Download from https://nodejs.org/ (LTS version recommended)

### Step 2: Install Frontend Dependencies
```bash
cd frontend
npm install
```

### Step 3: Start Development Server
```bash
npm run dev
```

The app will open at **http://localhost:3000**

---

## 🔗 Backend Connection

The frontend expects a backend API server running on **http://localhost:8000**

### Option A: Use the Template
1. Copy `backend_api_template.py` to your project directory
2. Install Flask: `pip install flask flask-cors`
3. Run: `python backend_api_template.py`

### Option B: Connect Your NEURONIX System
1. Modify the template to import your RAG query function
2. Update the `/api/chat` endpoint to use your system
3. Test the connection

---

## 📊 Expected API Response Format

Your backend should return:
```json
{
  "response": "Clinical response text here",
  "sources": [
    "Source document title",
    "Reference paper",
    "Clinical guideline"
  ]
}
```

---

## 🛠️ Development Tips

**Hot Reload:** Edit any file and the browser auto-refreshes
**Styling:** Edit `src/styles/main.css` for UI changes
**Components:** Edit files in `src/components/` for chat logic
**Dark Mode:** Toggle button in header top-right

---

## 📦 Build for Production

```bash
npm run build
```

Output: `frontend/dist/` - Ready to deploy!

---

## ✅ Testing Checklist

- [ ] Frontend loads at http://localhost:3000
- [ ] Backend running at http://localhost:8000
- [ ] Send test message - should see mock response
- [ ] Sources display below responses
- [ ] Dark mode toggle works
- [ ] New chat button creates sessions
- [ ] Messages auto-scroll to bottom

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| npm command not found | Install Node.js from nodejs.org |
| Cannot find module | Run `npm install` in frontend folder |
| Port 3000 already in use | Change port in vite.config.js |
| Backend connection error | Check backend is on port 8000 |
| Styling looks weird | Clear browser cache (Ctrl+Shift+Del) |

---

## 📝 Next Steps

1. **Connect Your RAG System** - Update backend_api_template.py with real queries
2. **Add Authentication** - Implement user login/signup
3. **Database Integration** - Store sessions and user data
4. **Deploy** - Push to production server
5. **Monitoring** - Track usage and errors

---

Good luck! 🎉
