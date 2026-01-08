# RISKOFF - Complete Implementation Walkthrough

**Project: RISKOFF** - A Fintech Platform for Risk Assessment and Loan Management

RISKOFF is an AI-powered smart lending platform that automates loan processing, risk assessment, and financial management. It integrates machine learning for risk scoring, parses financial documents for verification, and provides user-friendly interfaces for customers and admins. This README provides a comprehensive overview of the implementation, building upon the previous RISKON + VisualPe framework with enhanced features, security, and integrations.

## 🌟 Features

### Customer-Facing Features
- **📊 Financial Dashboard**: Visualize income, expenses, investments, and spending patterns.
- **📄 Bank Statement Upload**: Auto-parse and categorize transactions from CSV uploads with identity verification.
- **🎯 Customer Score**: AI-calculated creditworthiness score (0-900) based on DTI, expenses, and risk rules.
- **💰 Loan Application**: Apply for Personal, Home, Car, Education, or Business loans with instant AI assessment.
- **📋 Loan Tracking**: Real-time status updates and history.
- **❓ Grievance System**: AI-generated explanations for approvals/rejections.
- **🤖 AI Chat Agent**: Contextual responses for loan queries.
- **🎙️ Voice-to-Text Engine**: Users can apply for loans using voice notes. The system uses Gemini 1.5 Flash to transcribe audio directly into structured loan queries.
- **📤 File Uploads**: Support for receipts (images), bank statements (CSV), and audio transcription.

### Admin-Facing Features
- **📈 Dashboard**: Overview stats (loans by status, total volume).
- **🤖 Auto-Processing**: Auto-approve low-risk, auto-reject high-risk loans.
- **🔍 Risk Analysis**: Detailed ML-based assessment with fraud detection.
- **🚨 Fraud Detection**: Flags mismatches in expenses or identities.
- **💬 AI Responses**: Automated grievance explanations and notifications.
- **👨‍💼 Role-Based Access**: Admin-only endpoints for loan review and updates.

### Core Capabilities
- **AI-Powered Risk Engine**: EMI calculation and rule-based scoring.
- **Document Parsing**: AI extraction for receipts, statements, and audio.
- **Notifications**: Email alerts via Gmail SMTP.
- **Audit Logging**: Track all actions for compliance.
- **Security**: JWT auth, rate limiting, CORS, and headers.

## 📦 Technology Stack

| Component       | Technology/Framework          |
|-----------------|--------------------------------|
| Backend         | FastAPI (Python)              |
| Frontend        | React.js, TailwindCSS, Recharts |
| Database        | Supabase (PostgreSQL)         |
| AI/LLM          | Google Gemini 1.5 Flash       |
| ML Model        | Scikit-learn (Random Forest)  |
| Authentication  | Supabase Auth (JWT + OTP)     |
| Email           | Gmail SMTP                    |
| Containerization| Docker                        |
| Other Libraries | Pandas (parsing), Fuzzywuzzy (verification), SlowAPI (rate limiting) |

## 📁 Project Structure

```
riskoff/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI entry point + middleware
│   │   ├── config.py        # Supabase + Gemini initialization
│   │   ├── schemas.py       # Pydantic models for validation
│   │   ├── routers/
│   │   │   ├── auth.py      # Authentication endpoints
│   │   │   ├── loans.py     # Loan application endpoints
│   │   │   ├── upload.py    # File upload (CSV, images, audio)
│   │   │   ├── admin.py     # Admin panel endpoints
│   │   │   └── agent.py     # AI chat agent
│   │   ├── services/
│   │   │   ├── risk_engine.py # EMI + Risk score calculation
│   │   │   ├── parser.py    # CSV/Image/Audio parsing + identity verification
│   │   │   ├── llm.py       # Gemini AI text generation
│   │   │   ├── notification.py # Email notifications (SMTP/Mock)
│   │   │   └── audit.py     # Audit logging
│   │   └── utils/
│   │       └── security.py  # JWT verification, auth dependencies
│   ├── tests/               # Test files
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile           # Production Docker setup
│   ├── .dockerignore        # Docker build exclusions
│   └── .env                 # Environment secrets
├── frontend/
│   ├── src/                 # React source code
│   ├── public/              # Public assets
│   ├── package.json         # Node dependencies
│   └── ...                  # Other frontend files
├── .gitignore
└── README.md                # This file
```

## 🌐 API Endpoints Reference

### 🔐 Authentication (`/auth`)
| Method | Endpoint          | Auth Required | Description                  |
|--------|-------------------|---------------|------------------------------|
| POST   | /auth/signup      | ❌            | Register new user            |
| POST   | /auth/login       | ❌            | Login → returns JWT tokens   |
| POST   | /auth/login/form  | ❌            | OAuth2 login for Swagger     |
| POST   | /auth/logout      | ✅            | Sign out current user        |
| POST   | /auth/refresh     | ❌            | Refresh access token         |
| GET    | /auth/me          | ✅            | Get current user profile     |

### 💰 Loans (`/loans`)
| Method | Endpoint       | Auth Required | Description                        |
|--------|----------------|---------------|------------------------------------|
| POST   | /loans/apply   | ✅            | Submit loan application with AI assessment |
| GET    | /loans/my-loans| ✅            | Get user's loan history            |
| GET    | /loans/        | ❌ (Admin)    | Get all loans (admin view)         |
| GET    | /loans/{loan_id}| ❌ (Admin)    | Get specific loan                  |

**Loan Application Flow**:
1. User submits amount, tenure, income, expenses, purpose.
2. Risk Engine calculates EMI and risk score.
3. Gemini AI generates approval/rejection message.
4. Loan saved to Supabase `loans` table.
5. Action logged to `audit_logs`.

### 📤 Uploads (`/upload`)
| Method | Endpoint                | Auth Required | Description                              |
|--------|-------------------------|---------------|------------------------------------------|
| POST   | /upload/receipt         | Optional      | Upload receipt image → AI extracts data  |
| POST   | /upload/bank-statement  | ✅            | Upload CSV → parses with verification    |
| POST   | /upload/receipt/save    | ✅            | Save verified receipt to database        |
| POST   | /upload/audio/transcribe| ✅            | Transcribe voice notes to text using Gemini |

**Features**:
- **Receipt Parsing**: Gemini Vision extracts merchant, amount, date, category.
- **Bank Statement Parsing**: Pandas-based auto-categorization (Food, Transport, etc.).
- **Identity Verification**: Fuzzy name matching (60% threshold).
- **Audio Transcription**: Gemini for voice input on loan queries.

### 👨‍💼 Admin (`/admin`)
| Method | Endpoint                | Auth Required | Description                              |
|--------|-------------------------|---------------|------------------------------------------|
| GET    | /admin/stats            | Admin         | Dashboard stats (loans, volume)          |
| GET    | /admin/loans            | Admin         | Get all loans for review                 |
| PATCH  | /admin/loans/{loan_id}/status | Admin   | Update loan status + email notification  |

**Admin Features**:
- Role-based access (`profiles.role = 'admin'`).
- Email notifications on status changes.
- Audit logging for actions.

### 🤖 AI Agent (`/agent`)
| Method | Endpoint     | Auth Required | Description                        |
|--------|--------------|---------------|------------------------------------|
| POST   | /agent/chat  | ✅            | Chat with AI Bank Manager          |

**What it does**:
- Fetches user's loan data.
- Generates contextual responses using Gemini.

### 🏠 System Endpoints
| Method | Endpoint | Description              |
|--------|----------|--------------------------|
| GET    | /        | API status               |
| GET    | /health  | Health check (API + DB)  |

## ⚙️ Core Services

1. **Risk Engine (`risk_engine.py`)**:
   - **EMI Calculation**: `EMI = P × r × (1+r)^n / ((1+r)^n - 1)`.
   - **Risk Scoring Rules**:
     - DTI > 40%: +30 points.
     - DTI > 60%: +50 points (replaces 30).
     - Expenses > 70% of income: +20 points.
     - DTI > 50% AND Expenses > 80%: ×1.5 multiplier.
   - **Result**: Score > 50 = REJECTED, else APPROVED.

2. **Parser Service (`parser.py`)**:
   - Bank Statement: Pandas parsing, auto-categorization.
   - Receipts: Gemini Vision extraction.
   - Audio: Gemini transcription.
   - Identity: Fuzzy matching (60% threshold).

3. **LLM Service (`llm.py`)**:
   - Functions: Loan summaries, rejection/approval messages, chat responses, spending analysis.
   - Singleton for unified imports.

4. **Notification Service (`notification.py`)**:
   - Gmail SMTP (mock mode for dev).
   - Status update emails.

5. **Audit Service (`audit.py`)**:
   - Logs to `audit_logs` table.
   - Non-blocking design.

## 🔒 Security Implementation

| Feature                | Implementation                          |
|------------------------|-----------------------------------------|
| Authentication         | Supabase Auth + JWT + OTP               |
| Rate Limiting          | SlowAPI (60/min)                        |
| Security Headers       | X-Content-Type-Options, X-Frame-Options, HSTS |
| CORS                   | Configured (allow all origins)          |
| Role-Based Access      | Admin dependency checks                 |
| Identity Verification  | Fuzzy name matching for uploads         |

## 🗄️ Database Schema (Supabase)

| Table            | Purpose                              |
|------------------|--------------------------------------|
| loans            | Loan applications (status, score, EMI) |
| profiles         | User profiles (name, phone, role)    |
| transactions     | Parsed financial transactions        |
| bank_statements  | Uploaded statement records           |
| audit_logs       | Action audit trail                   |

## 🐳 Docker Setup

**Dockerfile** (for backend):
```
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**.dockerignore**:
```
__pycache__
*.pyc
venv/
.env
.git
.pytest_cache
tests/
```

**Build & Run** (for backend):
```
# Build image
docker build -t riskoff-backend .
# Run container
docker run -d -p 8000:8000 --env-file .env --name riskoff-api riskoff-backend
```

## 🚀 Running Locally

### Backend Setup
1. Navigate to backend: `cd backend`
2. Create virtual environment: `python -m venv venv`  
   - Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Set up `.env` with:
   ```
   SUPABASE_URL=your_url
   SUPABASE_KEY=your_key
   GEMINI_API_KEY=your_key
   SMTP_EMAIL=your_email
   SMTP_PASSWORD=your_password
   ```
5. Run server: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

### Frontend Setup
1. Navigate to frontend: `cd frontend`
2. Install dependencies: `npm install`
3. Run: `npm start`

**Access**:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

## 🔐 Demo Accounts
| Role  | Email              | Password  |
|-------|--------------------|-----------|
| Admin | admin@riskoff.com  | admin123 |
| User  | user@test.com      | user123  |

## ✅ Implementation Summary
All components (FastAPI backend, React frontend, Supabase, Auth, Risk Engine, AI, Parsing, Admin, Agent, Notifications, Audit, Docker, Security) are complete and tested.


ARCHITECTURE DIAGRAM

<img width="1600" height="872" alt="image" src="https://github.com/user-attachments/assets/f1e0f35b-429f-4141-a8fe-aa70ed7dfaf3" />








## 📄 License
MIT License







