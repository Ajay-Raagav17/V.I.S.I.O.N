# VISION - Complete Tech Stack

## ✅ Confirmed Technologies

### **Backend**
- **Language**: Python 3.12+
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose) + bcrypt (passlib)

### **Frontend**
- **Framework**: React.js 18
- **Language**: JavaScript (JSX)
- **Styling**: Tailwind CSS 3.4
- **UI Components**: 
  - Headless UI (accessible components)
  - Heroicons (icon library)
  - clsx (utility for conditional classes)
- **Routing**: React Router DOM
- **HTTP Client**: Axios
- **Build Tool**: Vite

### **Deployment**
- **Platform**: Vercel
- **Architecture**: Serverless Functions
- **Frontend**: Static site (Vercel Edge CDN)
- **Backend**: Python serverless functions

---

## 🔧 Serverless Functions Architecture

### **What Are Serverless Functions?**

Serverless functions are **event-driven, auto-scaling compute units** that run your backend code without managing servers.

#### **Key Characteristics:**
1. **On-Demand Execution** - Functions only run when triggered by HTTP requests
2. **Auto-Scaling** - Automatically handles traffic spikes
3. **Pay-Per-Use** - Only charged for actual execution time
4. **Zero Server Management** - Vercel handles all infrastructure

#### **How It Works:**

```
User Request → Vercel Edge → Serverless Function → Database → Response
                  ↓
            (Cold Start or Warm Instance)
```

### **Our Serverless Function Structure**

```
api/
├── auth/
│   └── __init__.py          # Authentication endpoints
│                            # POST /api/auth/register
│                            # POST /api/auth/login
│                            # POST /api/auth/logout
│                            # GET  /api/auth/me
│
├── live/
│   └── __init__.py          # Live captioning endpoints
│                            # WS   /api/live/stream (WebSocket)
│                            # POST /api/live/start
│                            # POST /api/live/stop
│
├── upload/
│   └── __init__.py          # Audio upload endpoints
│                            # POST /api/upload/audio
│                            # GET  /api/upload/status/:id
│
├── notes/
│   └── __init__.py          # Study notes endpoints
│                            # GET  /api/notes/:lectureId
│                            # GET  /api/notes/:lectureId/pdf
│
└── lectures/
    └── __init__.py          # Lecture history endpoints
                             # GET    /api/lectures
                             # GET    /api/lectures/:id
                             # DELETE /api/lectures/:id
```

### **Example Serverless Function** (To Be Implemented)

```python
# api/auth/__init__.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from passlib.context import CryptContext
from jose import jwt
import os

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/api/auth/register")
async def register(email: str, password: str, db: Session = Depends(get_db)):
    """
    This function:
    1. Spins up when /api/auth/register is called
    2. Executes the registration logic
    3. Returns response
    4. Shuts down (or stays warm for ~5 minutes)
    """
    # Check if user exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = pwd_context.hash(password)
    
    # Create user
    user = User(email=email, password_hash=hashed_password)
    db.add(user)
    db.commit()
    
    return {"message": "User created successfully", "user_id": str(user.id)}

@app.post("/api/auth/login")
async def login(email: str, password: str, db: Session = Depends(get_db)):
    """
    Another independent function that handles login
    """
    user = db.query(User).filter(User.email == email).first()
    if not user or not pwd_context.verify(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate JWT token
    token = jwt.encode(
        {"user_id": str(user.id), "email": user.email},
        os.getenv("JWT_SECRET"),
        algorithm="HS256"
    )
    
    return {"access_token": token, "token_type": "bearer"}
```

### **Serverless Function Lifecycle**

```
1. Request arrives at /api/auth/login
   ↓
2. Vercel checks if function is "warm" (recently used)
   ↓
3a. If WARM: Execute immediately (~50ms)
3b. If COLD: Start Python runtime → Load dependencies → Execute (~1-3s)
   ↓
4. Function connects to PostgreSQL database
   ↓
5. Execute business logic (authentication)
   ↓
6. Return response to client
   ↓
7. Function stays "warm" for ~5 minutes
   ↓
8. If no requests, function shuts down (saves resources)
```

### **Benefits for VISION**

1. **Cost-Effective**: Only pay when users are active
2. **Scalable**: Handles 1 user or 10,000 users automatically
3. **No DevOps**: No server configuration, monitoring, or maintenance
4. **Global**: Functions run close to users (Vercel Edge Network)
5. **Fast Development**: Focus on code, not infrastructure

### **Limitations to Consider**

1. **Cold Starts**: First request after idle period is slower (~1-3s)
2. **Execution Time**: Max 60 seconds per function (sufficient for our use case)
3. **Memory**: 1024MB per function (enough for audio processing)
4. **Stateless**: Can't store data between requests (use database/cache)

---

## 📦 Complete Dependency List

### **Python (requirements.txt)**
```
# Web Framework
fastapi==0.108.0
uvicorn[standard]==0.25.0
python-multipart==0.0.6
pydantic==2.5.3

# Database
sqlalchemy==2.0.23
alembic==1.13.1
psycopg2-binary==2.9.9

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0

# External APIs
google-cloud-speech==2.23.0
google-generativeai==0.3.2

# PDF Generation
reportlab==4.0.7
weasyprint==60.2

# Testing
pytest==7.4.3
pytest-asyncio==0.23.2
hypothesis==6.92.2
httpx==0.26.0
websockets==12.0
```

### **Frontend (package.json)**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.2",
    "@headlessui/react": "^1.7.17",
    "@heroicons/react": "^2.1.1",
    "clsx": "^2.0.0"
  },
  "devDependencies": {
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.32",
    "autoprefixer": "^10.4.16",
    "vite": "^5.0.8",
    "@vitejs/plugin-react": "^4.2.1",
    "jest": "^29.7.0",
    "fast-check": "^3.15.0",
    "@testing-library/react": "^14.1.2",
    "@testing-library/jest-dom": "^6.1.5"
  }
}
```

---

## 🎨 UI Component Libraries

### **Headless UI**
- Unstyled, accessible UI components
- Works perfectly with Tailwind CSS
- Components: Dialog, Menu, Listbox, Combobox, Tabs, etc.

### **Heroicons**
- Beautiful hand-crafted SVG icons
- Designed by Tailwind CSS team
- Outline and solid variants

### **Usage Example:**
```jsx
import { Dialog } from '@headlessui/react'
import { XMarkIcon } from '@heroicons/react/24/outline'

function Modal({ isOpen, onClose }) {
  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/30" aria-hidden="true" />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="card max-w-md">
          <Dialog.Title className="text-lg font-bold">
            Upload Audio
          </Dialog.Title>
          <button onClick={onClose}>
            <XMarkIcon className="h-6 w-6" />
          </button>
        </Dialog.Panel>
      </div>
    </Dialog>
  )
}
```

---

## 🚀 Current Implementation Status

### ✅ Completed (Tasks 1-2)
- [x] Project structure setup
- [x] Database models (User, Lecture, StudyNotes)
- [x] Database connection with pooling
- [x] Alembic migrations
- [x] Unit tests for models (17 tests passing)
- [x] Tailwind CSS configuration
- [x] Frontend build setup (Vite + React)

### 🔄 To Be Implemented (Tasks 3-20)
- [ ] Serverless functions for authentication
- [ ] Serverless functions for live captioning
- [ ] Serverless functions for audio upload
- [ ] Audio processing pipeline
- [ ] Google Speech-to-Text integration
- [ ] Gemini AI integration
- [ ] PDF generation service
- [ ] React components (UI)
- [ ] WebSocket for real-time captioning
- [ ] Error handling and logging
- [ ] Deployment configuration

---

## 📝 Summary

**Yes, we are using:**
- ✅ Python
- ✅ FastAPI
- ✅ PostgreSQL
- ✅ React.js
- ✅ JavaScript
- ✅ Tailwind CSS
- ✅ Headless UI & Heroicons

**Serverless functions** are the deployment architecture where each API endpoint runs as an independent, auto-scaling function on Vercel. They haven't been implemented yet - we've only set up the database layer so far. The actual serverless function code will be created in tasks 3-11.
