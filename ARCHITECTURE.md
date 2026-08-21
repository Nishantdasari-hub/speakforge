# SpeakForge - Complete Project Architecture

### **Project Overview**
SpeakForge is an AI-powered speaking evaluation system that assesses users' English speaking and writing skills through automated tests. It uses advanced AI for grammar checking, fluency scoring, and provides detailed feedback for improvement.

---

### **System Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   User UI    │  │  Admin UI    │  │  Auth Pages  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                          ↕ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Auth Routes │  │  Test Routes │  │ Report Routes│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ AI Scoring   │  │ Auth Service │  │ Email Utils   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE (MySQL)                           │
│  Users | Tests | Questions | Answers | Results              │
└─────────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────────┐
│                   AI SERVICES                                │
│  Whisper AI (Audio) | LanguageTool (Grammar) | OpenAI (Scoring)│
└─────────────────────────────────────────────────────────────┘
```

---

### **Technology Stack**

#### **Backend**
- **FastAPI**: Modern, fast Python web framework
- **SQLAlchemy**: ORM for database operations
- **MySQL**: Production relational database
- **Pydantic**: Data validation and settings management
- **JWT (python-jose)**: Token-based authentication
- **Bcrypt**: Password hashing
- **Whisper AI**: Audio transcription
- **LanguageTool**: Grammar checking
- **OpenAI API**: Advanced AI scoring and feedback
- **FastAPI-Mail**: Email functionality
- **PyTorch**: Machine learning operations
- **NumPy/SciPy**: Numerical computations

#### **Frontend**
- **React 18**: UI framework
- **React Router 6**: Client-side routing
- **Vite 4**: Build tool and dev server
- **Tailwind CSS 3**: Utility-first styling
- **Framer Motion**: Smooth animations
- **SweetAlert2**: Beautiful alerts
- **Axios**: HTTP client
- **Lucide React**: Icon library
- **Recharts**: Data visualization
- **@dnd-kit**: Drag and drop functionality

---

### **Database Schema**

#### **Users Table**
- `id`, `name`, `email`, `password`, `role`, `is_verified`
- `created_at`, `updated_at`, `reset_token`, `reset_token_expiry`

#### **Tests Table**
- `id`, `title`, `description`, `created_at`

#### **Questions Table**
- `id`, `test_id`, `question_text`, `question_type` (text/audio)
- `time_limit`, `order_number`

#### **QuestionAnswers Table**
- `id`, `user_id`, `question_id`
- `written_answer`, `audio_path`, `transcribed_text`
- `grammar_score`, `fluency_score`, `final_score`
- `grammar_errors`, `word_count`, `feedback`
- `created_at`

#### **Results Table**
- `id`, `user_id`, `test_id`, `score`
- `answers` (JSON), `evaluation` (JSON), `submitted_at`

---

### **Core Features**

#### **User Features**
1. **Authentication**: Registration, login, email verification, password reset
2. **User Dashboard**: Performance stats, recent attempts, skill level
3. **Test Taking**: View available tests, answer questions (text/audio)
4. **Results**: Detailed reports with AI feedback and scoring
5. **My Results**: History of all test attempts

#### **Admin Features**
1. **Admin Dashboard**: Analytics (total tests, users, questions, attempts)
2. **Test Management**: Create, update, delete tests
3. **Question Management**: Add questions to tests, manage question types
4. **Analytics**: View system-wide performance metrics

---

### **AI Evaluation System**

#### **Audio Processing Pipeline**
1. User records audio answer → Upload to server
2. Whisper AI transcribes audio to text
3. LanguageTool checks grammar errors
4. AI analyzes fluency, vocabulary, coherence
5. Generates comprehensive feedback and scores

#### **Text Processing Pipeline**
1. User submits text answer
2. LanguageTool analyzes grammar and syntax
3. AI evaluates content quality, vocabulary usage
4. Provides grammar score, fluency score, final score
5. Generates improvement suggestions

#### **Scoring System**
- **Grammar Score**: 0-10 based on error count and complexity
- **Fluency Score**: 0-10 based on flow, coherence, vocabulary
- **Final Score**: Weighted average of grammar and fluency
- **Performance Levels**: Beginner, Intermediate, Upper-Intermediate, Advanced, Expert

---

### **API Endpoints**

#### **Authentication**
- `POST /auth/register` - User registration
- `POST /auth/login` - User login (returns JWT token)
- `GET /auth/verify-email` - Email verification
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password with token

#### **Tests**
- `GET /tests/` - Get all tests
- `GET /tests/{id}` - Get test details
- `GET /tests/{id}/questions` - Get test questions (requires auth)
- `POST /tests/submit-answer/{question_id}` - Submit audio/text answer
- `POST /tests/{id}/submit` - Submit completed test for AI evaluation

#### **User Dashboard**
- `GET /tests/me/dashboard` - User statistics and performance level
- `GET /tests/me/answers` - Recent answer attempts
- `GET /tests/me/results` - Complete test results history

#### **Admin**
- `POST /tests/` - Create test (admin only)
- `PUT /tests/{id}` - Update test (admin only)
- `DELETE /tests/{id}` - Delete test (admin only)
- `POST /tests/{test_id}/questions` - Add question (admin only)
- `PUT /tests/{test_id}/questions/{question_id}` - Update question
- `DELETE /tests/{test_id}/questions/{question_id}` - Delete question
- `GET /tests/admin/analytics` - System analytics (admin only)

#### **Reports**
- `GET /tests/report/{test_id}` - Get detailed test report

---

### **Frontend Architecture**

#### **Pages Structure**
- **Auth Pages**: Login, Register, ForgotPassword, ResetPassword
- **User Pages**: UserDashboard, UserTests, TestDetail, MyResults, TestReport
- **Admin Pages**: AdminDashboard, AdminTests, AdminQuestions, AdminAnalytics

#### **Components**
- **ProtectedRoute**: Authentication wrapper for protected routes
- **MainLayout**: Admin dashboard layout with navigation

#### **API Integration**
- Centralized API functions in `api.js`
- Base URL: configured through `VITE_API_URL`
- JWT token stored in localStorage
- Automatic token inclusion in headers

---

### **Security Features**
- JWT token-based authentication
- Bcrypt password hashing
- Role-based access control (User/Admin)
- CORS protection
- Email verification system
- Password reset with expiring tokens
- Protected API endpoints

---

### **Project Structure**

#### **Backend**
```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── email_id.py          # Email configuration
│   ├── routes/
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── test.py          # Test management endpoints
│   │   └── report.py        # Report generation endpoints
│   ├── services/
│   │   ├── auth_service.py  # Authentication logic
│   │   ├── test_service.py  # Test management logic
│   │   └── ai_scoring.py    # AI evaluation logic
│   └── utils/
│       ├── email.py         # Email utilities
│       └── security.py      # Security utilities
├── requirements.txt         # Python dependencies
└── .env                     # Environment variables
```

#### **Frontend**
```
frontend/
├── src/
│   ├── main.jsx             # React entry point
│   ├── App.jsx              # Main app component with routing
│   ├── api.js               # API integration functions
│   ├── index.css            # Global styles
│   ├── pages/               # Page components
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   ├── UserDashboard.jsx
│   │   ├── AdminDashboard.jsx
│   │   ├── TestDetail.jsx
│   │   └── ...
│   ├── components/          # Reusable components
│   │   └── ProtectedRoute.jsx
│   └── layout/              # Layout components
│       └── MainLayout.jsx
├── public/                  # Static assets
├── index.html               # HTML template
├── vite.config.js           # Vite configuration
├── tailwind.config.js       # Tailwind CSS configuration
└── package.json             # Node.js dependencies
```

---

### **Current Status**
✅ **Backend**: FastAPI service with production deployment support
✅ **Frontend**: Running on http://127.0.0.1:5173  
✅ **Database**: MySQL with Alembic migrations
✅ **Build**: Frontend production build successful
✅ **Dependencies**: All compatibility issues resolved
✅ **Email**: Optional configuration (works without email setup)

The system is fully operational with all core features functional. Users can register, take tests, receive AI-powered feedback, and admins can manage the complete test system.
