# SpeakForge AI Speaking System
SpeakForge is an AI-powered speaking evaluation platform that transcribes audio responses using Whisper and scores grammar and fluency in real-time.
A comprehensive AI-powered speaking evaluation system built with FastAPI backend and React frontend.

## 🚀 Features

- **AI-Powered Evaluation**: Advanced grammar and fluency scoring for both audio and text answers
- **User Management**: Registration, login, email verification
- **Admin Dashboard**: Test creation, question management, analytics
- **User Dashboard**: Performance stats, recent attempts, available tests
- **Real-time Feedback**: Instant AI evaluation with detailed scoring
- **Responsive Design**: Modern UI with Tailwind CSS and Framer Motion

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database management
- **JWT**: Secure authentication
- **Whisper AI**: Audio transcription
- **LanguageTool**: Grammar checking
- **SQLite**: Database (configurable)

### Frontend
- **React 18**: Modern UI framework
- **React Router**: Client-side routing
- **Tailwind CSS**: Utility-first styling
- **Framer Motion**: Smooth animations
- **SweetAlert2**: Beautiful alerts
- **Axios**: HTTP client

## 📋 Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn

## 🚀 Quick Start

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start the server**
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

## 🔧 Configuration

### Environment Variables (.env)

```env
# Database Configuration (local MySQL)
DATABASE_URL=mysql+pymysql://root:0404@localhost:3306/speakforge

# JWT Configuration
SECRET_KEY=your_super_secret_key_here

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com

# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

## 📊 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/verify-email` - Email verification

### Tests
- `GET /tests/` - Get all tests
- `GET /tests/{id}` - Get test details
- `GET /tests/{id}/questions` - Get test questions
- `GET /tests/report/{id}` - Get the authenticated user's evaluation report
- `POST /tests/submit-answer/{question_id}` - Submit audio answer
- `POST /tests/submit-text-answer/{question_id}` - Submit text answer

### User Dashboard
- `GET /tests/me/dashboard` - User statistics
- `GET /tests/me/answers` - Recent answers

### Admin
- `POST /tests/` - Create test
- `PUT /tests/{id}` - Update test
- `DELETE /tests/{id}` - Delete test

## 🎯 Key Features

### AI Evaluation System
- **Audio Processing**: Whisper transcription + AI analysis
- **Text Analysis**: Direct text evaluation
- **Dual Scoring**: Separate fluency metrics for speaking vs writing
- **Performance Levels**: Beginner to Expert classification
- **Detailed Feedback**: Grammar, fluency, and improvement suggestions

### User Experience
- **Loading States**: Visual feedback during AI processing
- **Error Handling**: Comprehensive error messages
- **Responsive Design**: Works on all devices
- **Smooth Animations**: Professional UI transitions

## 🔒 Security Features

- **JWT Authentication**: Secure token-based auth
- **Password Hashing**: Bcrypt encryption
- **Email Verification**: Account validation
- **Role-Based Access**: Admin/User separation
- **CORS Protection**: Secure cross-origin requests

## 🐛 Troubleshooting

### Common Issues

1. **401 Unauthorized Errors**
   - Check JWT secret key configuration
   - Verify token storage in localStorage
   - Ensure correct API endpoints with /auth prefix

2. **Database Connection Issues**
   - Check DATABASE_URL in .env
   - Ensure database file permissions
   - Run database migrations

3. **Email Verification Not Working**
   - Verify SMTP configuration
   - Check email/password credentials
   - Ensure app password for Gmail

4. **Frontend Build Issues**
   - Clear node_modules and reinstall
   - Check Node.js version compatibility
   - Verify environment variables

## 📝 Development Notes

### Backend Architecture
- Modular structure with separate routes, services, and utilities
- Dependency injection for database sessions
- Comprehensive error handling
- Type hints throughout codebase

### Frontend Architecture
- Component-based structure
- Protected routes with authentication checks
- Centralized API configuration
- Responsive design patterns

## 🚀 Deployment

### Backend Deployment
1. Set production environment variables
2. Use production database (PostgreSQL recommended)
3. Configure reverse proxy (nginx)
4. Use WSGI server (Gunicorn)

### Frontend Deployment
1. Build production assets: `npm run build`
2. Serve static files
3. Configure environment variables
4. Set up proper routing

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review API documentation
- Verify environment setup
- Check browser console for errors
