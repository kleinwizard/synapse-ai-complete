#!/bin/bash
set -euo pipefail

# Synapse AI Production Deployment Script
echo "🚀 Starting Synapse AI Production Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found!"
    print_status "Please copy .env.production to .env and configure your settings"
    exit 1
fi

# Load environment variables
source .env

# Validate required environment variables
REQUIRED_VARS=("DOMAIN" "DB_PASSWORD" "JWT_SECRET_KEY" "OPENAI_API_KEY")

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        print_error "Required environment variable $var is not set"
        exit 1
    fi
done

print_success "Environment variables validated"

# Update domain in nginx configuration
print_status "Updating domain configuration..."
sed -i "s/DOMAIN_PLACEHOLDER/${DOMAIN}/g" nginx/conf.d/synapse.conf
print_success "Domain configuration updated"

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    print_success "Docker installed"
else
    print_success "Docker already installed"
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed"
else
    print_success "Docker Compose already installed"
fi

# Create necessary directories
print_status "Creating directories..."
sudo mkdir -p /var/www/html
sudo mkdir -p ./backups
sudo mkdir -p ./nginx/html
print_success "Directories created"

# Stop existing containers if running
print_status "Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down --remove-orphans || true

# Build and start services
print_status "Building and starting services..."
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to be healthy
print_status "Waiting for services to be ready..."
sleep 30

# Check service health
print_status "Checking service health..."
if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    print_success "Services are running"
else
    print_error "Some services failed to start"
    docker-compose -f docker-compose.prod.yml logs
    exit 1
fi

# Run database migrations
print_status "Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T api python migrations/migrate.py

# Install Certbot for SSL certificates
if ! command -v certbot &> /dev/null; then
    print_status "Installing Certbot..."
    sudo apt update
    sudo apt install -y certbot
    print_success "Certbot installed"
fi

# Generate SSL certificate
print_status "Generating SSL certificate..."
sudo certbot certonly --webroot \
    --webroot-path=/var/www/html \
    --email admin@${DOMAIN} \
    --agree-tos \
    --no-eff-email \
    -d ${DOMAIN} \
    --non-interactive || {
    print_warning "SSL certificate generation failed. You may need to configure DNS first."
    print_status "The application is running on HTTP. Configure SSL manually later."
}

# Restart nginx with SSL
print_status "Restarting nginx with SSL configuration..."
docker-compose -f docker-compose.prod.yml restart nginx

# Set up automatic SSL renewal
print_status "Setting up SSL certificate auto-renewal..."
(crontab -l 2>/dev/null; echo "0 12 * * * certbot renew --quiet && docker-compose -f $(pwd)/docker-compose.prod.yml restart nginx") | crontab -

# Create backup script
print_status "Creating backup script..."
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U synapse_user synapse_ai | gzip > ${BACKUP_DIR}/db_backup_${DATE}.sql.gz

# Application backup
tar -czf ${BACKUP_DIR}/app_backup_${DATE}.tar.gz --exclude='./backups' --exclude='.git' .

# Clean old backups (keep last 7 days)
find ${BACKUP_DIR} -name "*.gz" -mtime +7 -delete

echo "Backup completed: ${DATE}"
EOF

chmod +x backup.sh

# Schedule daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * cd $(pwd) && ./backup.sh >> backup.log 2>&1") | crontab -

print_success "Backup system configured"

# Display final status
print_status "Deployment Summary:"
echo "===================="
echo "🌐 Domain: https://${DOMAIN}"
echo "🔧 Backend API: https://${DOMAIN}/api"
echo "📊 Health Check: https://${DOMAIN}/api/healthz"
echo "🔒 Admin Panel: https://${DOMAIN}/api/admin/security-status"
echo ""

print_status "Testing application..."

# Test health endpoints
if curl -f -s "http://localhost:8000/healthz" > /dev/null; then
    print_success "Backend health check passed"
else
    print_warning "Backend health check failed"
fi

if curl -f -s "http://localhost:3000/health" > /dev/null; then
    print_success "Frontend health check passed"
else
    print_warning "Frontend health check failed"
fi

print_success "🎉 Deployment completed!"
print_status "Your Synapse AI application is now running in production!"
print_warning "Don't forget to:"
echo "  1. Point your domain DNS to this server's IP address"
echo "  2. Test the application at https://${DOMAIN}"
echo "  3. Monitor the logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  4. Check SSL status after DNS propagation"