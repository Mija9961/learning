# learnAnythingWithAI - AI Learning Platform

A modern, AI-powered learning platform built with Flask that provides interactive education experiences, mock interviews, and personalized learning paths.

## 🚀 Features

- **AI-Powered Learning**: Interactive lessons with real-time AI feedback
- **Mock Interviews**: Practice technical interviews with AI assistance
- **Custom Learning Paths**: Personalized learning experiences
- **Multiple Subjects**: Python, DSA, and custom topics
- **Real-time Chat**: Interactive chat with AI tutor
- **Progress Tracking**: Monitor your learning journey
- **Admin Dashboard**: Comprehensive user and content management

## 🛠️ Technology Stack

- **Backend**: Python 3.12, Flask
- **Database**: MySQL, ChromaDB
- **Frontend**: Bootstrap 5, JavaScript
- **AI Integration**: OpenAI GPT, Google GenAI
- **Authentication**: JWT

## 📋 Prerequisites

- Python 3.12+
- MySQL
- pip (Python package manager)
- Git

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/learning.git
```

### 2. Set Up Virtual Environment

```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the root directory:

```env
FLASK_APP=run.py
FLASK_ENV=development

OPENAI_API_KEY=your-openai-api-key
GOOGLE_API_KEY=your-google-api-key
TAVILY_API_KEY=your-tavily-api-key

# Flask Secret Key
SECRET_KEY=
# Email Set Up
PASSWORD_EMAIL=your-app-password
EMAIL_SERVER='smtp.gmail.com'
PORT=587
SENDER_EMAIL=your-email
EMAIL_SEND_ENABLED=True
TIME_OUT=10

#Database
MYSQL_HOST="localhost"
MYSQL_USER="root"
MYSQL_PASSWORD="root"
MYSQL_DB="learning"

# Flask Secrete key
SECRET_KEY=your-secret-key

# ChromaDB
CHROMADB_HOST="localhost"
CHROMADB_PORT=yourport
CHROMADB_COLLECTION="default_memory"

# Flask APP
export FLASK_APP=run.py
export FLASK_DEBUG=1  # Enables reloading


# Default AI Model and Provider
DEFAULT_AI_PROVIDER="openai"
DEFAULT_AI_MODEL="gpt-4.1-mini"

# User Profile Image
UPLOAD_FOLDER = 'static/images/uploads'  # Make sure this folder exists and is writable

```

### 5. Database Setup

```bash
flask db upgrade
flask seed-db  # If you want to populate with sample data
```

### 6. Run the Application

```bash
flask run
```

Visit `http://localhost:5000` in your browser.

## 🐳 Docker Deployment

```bash
# Build the image
docker build -t your-docker-user-name/learnanythingwithai:latest .

# Run the container
docker run -e ENV_VAR=VALUE -p 5000:5000 your-docker-user-name/learnanythingwithai:latest
```

## 📁 Project Structure

```
learning/
├── app/                      # Main application package
│   ├── admin/               # Admin panel blueprint
│   ├── user/                # User dashboard blueprint
│   ├── auth/                # Authentication blueprint
│   ├── mocktest/            # Mock test functionality
│   ├── custom_subject/      # User defined subjects
│   ├── mock_interview/      # Mock interview
│   ├── chat/               # AI chat functionality
│   └── templates/          # General HTML templates
├── migrations/              # Database migrations
└── run.py                  # Application entry point
```


## 📚 API Documentation


## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- Mijanur Molla - *Initial work* - [Github](https://github.com/mija9961)

## 🙏 Acknowledgments

- OpenAI for GPT integration
- Google for GenAI integration
- Flask team for the amazing framework
- Bootstrap team for the UI components

## 📞 Support

For support, email itsmijanur@gmail.com.
