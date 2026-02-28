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

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Deployment Commands](#-deployment-commands)
- [Docker Configuration](#-docker-configuration)
- [Environment Variables](#-environment-variables)
- [API Documentation](#-api-documentation)
- [Database Schema](#-database-schema)
- [Project Structure](#-project-structure)
- [Git Setup Guide](#-git-setup-guide)
- [Troubleshooting](#-troubleshooting)
- [Production Deployment](#-production-deployment)
- [Monitoring](#-monitoring)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## 🌟 Overview

Yeh ek **complete Hospital Management System** hai jo Docker containers mein deploy hota hai. Is project mein:

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

## ✨ Features

### 🏥 **Hospital Management Features**

- **Patient Management**
  - Patient registration
  - Medical history tracking
  - Patient search and filtering
  - Patient records management

- **Doctor Management**
  - Doctor profiles
  - Specialization management
  - Availability scheduling
  - Doctor-patient assignment

- **Appointment System**
  - Appointment booking
  - Schedule management
  - Appointment reminders
  - Status tracking

- **Billing & Payments**
  - Invoice generation
  - Payment processing
  - Payment history
  - Reports generation

### 🐳 **Technical Features**

- **Containerization**
  - Multi-container Docker setup
  - Docker Compose orchestration
  - Isolated services
  - Easy deployment

- **Database**
  - MySQL database
  - Automated migrations
  - Data persistence
  - Backup support

- **API**
  - RESTful endpoints
  - JSON responses
  - Authentication
  - CORS support

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

### Required Software

| Software | Version | Download Link |
|----------|---------|---------------|
| Docker | 24.0+ | [Get Docker](https://www.docker.com/products/docker-desktop/) |
| Docker Compose | 2.0+ | Included with Docker Desktop |
| Git | Latest | [Get Git](https://git-scm.com/downloads) |

### System Requirements

```
Minimum:
- OS: Ubuntu 20.04+ / Windows 10+ / macOS 10.15+
- RAM: 4 GB
- Storage: 10 GB
- CPU: 2 cores

Recommended:
- OS: Ubuntu 22.04+ / Windows 11 / macOS 12+
- RAM: 8 GB
- Storage: 20 GB
- CPU: 4 cores
```

---

## 🚀 Quick Start

### One-Command Deployment

```bash
# Clone, build, and run in one command
git clone https://github.com/fsdmubashar/hospital-management-project.git && \
cd hospital-management-project && \
docker-compose up --build -d
```

### Access Application

```
Frontend:  http://localhost:3000
API:       http://localhost:8000
Database:  localhost:3306
```

---

## 📋 Deployment Commands

### Step-by-Step Deployment

#### 1️⃣ **Clone Repository**

```bash
# Clone the repository
git clone https://github.com/fsdmubashar/hospital-management-project.git

# Navigate to project directory
cd hospital-management-project
```

#### 2️⃣ **Environment Configuration**

```bash
# Create .env file from template
cp .env.example .env

# Edit environment variables
nano .env
```

**Required Environment Variables:**
```env
# Database Configuration
MYSQL_ROOT_PASSWORD=root_password
MYSQL_DATABASE=hospital_db
MYSQL_USER=hospital_user
MYSQL_PASSWORD=hospital_pass

# Application Configuration
APP_PORT=8000
SECRET_KEY=your-secret-key-here
DEBUG=False

# Frontend Configuration
FRONTEND_PORT=3000
API_URL=http://localhost:8000
```

#### 3️⃣ **Build Docker Images**

```bash
# Build all containers
docker-compose build

# Or build with no cache (fresh build)
docker-compose build --no-cache
```

#### 4️⃣ **Start Services**

```bash
# Start all containers in detached mode
docker-compose up -d

# Or start with logs visible
docker-compose up
```

#### 5️⃣ **Run Database Migrations**

```bash
# Execute migrations inside backend container
docker-compose exec backend python manage.py migrate

# Or if using different command
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
```

#### 6️⃣ **Create Superuser (Admin)**

```bash
# Create admin user for Django
docker-compose exec backend python manage.py createsuperuser

# Follow prompts to enter:
# - Username
# - Email
# - Password
```

#### 7️⃣ **Verify Installation**

```bash
# Check running containers
docker-compose ps

# Expected output:
# NAME                    STATUS              PORTS
# backend                 Up                  0.0.0.0:8000->8000/tcp
# frontend                Up                  0.0.0.0:3000->3000/tcp
# database                Up                  0.0.0.0:3306->3306/tcp
```

---

## 🐳 Docker Configuration

### docker-compose.yml Overview

```yaml
version: '3.8'

services:
  # Database Container
  database:
    image: mysql:8.0
    container_name: hospital_db
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - hospital_network

  # Backend Container
  backend:
    build: ./backend
    container_name: hospital_backend
    restart: always
    depends_on:
      - database
    environment:
      DB_HOST: database
      DB_NAME: ${MYSQL_DATABASE}
      DB_USER: ${MYSQL_USER}
      DB_PASSWORD: ${MYSQL_PASSWORD}
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    networks:
      - hospital_network

  # Frontend Container
  frontend:
    build: ./frontend
    container_name: hospital_frontend
    restart: always
    depends_on:
      - backend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
    networks:
      - hospital_network

volumes:
  mysql_data:

networks:
  hospital_network:
    driver: bridge
```

---

## 🔧 Environment Variables

### .env File Structure

```env
# ===========================
# Database Configuration
# ===========================
MYSQL_ROOT_PASSWORD=root_secure_password
MYSQL_DATABASE=hospital_db
MYSQL_USER=hospital_user
MYSQL_PASSWORD=hospital_secure_pass
DB_HOST=database
DB_PORT=3306

# ===========================
# Backend Configuration
# ===========================
APP_PORT=8000
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# ===========================
# Frontend Configuration
# ===========================
FRONTEND_PORT=3000
REACT_APP_API_URL=http://localhost:8000/api
NODE_ENV=production

# ===========================
# Email Configuration (Optional)
# ===========================
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# ===========================
# AWS S3 Configuration (Optional)
# ===========================
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=hospital-media
AWS_S3_REGION_NAME=us-east-1
```

---

## 📡 API Documentation

### Base URL
```
http://localhost:8000/api
```

### Authentication Endpoints

#### 1. User Registration

**POST** `/api/auth/register`

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

---

#### 2. User Login

**POST** `/api/auth/login`

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "secure_password"
  }'
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

---

### Patient Endpoints

#### 3. Create Patient

**POST** `/api/patients/`

```bash
curl -X POST http://localhost:8000/api/patients/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith",
    "date_of_birth": "1990-05-15",
    "gender": "Female",
    "phone": "+1234567890",
    "email": "jane.smith@example.com",
    "address": "123 Main St, City"
  }'
```

---

#### 4. Get All Patients

**GET** `/api/patients/`

```bash
curl -X GET http://localhost:8000/api/patients/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

#### 5. Get Patient by ID

**GET** `/api/patients/{id}/`

```bash
curl -X GET http://localhost:8000/api/patients/1/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Doctor Endpoints

#### 6. Create Doctor

**POST** `/api/doctors/`

```bash
curl -X POST http://localhost:8000/api/doctors/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Dr. Sarah",
    "last_name": "Johnson",
    "specialization": "Cardiology",
    "phone": "+1987654321",
    "email": "dr.sarah@hospital.com",
    "qualification": "MD, MBBS"
  }'
```

---

#### 7. Get All Doctors

**GET** `/api/doctors/`

```bash
curl -X GET http://localhost:8000/api/doctors/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Appointment Endpoints

#### 8. Create Appointment

**POST** `/api/appointments/`

```bash
curl -X POST http://localhost:8000/api/appointments/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "doctor_id": 1,
    "appointment_date": "2025-02-10",
    "appointment_time": "10:00:00",
    "reason": "Regular checkup"
  }'
```

---

#### 9. Get All Appointments

**GET** `/api/appointments/`

```bash
curl -X GET http://localhost:8000/api/appointments/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 💾 Database Schema

### Main Tables

```sql
-- Patients Table
CREATE TABLE patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender ENUM('Male', 'Female', 'Other'),
    phone VARCHAR(20),
    email VARCHAR(100) UNIQUE,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Doctors Table
CREATE TABLE doctors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100) UNIQUE,
    qualification VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Appointments Table
CREATE TABLE appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status ENUM('Scheduled', 'Completed', 'Cancelled') DEFAULT 'Scheduled',
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);
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

## 🌐 Git Setup Guide

### Initial Setup

```bash
# Configure Git
git config --global user.name "fsdmubashar"
git config --global user.email "107295594+fsdmubashar@users.noreply.github.com"
git config --global init.defaultBranch main
```

### Clone Repository

```bash
# Clone project
git clone https://github.com/fsdmubashar/hospital-management-project.git
cd hospital-management-project
```

### Making Changes

```bash
# Check status
git status

# Add changes
git add .

# Commit changes
git commit -m "Updated feature X"

# Push changes
git push origin main
```

---

## 🔍 Troubleshooting

### Issue 1: Container Won't Start

```bash
# Check container logs
docker-compose logs backend
docker-compose logs database

# Restart containers
docker-compose restart

# Rebuild containers
docker-compose down
docker-compose up --build
```

---

### Issue 2: Database Connection Error

```bash
# Check if database is running
docker-compose ps

# Check database logs
docker-compose logs database

# Restart database
docker-compose restart database

# Test connection
docker-compose exec database mysql -u hospital_user -p hospital_db
```

---

### Issue 3: Port Already in Use

```bash
# Find process using port
lsof -i :8000
lsof -i :3000
lsof -i :3306

# Kill process
kill -9 <PID>

# Or change ports in docker-compose.yml
ports:
  - "8001:8000"  # Changed from 8000
```

---

### Issue 4: Permission Denied

```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Fix Docker permissions
sudo chmod 666 /var/run/docker.sock
```

---

## 🚀 Production Deployment

### Using Docker Compose

```bash
# Production build
docker-compose -f docker-compose.prod.yml up -d --build

# Scale services
docker-compose up -d --scale backend=3
```

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml hospital

# List services
docker service ls

# Scale service
docker service scale hospital_backend=3
```

---

## 📊 Monitoring

### Docker Commands

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f

# View resource usage
docker stats

# Execute commands in container
docker-compose exec backend python manage.py shell
```

### Health Checks

```bash
# Backend health check
curl http://localhost:8000/api/health

# Database health check
docker-compose exec database mysqladmin ping -h localhost
```

---

## 💡 Useful Docker Commands

```bash
# Stop all containers
docker-compose down

# Remove all containers and volumes
docker-compose down -v

# View container logs
docker-compose logs -f backend

# Rebuild specific service
docker-compose build backend

# Run command in container
docker-compose exec backend python manage.py migrate

# Access container shell
docker-compose exec backend bash

# Backup database
docker-compose exec database mysqldump -u hospital_user -p hospital_db > backup.sql

# Restore database
docker-compose exec -T database mysql -u hospital_user -p hospital_db < backup.sql
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

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


























# Hospital Management System (PyQt6)

Hospital Management System is a desktop application built with `Python`, `PyQt6`, and `SQLAlchemy`.  
It provides role-based workflows for common hospital operations such as patients, doctors, appointments, billing, pharmacy, and reporting.

## Docker Setup

### Prerequisites

- Docker Engine (with Compose plugin)
- Linux host with X11 (for GUI display)

### 1) Enable GUI Access from Host (Linux)

Run this on your host before starting the container:

```bash
xhost +local:docker
```

This allows Docker containers to access your local X server.

### 2) Build and Initialize

Use the provided setup script:

```bash
chmod +x setup.sh
./setup.sh
```

What this script does:

- builds the Docker image
- creates required runtime directories
- initializes and seeds the database once

For database switching, copy `.env.example` to `.env` and set `HMS_DB_URL`.

```bash
cp .env.example .env
```

### 3) Run the Application

```bash
docker compose up
```

The app starts with automatic DB init + seed and then launches the PyQt6 GUI.

### 4) Stop the Application

```bash
docker compose down
```

## Database Backends (SQLAlchemy)

Switch backend by changing only `HMS_DB_URL` in `.env`:

- SQLite: `sqlite:////app/hospital.db`
- MySQL/MariaDB: `mysql+pymysql://user:pass@mysql:3306/hospital_db`
- PostgreSQL: `postgresql+psycopg2://user:pass@postgres:5432/hospital_db`

Optional local DB containers are available under the `debug` profile:

```bash
docker compose --profile debug up
```

## Default Login

- Username: `admin`
- Password: `admin123`

## Notes

- The container runs as non-root user `hospitaluser` for better security.
- `QT_X11_NO_MITSHM=1` is enabled to improve X11 compatibility in Docker.
- Container limits are set to `1 CPU` and `1GB RAM` in `docker-compose.yml`.
