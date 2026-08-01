#!/bin/bash
# 
# generate_ssl_cert.sh - Generate self-signed SSL certificates for development
# 
# WARNING: These certificates are for development/testing only!
# They should NEVER be used in production or committed to git.
# For production, use Let's Encrypt/certbot or a proper CA.
#
# Usage: DOMAIN=staging.aifp-aos.local ./scripts/generate_ssl_cert.sh
# Or: ./scripts/generate_ssl_cert.sh staging.aifp-aos.local

set -e

# Configuration
DOMAIN="${1:-${DOMAIN:-staging.aifp-aos.local}}"
CERT_DIR="nginx/ssl"
DAYS_VALID=365

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}SSL Certificate Generator (Dev Only)${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Warning message
echo -e "${RED}WARNING: This generates self-signed certificates for development only!${NC}"
echo -e "${RED}Do NOT use these in production or commit them to git.${NC}"
echo ""

# Confirm
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Generate the certificate using Python
echo "Generating self-signed certificate for: $DOMAIN"
echo "Valid for: $DAYS_VALID days"
echo ""

python scripts/generate_ssl_cert.py "$DOMAIN" --cert-dir "$CERT_DIR" --days "$DAYS_VALID"

echo ""
echo -e "${GREEN}[SUCCESS] Certificates generated successfully!${NC}"
echo ""
echo "The nginx/ssl directory is in .gitignore, so these won't be committed."
echo ""
echo "For production, use Let's Encrypt:"
echo "  sudo certbot certonly --standalone -d your-domain.com"
echo "  sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/"
echo "  sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/"
