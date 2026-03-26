# vertex-cms Deployment Guide

## Prerequisites
- Docker
- Docker Compose
- Python 3.8+
- PostgreSQL

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/pnigroh/vertex-cms.git
   cd vertex-cms
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. Build and start Docker containers:
   ```bash
   docker-compose up --build -d
   ```

4. Run database migrations:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. Create superuser (optional):
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. Access the application at:
   http://localhost:8000

## Maintenance
- Stop containers: `docker-compose down`
- View logs: `docker-compose logs -f`
- Run management commands: `docker-compose exec web python manage.py <command>`

## Backup and Restore
- To backup: `docker exec -t your_db_container pg_dumpall -c -U your_db_user > backup.sql`
- To restore: `cat backup.sql | docker exec -i your_db_container psql -U your_db_user`
