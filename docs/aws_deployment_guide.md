# AWS EC2 Ubuntu 24.04 Deployment & Operations Guide

This guide walks you through deploying the Quiz Platform to an AWS EC2 instance running Ubuntu 24.04 LTS from scratch.

---

## 1. AWS EC2 Provisioning

### Instance Configuration
1. **AMI**: `Ubuntu Server 24.04 LTS` (64-bit x86).
2. **Instance Type**: Recommended minimum **`t3.medium`** (2 vCPUs, 4GB RAM) or higher. 
   > [!IMPORTANT]
   > Do **NOT** use `t2.micro` or `t3.micro`. Loading spaCy NLP pipelines and HuggingFace Transformer models in the FastAPI service/Celery worker requires at least 3-4 GB of RAM, and builds will fail or run out of memory on micro instances.
3. **Elastic IP**: Allocate an Elastic IP address and associate it with your EC2 instance. This prevents your server IP from changing on reboot.
4. **Storage**: Configure at least **20 GB** (gp3 SSD) storage to accommodate OS files, Docker images, and local databases.

### Security Group Settings
Attach a Security Group to your EC2 instance with the following inbound rules:

| Protocol | Port | Source | Purpose |
| :--- | :--- | :--- | :--- |
| **SSH** | 22 | My IP (or trusted CIDR) | Admin server access |
| **HTTP** | 80 | `0.0.0.0/0` and `::/0` | Let's Encrypt challenge & HTTP to HTTPS redirect |
| **HTTPS** | 443 | `0.0.0.0/0` and `::/0` | Secure public web access |

---

## 2. Domain & DNS Configuration

1. Purchase a domain or use an existing domain (e.g., `domain.com`).
2. Go to your DNS provider (e.g., Route 53, GoDaddy, Cloudflare) and create the following records:
   - **A Record**: `domain.com` pointing to the **Elastic IP** of your EC2 instance.
   - **A Record / CNAME**: `www.domain.com` pointing to `domain.com` or the **Elastic IP**.

---

## 3. Host Server Setup

SSH into your Ubuntu 24.04 instance using your key pair:
```bash
ssh -i /path/to/quizApp.pem ubuntu@your-ec2-elastic-ip
```

Update system packages:
```bash
sudo apt update && sudo apt upgrade -y
```

### Git Setup
Clone your repository into `/home/ubuntu/quiz-platform`:
```bash
git clone https://github.com/your-username/your-repo-name.git /home/ubuntu/quiz-platform
cd /home/ubuntu/quiz-platform
```

---

## 4. Environment Variables Configuration

Create a production `.env` file at the root `/home/ubuntu/quiz-platform/.env`:
```bash
nano .env
```

Paste the template below and configure the values (ensure no spaces around `=`):
```env
# Domain Settings
DOMAIN=domain.com
LETSENCRYPT_EMAIL=your-email@domain.com

# Django Configuration
DJANGO_SECRET_KEY=generate-a-strong-random-key-here
DJANGO_DEBUG=False
ALLOWED_HOSTS=domain.com,www.domain.com,django_backend
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://domain.com,https://www.domain.com
CSRF_TRUSTED_ORIGINS=https://domain.com,https://www.domain.com
SECURE_SSL_REDIRECT=True

# MongoDB Connection
# Points to the internal docker mongodb container (no port exposure needed)
MONGO_URI=mongodb://mongodb:27017/nlp_quiz_db

# Redis Connection
REDIS_URL=redis://redis:6379/0

# External APIs
NEWSAPI_KEY=your_newsapi_key
GNEWS_API_KEY=your_gnews_api_key
HF_API_KEY=your_huggingface_api_key
```

---

## 5. Deployment Orchestration

Make the scripts executable:
```bash
chmod +x deploy.sh rollback.sh backup.sh
```

Run the deployment script as root:
```bash
sudo ./deploy.sh
```

### What `deploy.sh` does automatically:
1. Installs Docker Engine and Docker Compose.
2. Installs Certbot via snap.
3. Obtains Let's Encrypt certificates for your domain.
4. Generates/updates the production Nginx config.
5. Builds and launches the 7-container Docker Compose stack.
6. Runs Django SQLite database migrations.
7. Collects Django static assets.
8. Registers a systemd service (`quiz-platform.service`) for auto-starts.
9. Registers a cron job to renew SSL certificates every 12 hours.

---

## 6. Verification and Troubleshooting

### Check Container Status
```bash
sudo docker compose -f docker-compose.production.yml ps
```

### Health Check Tests
Test the endpoints via curl on the host machine:
```bash
# Django check
curl -i http://localhost:8000/health/

# FastAPI check
curl -i http://localhost:8001/api/v1/health
```

---

## 7. Monitoring & Log Management

### View Application Logs
```bash
# All logs
sudo docker compose -f docker-compose.production.yml logs -f

# Specific container logs
sudo docker compose -f docker-compose.production.yml logs -f django_backend
sudo docker compose -f docker-compose.production.yml logs -f fastapi_service
sudo docker compose -f docker-compose.production.yml logs -f celery_worker
```

### Resource Utilization
```bash
sudo docker stats
```

### Docker Log Rotation
To prevent container log files from consuming all disk space, configure Docker daemon logs.
Create or edit `/etc/docker/daemon.json`:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```
Restart docker: `sudo systemctl restart docker`.

---

## 8. Backups and Automated Recovery

### Automated Cron Backups
Create a cron job to run the backup script daily at 2:00 AM.
Open crontab editor:
```bash
sudo crontab -e
```
Add the following line:
```cron
0 2 * * * /home/ubuntu/quiz-platform/backup.sh >> /var/log/quiz-platform-backup.log 2>&1
```

### Restoration Process
In case of server failure or database corruption, you can restore your data from an archive (`tar.gz`) file in `/var/backups/quiz-platform/`:

1. **Extract the backup archive**:
   ```bash
   tar -xzf /var/backups/quiz-platform/quiz_platform_backup_YYYY-MM-DD_HHMMSS.tar.gz -C /tmp/
   ```
2. **Restore SQLite (Django Auth/Admin)**:
   ```bash
   cp /tmp/django_sqlite_*.db /home/ubuntu/quiz-platform/django_backend/db.sqlite3
   ```
3. **Restore MongoDB (Quiz/News data)**:
   ```bash
   # Copy dump archive inside mongodb container and restore
   docker compose -f docker-compose.production.yml cp /tmp/mongodb_*.gz mongodb:/tmp/mongodb_dump.gz
   docker compose -f docker-compose.production.yml exec -T mongodb mongorestore --archive=/tmp/mongodb_dump.gz --gzip --drop
   ```

---

## 9. Code Rollbacks
If a buggy deployment is pushed, rollback to the previous version or a specific git tag:
```bash
# Rollback to the previous version
sudo ./rollback.sh

# Rollback to a specific Git commit or tag
sudo ./rollback.sh v1.0.0
```
This script resets the working directory, rebuilds the images, restarts services, and verifies health checks.
