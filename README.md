# 🏥 Hospital Management System - Dockerized Application

<div align="center">

![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-blue?style=for-the-badge&logo=mysql&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-2.0-blue?style=for-the-badge&logo=docker&logoColor=white)

**A Complete Hospital Management System with Docker Containerization**

[Features](#-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [Deployment](#-deployment-commands) • [API Docs](#-api-documentation)

</div>

---

## 📋 Overview

Hospital Management System jo Docker containers mein deploy hota hai with:
- ✅ Patient management
- ✅ Doctor management
- ✅ Appointment scheduling
- ✅ Medical records management
- ✅ Billing system
- ✅ User authentication
- ✅ RESTful API
- ✅ MySQL database
- ✅ Docker containerization
- ✅ Production-ready setup

---

## 🚀 Quick Start

### One-Command Deployment

```bash
git clone https://github.com/fsdmubashar/hospital-management-project.git && \
cd hospital-management-project && \
docker-compose up --build -d
```

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Hospital Management System             │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Frontend   │  │   Backend    │  │   Database   │ │
│  │  Container   │◄─┤  Container   │◄─┤  Container   │ │
│  │              │  │              │  │              │ │
│  │  Port: 3000  │  │  Port: 8000  │  │  Port: 3306  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Docker Network Architecture

```
┌──────────────────────────────────────────────────────┐
│              Docker Bridge Network                    │
│                                                       │
│  ┌──────────────┐   ┌──────────────┐   ┌─────────┐ │
│  │   Web App    │   │   API Server │   │  MySQL  │ │
│  │  Container   │◄─►│  Container   │◄─►│  DB     │ │
│  │              │   │              │   │         │ │
│  │ nginx/apache │   │ Python/Node  │   │ MySQL   │ │
│  └──────────────┘   └──────────────┘   └─────────┘ │
│                                                       │
└──────────────────────────────────────────────────────┘
```

---

## 📦 Prerequisites

```bash
# Docker version check
docker --version

# Docker Compose version check
docker-compose --version

# Git version check
git --version
```

**Required:**
- Docker 24.0+
- Docker Compose 2.0+
- Git

---

## ⚙️ Deployment Commands

### 1. Clone Repository

```bash
git clone https://github.com/fsdmubashar/hospital-management-project.git
cd hospital-management-project
```

### 2. Environment Setup

```bash
cp .env.example .env
nano .env
```

### 3. Build Docker Images

```bash
docker-compose build
```

### 4. Start Containers

```bash
docker-compose up -d
```

### 5. Run Database Migrations

```bash
docker-compose exec backend python manage.py migrate
```

### 6. Create Admin User

```bash
docker-compose exec backend python manage.py createsuperuser
```

### 7. Verify Containers

```bash
docker-compose ps
```

---

## 🐳 Important Dockerfile Configuration

### **Ubuntu Base Image with UI Terminal Support**

⚠️ **Critical Requirement:** Dockerfile mein Ubuntu base image use karein jo **UI/Terminal support** karta ho.

**Recommended Base Images:**

```dockerfile
# Option 1: Ubuntu with full desktop support
FROM ubuntu:22.04

# Install essential packages for UI/Terminal
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    libncurses5-dev \
    libncursesw5-dev \
    wget \
    curl \
    git \
    nano \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Set environment for proper terminal behavior
ENV TERM=xterm-256color
ENV DEBIAN_FRONTEND=noninteractive
```

**Ya alternative:**

```dockerfile
# Option 2: Python base with Ubuntu dependencies
FROM python:3.10-slim-bullseye

# Add terminal support packages
RUN apt-get update && apt-get install -y \
    libncurses5 \
    libncursesw5 \
    procps \
    && rm -rf /var/lib/apt/lists/*

ENV TERM=xterm-256color
```

### **Why UI Terminal Support?**

UI terminal support zaroori hai taake:
- ✅ Interactive commands properly run ho sakein
- ✅ Terminal-based tools (nano, vim) kaam karein
- ✅ Color output properly displays ho
- ✅ Ncurses-based applications run ho sakein
- ✅ Python interactive shell properly kaam kare

---

## 🔧 Environment Variables (.env)

```env
MYSQL_ROOT_PASSWORD=root_password
MYSQL_DATABASE=hospital_db
MYSQL_USER=hospital_user
MYSQL_PASSWORD=hospital_pass

APP_PORT=8000
SECRET_KEY=your-secret-key-here

FRONTEND_PORT=3000
```

---

## 🐳 Docker Commands

### Start/Stop Services

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart
```

### View Logs

```bash
# All logs
docker-compose logs -f

# Specific container
docker-compose logs -f backend
```

### Execute Commands

```bash
# Backend shell
docker-compose exec backend bash

# Database access
docker-compose exec database mysql -u hospital_user -p

# Django shell
docker-compose exec backend python manage.py shell
```

### Rebuild

```bash
# Rebuild all
docker-compose build --no-cache

# Rebuild specific service
docker-compose build backend
```

### Database Operations

```bash
# Backup
docker-compose exec database mysqldump -u hospital_user -p hospital_db > backup.sql

# Restore
docker-compose exec -T database mysql -u hospital_user -p hospital_db < backup.sql
```

---

## 📁 Project Structure

```
hospital-management-project/
│
├── backend/                      # Backend application
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── hospital/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── patients/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   ├── doctors/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   └── appointments/
│       ├── models.py
│       ├── views.py
│       ├── serializers.py
│       └── urls.py
│
├── frontend/                     # Frontend application
│   ├── Dockerfile
│   ├── package.json
│   ├── public/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── services/
│       └── App.js
│
├── database/                     # Database scripts
│   ├── init.sql
│   └── seed.sql
│
├── docker-compose.yml           # Docker Compose configuration
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── README.md                    # This file
└── LICENSE                      # MIT License
```

---

## 🔍 Troubleshooting

### Container Issues

```bash
# Check logs
docker-compose logs backend

# Restart container
docker-compose restart backend

# Rebuild
docker-compose up --build
```

### Database Connection

```bash
# Check database status
docker-compose ps

# Test connection
docker-compose exec database mysql -u hospital_user -p hospital_db
```

### Port Conflicts

```bash
# Find process
lsof -i :8000

# Kill process
kill -9 <PID>
```

---

## 🌐 Access URLs

```
Frontend:  http://localhost:3000
Backend:   http://localhost:8000
Database:  localhost:3306
```

---

## 🔄 Git Workflow

```bash
# Clone
git clone https://github.com/fsdmubashar/hospital-management-project.git

# Pull updates
git pull origin main

# Commit changes
git add .
git commit -m "Your message"
git push origin main
```

---

## 📄 License

MIT License

```
Copyright (c) 2025 Muhammad Mubashar Karamat Ali

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📞 Contact

**Muhammad Mubashar Karamat Ali**

[![Email](https://img.shields.io/badge/Email-Contact-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:city.mubashar@gmail.com)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/fsdmubashar)

**Project:** [https://github.com/fsdmubashar/hospital-management-project](https://github.com/fsdmubashar/hospital-management-project)

---

## 📞 Contact

**Muhammad Mubashar Karamat Ali**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/mubashar-karamat-833457245/)
[![Email](https://img.shields.io/badge/Email-Contact-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:city.mubashar@gmail.com)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/fsdmubashar)
[![Medium](https://img.shields.io/badge/Medium-Follow-12100E?style=for-the-badge&logo=medium&logoColor=white)](https://medium.com/@city.mubashar)

**Project Link:** [https://github.com/fsdmubashar/hospital-management-project](https://github.com/fsdmubashar/hospital-management-project)

---

## 🙏 Acknowledgments

- Docker team for containerization platform
- Python/Django community
- React.js team
- MySQL team
- Open source contributors

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [MySQL Documentation](https://dev.mysql.com/doc/)
- [Django Documentation](https://docs.djangoproject.com/)
- [React Documentation](https://react.dev/)

---

<div align="center">

**⭐ If you find this project helpful, please give it a star!**

**Made with ❤️ by [Muhammad Mubashar Karamat Ali](https://github.com/fsdmubashar)**

![Visitors](https://komarev.com/ghpvc/?username=fsdmubashar-hospital&color=brightgreen&style=for-the-badge)

</div>
