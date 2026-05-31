#!/usr/bin/env bash
# Production Deployment Script for Quiz Platform
# Target OS: Ubuntu 24.04 LTS

set -e

# Configuration
APP_DIR="/home/ubuntu/quiz-platform"
SERVICE_NAME="quiz-platform.service"

echo "=== Starting deployment process ==="

# 1. Check prerequisites
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (using sudo)."
  exit 1
fi

# Determine script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# 2. Check if .env exists
if [ ! -f .env ]; then
  echo "Error: .env file is missing in $SCRIPT_DIR!"
  echo "Please create a .env file with production environment variables before running this script."
  exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Domain check
if [ -z "$DOMAIN" ]; then
  echo "Error: DOMAIN environment variable is not defined in .env."
  exit 1
fi

if [ -z "$LETSENCRYPT_EMAIL" ]; then
  echo "Error: LETSENCRYPT_EMAIL environment variable is not defined in .env."
  exit 1
fi

echo "Deploying for Domain: $DOMAIN"
echo "SSL Contact Email: $LETSENCRYPT_EMAIL"

# 3. Install Docker & Docker Compose if missing
if ! [ -x "$(command -v docker)" ]; then
  echo "Docker is not installed. Installing Docker..."
  apt-get update
  apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
  mkdir -p /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
fi

# 4. Install Certbot for SSL if missing
if ! [ -x "$(command -v certbot)" ]; then
  echo "Certbot is not installed. Installing Certbot via snap..."
  apt-get install -y snapd
  snap install core; snap refresh core
  snap install --classic certbot
  ln -sf /snap/bin/certbot /usr/bin/certbot
fi

# 5. Bootstrap Let's Encrypt SSL certificates
SSL_DIR="/etc/letsencrypt/live/$DOMAIN"
if [ ! -d "$SSL_DIR" ]; then
  echo "SSL certificates not found for $DOMAIN. Requesting initial certificate via Certbot standalone..."
  
  # Ensure port 80 is not currently bound by docker compose (shutdown stack)
  docker compose -f docker-compose.production.yml down || true
  
  # Request certificate
  set +e
  certbot certonly --standalone \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --email "$LETSENCRYPT_EMAIL" \
    --agree-tos \
    --non-interactive \
    --no-eff-email
  
  # Fallback to single domain if www fail
  CERT_STATUS=$?
  set -e
  if [ $CERT_STATUS -ne 0 ]; then
    echo "SSL request with www.$DOMAIN failed. Retrying with main domain $DOMAIN only..."
    certbot certonly --standalone \
      -d "$DOMAIN" \
      --email "$LETSENCRYPT_EMAIL" \
      --agree-tos \
      --non-interactive \
      --no-eff-email
  fi
else
  echo "SSL certificates already exist for $DOMAIN."
fi

# 6. Update Nginx configuration with the actual domain name
echo "Updating Nginx configuration with domain: $DOMAIN"
sed -i "s/domain.com/$DOMAIN/g" ./nginx/nginx.production.conf

# 7. Start/rebuild containers
echo "Starting application containers using Docker Compose..."
docker compose -f docker-compose.production.yml build
docker compose -f docker-compose.production.yml up -d

# 8. Post-startup operations (Migrations, Static files)
echo "Running Django migrations..."
docker compose -f docker-compose.production.yml exec -T django_backend python manage.py migrate --noinput

echo "Collecting Django static files..."
docker compose -f docker-compose.production.yml exec -T django_backend python manage.py collectstatic --noinput

# 9. Register and start systemd service
if [ -f "quiz-platform.service" ]; then
  echo "Installing systemd service unit..."
  
  # Copy service file and replace folder path if necessary
  cp quiz-platform.service /etc/systemd/system/$SERVICE_NAME
  
  # Update WorkingDirectory in systemd file if it differs
  sed -i "s|WorkingDirectory=.*|WorkingDirectory=$SCRIPT_DIR|g" /etc/systemd/system/$SERVICE_NAME
  
  systemctl daemon-reload
  systemctl enable $SERVICE_NAME
  systemctl start $SERVICE_NAME
fi

# 10. Set up auto-renewal cronjob for SSL certs
CRON_JOB="0 */12 * * * certbot renew --post-hook \"docker compose -f $SCRIPT_DIR/docker-compose.production.yml exec -T nginx nginx -s reload\" >> /var/log/certbot-renew.log 2>&1"
(crontab -l 2>/dev/null | grep -F "certbot renew" || (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -)

echo "=== Deployment Completed Successfully ==="
