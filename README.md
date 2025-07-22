# 🎯 CodeMentor – AI Learning Assistant Chrome Extension

CodeMentor is an intelligent Chrome extension designed to assist coders by providing **progressive educational hints** for coding problems on platforms like LeetCode, HackerRank, and CodeForces. It guides users through the problem-solving process **without giving away full solutions**, promoting **genuine learning** over copy-pasting.

---

## 📋 Project Overview

- **Project Name**: CodeMentor - AI Learning Assistant Chrome Extension  
- **Mission**: Bridge the gap between struggling alone and full solutions by providing contextual hints to encourage problem-solving.
- **Target Users**: Computer science students, coding bootcamp learners, software engineers, and competitive programmers.
- **Core Value Proposition**: Empower learners to solve problems with guided help, not answers.

---

## 🧠 Core Features

### ✅ Intelligent Problem Detection
- Auto-detect platforms (LeetCode, HackerRank, CodeForces)
- Extract problem metadata: title, difficulty, tags, constraints
- Track URL changes and problem context

### ✅ Progressive Hint System (5 Levels)
1. Problem type identification  
2. Approach suggestion  
3. Data structure hints  
4. Implementation guidance  
5. Debugging tips  

### ✅ Code Analysis Engine
- Real-time editor tracking
- Detect programming language
- Identify effort and intent
- Pattern recognition

### ✅ Anti-Cheating Mechanisms
- Delays between hints
- Effort-based unlocking
- Daily hint limits
- Learning vs Test mode

### ✅ Learning Analytics
- Hint usage & success tracking
- Knowledge gap detection
- Personalized problem suggestions
- Performance stats

### ✅ Advanced Features
- Multi-platform support
- Collaborative learning: study groups, discussion, peer hints
- Educational integration: instructor dashboards, assignments, gradebook support

---

## 🏗️ Architecture Overview

### 🧩 Extension Components
- **Manifest V3 Compliant**
- **Content Scripts** for DOM parsing
- **Service Workers** for background processing
- **Popup UI** and **Options Page**

### 🔁 Data Flow
User Code → Content Script → Background Service → Backend API → AI Hint Engine → UI

---

## 🛠️ Technology Stack

### 🔹 Frontend (Chrome Extension)
- React 18 + TypeScript
- Tailwind CSS
- Chrome Extension APIs (storage, tabs)
- IndexedDB
- WebSocket (for real-time features)

### 🔹 Backend
- FastAPI (Python)
- PostgreSQL + Redis
- SQLAlchemy + Alembic
- Celery for background jobs
- JWT for authentication

### 🔹 AI/ML
- OpenAI GPT-4 or Anthropic Claude
- LangChain for prompt management
- ChromaDB for vector storage
- Sentence Transformers
- spaCy for NLP

### 🔹 DevOps
- Docker (multi-stage builds)
- GitHub Actions for CI/CD
- AWS ECS / DigitalOcean App Platform
- Sentry, Prometheus + Grafana for monitoring

---

## 🚀 Implementation Phases

### 📦 Phase 1: MVP (6-8 Weeks)
- LeetCode support
- 3-Level hinting
- Basic analytics & UI
- Auth system  
**Success:** 80%+ users complete problems using hints.

### 🌐 Phase 2: Multi-Platform (4-6 Weeks)
- HackerRank & CodeForces support
- AI-based hinting
- User dashboards
- Subscription model  
**Success:** 90% hint relevance, <500ms API latency

### 🧑‍🏫 Phase 3: Educational Features (6-8 Weeks)
- Study groups, instructor dashboards
- Mobile app companion
- Enterprise readiness  
**Success:** Educational partnerships & 10k+ active users

---

## 📐 Development Standards

- TypeScript strict mode
- ESLint + Prettier
- Jest & Playwright for testing
- Conventional commits
- Secure token handling
- CSP, input sanitization, CORS

---

## 📊 Key Metrics

### 📈 User Metrics
- Daily Active Users (DAU)
- Session duration
- Hint usage per problem
- Problem completion rate

### 🎓 Learning Metrics
- Success rate after hints
- Time-to-solution comparison
- Retention & progression

### ⚙️ Technical KPIs
- 99.9% API uptime
- <500ms API latency
- <0.1% crash rate

---

## 🧪 Setup Instructions

```bash
# Backend Setup
cd backend
python -m venv venv
source venv/Scripts/activate  # or source venv/bin/activate (Linux/Mac)
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend Setup (Chrome Extension)
cd extension
npm install
npm run build
# Load unpacked extension into Chrome via Extensions > Developer Mode
