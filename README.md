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
