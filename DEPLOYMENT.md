# 🚀 Synapse AI - Production Deployment Guide

This guide provides step-by-step instructions for deploying Synapse AI to production.

## 📋 Prerequisites

- Python 3.12+ 
- Node.js 18+
- PostgreSQL 15+ (recommended for production)
- SSL certificate for HTTPS
- Domain name
- Server with at least 2GB RAM (4GB+ recommended)

## 🔧 Quick Deployment Checklist

### 1. Server Setup

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python, Node.js, PostgreSQL
sudo apt install python3.12 python3.12-pip nodejs npm postgresql postgresql-contrib nginx -y

# Install Python package manager
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE synapse_ai;
CREATE USER synapse_user WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE synapse_ai TO synapse_user;
\q
```

### 3. Application Deployment

```bash
# Clone repository
git clone https://github.com/yourusername/synapse-ai-complete.git
cd synapse-ai-complete

# Backend setup
cd backend
poetry install --only=main
cp .env.example .env

# Edit .env with your production values
nano .env

# Run database migrations
python migrations/migrate.py

# Frontend setup
cd ../frontend
npm install
npm run build

# Copy build files to web server directory
sudo cp -r dist/* /var/www/synapse-ai/
```

### 4. Environment Configuration

Edit `backend/.env` with production values:

```env
ENVIRONMENT=production
DATABASE_URL=postgresql://synapse_user:your_password@localhost:5432/synapse_ai
JWT_SECRET_KEY=your_super_secure_jwt_secret_here
OPENAI_API_KEY=sk-your-openai-key
STRIPE_SECRET_KEY=sk_live_your_stripe_key
CORS_ORIGIN_URL=https://yourdomain.com
```

### 5. Process Management

Create systemd service for the backend:

```bash
sudo nano /etc/systemd/system/synapse-api.service
```

```ini
[Unit]
Description=Synapse AI API
After=network.target postgresql.service

[Service]
Type=exec
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/synapse-ai-complete/backend
Environment=PATH=/home/ubuntu/.local/bin
ExecStart=/home/ubuntu/.local/bin/poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable synapse-api.service
sudo systemctl start synapse-api.service
sudo systemctl status synapse-api.service
```

### 6. Web Server Configuration (Nginx)

```bash
sudo nano /etc/nginx/sites-available/synapse-ai
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Frontend (React app)
    location / {
        root /var/www/synapse-ai;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # WebSocket support (for streaming)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Health check endpoint
    location /healthz {
        proxy_pass http://127.0.0.1:8000/healthz;
        access_log off;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    location /api/ {
        limit_req zone=api burst=20 nodelay;
    }
}
```

```bash
# Enable site and restart nginx
sudo ln -s /etc/nginx/sites-available/synapse-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Generate certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (already set up by certbot)
sudo certbot renew --dry-run
```

### 8. Monitoring Setup

Create log rotation:

```bash
sudo nano /etc/logrotate.d/synapse-ai
```

```
/var/log/synapse-ai/*.log {
    daily
    missingok
    rotate 52
    compress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload synapse-api
    endscript
}
```

### 9. Backup Configuration

```bash
# Create backup script
sudo nano /usr/local/bin/synapse-backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/synapse-ai"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U synapse_user -h localhost synapse_ai > $BACKUP_DIR/db_backup_$DATE.sql

# Application backup
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz -C /home/ubuntu synapse-ai-complete

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
# Make executable and schedule
sudo chmod +x /usr/local/bin/synapse-backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/synapse-backup.sh") | crontab -
```

### 10. Security Hardening

```bash
# Install fail2ban
sudo apt install fail2ban -y

# Configure fail2ban for nginx
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-http-auth]
enabled = true

[nginx-req-limit]
enabled = true
filter = nginx-req-limit
action = iptables-multiport[name=ReqLimit, port="http,https", protocol=tcp]
logpath = /var/log/nginx/*.log
maxretry = 10
findtime = 600
```

## 🔍 Health Checks and Monitoring

### Application Health Endpoints

- **General Health**: `GET /healthz`
- **Database Health**: `GET /health/db` 
- **Rate Limit Stats**: `GET /admin/rate-limits`
- **Security Status**: `GET /admin/security-status`

### System Monitoring Commands

```bash
# Check application status
sudo systemctl status synapse-api

# View application logs
sudo journalctl -u synapse-api -f

# Check database connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname='synapse_ai';"

# Monitor system resources
htop
df -h
free -m
```

### Performance Optimization

```bash
# Optimize PostgreSQL
sudo nano /etc/postgresql/15/main/postgresql.conf
```

Key settings for production:
```
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
max_connections = 100
```

## 🚨 Troubleshooting

### Common Issues

1. **502 Bad Gateway**: Check if backend service is running
   ```bash
   sudo systemctl status synapse-api
   sudo systemctl restart synapse-api
   ```

2. **Database Connection Errors**: Verify PostgreSQL is running
   ```bash
   sudo systemctl status postgresql
   ```

3. **CORS Errors**: Check CORS_ORIGIN_URL in .env
   ```bash
   grep CORS_ORIGIN_URL backend/.env
   ```

4. **SSL Issues**: Verify certificate is valid
   ```bash
   sudo certbot certificates
   ```

### Log Locations

- **Application Logs**: `sudo journalctl -u synapse-api`
- **Nginx Logs**: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- **PostgreSQL Logs**: `/var/log/postgresql/postgresql-15-main.log`

## 📈 Scaling Considerations

### Horizontal Scaling

1. **Load Balancer**: Use HAProxy or AWS Application Load Balancer
2. **Database**: Consider PostgreSQL read replicas
3. **Caching**: Implement Redis for session storage
4. **CDN**: Use CloudFlare or AWS CloudFront for static assets

### Vertical Scaling

1. **Memory**: Increase RAM for better database caching
2. **CPU**: More cores for handling concurrent requests  
3. **Storage**: Use SSD for database performance

### Container Deployment

Consider using Docker and Docker Compose for easier deployment:

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/synapse
    depends_on:
      - db
      
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: synapse_ai
      POSTGRES_USER: synapse_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 🆘 Support

For deployment support:
- Check the troubleshooting section above
- Review application logs for errors
- Verify all environment variables are set correctly
- Ensure all services are running and healthy

## 🔒 Security Best Practices

1. **Keep system updated**: `sudo apt update && sudo apt upgrade`
2. **Use strong passwords**: Generate random passwords for all accounts
3. **Enable firewall**: `sudo ufw enable`
4. **Regular backups**: Verify backups are working and can be restored
5. **Monitor logs**: Set up log monitoring and alerting
6. **SSL only**: Redirect all HTTP traffic to HTTPS
7. **Rate limiting**: Monitor for unusual traffic patterns
8. **API keys**: Rotate API keys regularly

This deployment guide ensures a secure, scalable, and maintainable production environment for Synapse AI.