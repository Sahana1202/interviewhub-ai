# 🚀 InterviewHub AI – AI-Powered Interview Preparation Platform

InterviewHub AI is a web-based interview preparation platform designed to help students and job seekers prepare for technical interviews through an interactive application.

The project uses a modern frontend and Python backend architecture to provide a foundation for interview preparation, user management, and AI-powered functionality.

## ✨ Project Overview

InterviewHub AI aims to make interview preparation more accessible through a centralized web application.

### Key Components

- **Frontend Application:** Interactive user interface built with React.js and Vite.
- **Backend API:** Python-based REST API powered by FastAPI.
- **Database:** MySQL for persistent application data.
- **API Integration:** Communication between the frontend and backend through HTTP requests.
- **Deployment:** Frontend hosted on Netlify, with backend deployment configured separately.

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Frontend | React.js, JavaScript, Vite |
| Backend | Python, FastAPI |
| Database | MySQL |
| API | REST API |
| Frontend Deployment | Netlify |
| Backend Deployment | Railway |
| Version Control | Git, GitHub |

## 🏗️ Project Architecture

```text
InterviewHub-AI/
│
├── interviewhub-ai/
│   │
│   ├── frontend/
│   │   ├── src/
│   │   ├── public/
│   │   ├── package.json
│   │   └── vite.config.js
│   │
│   └── backend/
│       ├── app/
│       ├── requirements.txt
│       └── .env.example
│
└── README.md
```

*Note: This is a simplified architecture overview. Refer to the actual folders and files in the repository for the complete structure.*

## ⚙️ Getting Started

Follow these steps to run the project locally.

### 1. Clone the Repository

```bash
git clone https://github.com/Sahana1202/interviewhub-ai.git

cd interviewhub-ai/interviewhub-ai
```

### 2. Frontend Setup

Navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The Vite development server will display its local URL in the terminal.

### 3. Backend Setup

Open another terminal and navigate to the backend directory:

```bash
cd interviewhub-ai/backend
```

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate the environment on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Configure the backend environment variables using the provided `.env.example` file.

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The API documentation can be accessed at:

```text
http://localhost:8000/docs
```

*Ensure that the database is configured and the required environment variables are set before running the backend.*

## 🗄️ Database Configuration

InterviewHub AI uses MySQL as its database.

To configure the database:

1. Install or create a MySQL database.
2. Create the required database and user.
3. Configure the database connection string in the backend environment variables.
4. Apply the project's required database migrations.
5. Start the backend server.

Never commit database passwords, API keys, or other sensitive credentials to GitHub.

## 🌐 Deployment

The application uses a separate frontend and backend deployment approach.

### Frontend – Netlify

The React + Vite frontend is deployed using Netlify.

**Production URL:**

https://interviewhubai.netlify.app

Deployment configuration:

| Setting | Value |
|---|---|
| Build command | `npm run build` |
| Publish directory | `dist` |
| Base directory | `interviewhub-ai/frontend` |
| Branch | `main` |

### Backend – Railway

The FastAPI backend is intended to be hosted separately on Railway.

The frontend communicates with the backend using the configured API base URL.

Backend deployment and production database configuration must be completed separately.

## 🔐 Security

- Store API keys and passwords in environment variables.
- Never expose backend secrets in frontend code.
- Configure CORS to allow only trusted frontend origins.
- Use secure authentication and database access practices.
- Do not commit `.env` files to the repository.

## 🎯 Project Objectives

- Develop a web-based interview preparation application.
- Build a responsive and user-friendly frontend.
- Implement backend services using FastAPI.
- Integrate persistent database storage.
- Establish a scalable frontend and backend architecture.
- Deploy the application using cloud hosting platforms.

## 🚀 Future Enhancements

- Expand AI-powered interview preparation capabilities.
- Improve interview performance analysis.
- Add more practice categories and question sets.
- Enhance user dashboards and progress tracking.
- Improve application scalability and performance.

## 👩‍💻 Author

**Sahana**

GitHub: https://github.com/Sahana1202

## 📄 License

This project is available for educational and development purposes. Add an appropriate open-source license if you intend to distribute it under one.

---

⭐ If you find this project interesting, consider starring the repository!
