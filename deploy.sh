#!/bin/bash

# TinyVault Deployment Script
# This script deploys the TinyVault application to an EC2 instance using Ansible

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required environment variables are set
check_env_vars() {
    local required_vars=(
        "EC2_HOST"
        "SSH_PRIVATE_KEY"
        "DB_URL"
        "TELEGRAM_BOT_TOKEN"
        "ADMIN_API_KEY"
        "WEBHOOK_SECRET"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "Please set these variables in your environment or create a .env file"
        exit 1
    fi
}

# Create SSH key file
setup_ssh() {
    print_status "Setting up SSH connection..."
    
    mkdir -p ~/.ssh
    echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
    chmod 600 ~/.ssh/id_rsa
    
    # Add host to known_hosts
    ssh-keyscan -H "$EC2_HOST" >> ~/.ssh/known_hosts 2>/dev/null || true
    
    print_status "SSH setup completed"
}

# Cleanup SSH key
cleanup_ssh() {
    print_status "Cleaning up SSH key..."
    rm -f ~/.ssh/id_rsa
    print_status "SSH key cleaned up"
}

# Deploy using Ansible
deploy_with_ansible() {
    print_status "Starting deployment with Ansible..."
    
    cd ansible
    
    # Install required Ansible collections
    print_status "Installing required Ansible collections..."
    ansible-galaxy collection install -r requirements.yml
    
    # Export environment variables for Ansible
    export EC2_HOST
    export SSH_PRIVATE_KEY_PATH=~/.ssh/id_rsa
    export DB_URL
    export TELEGRAM_BOT_TOKEN
    export ADMIN_API_KEY
    export WEBHOOK_SECRET
    
    # Run Ansible playbook
    ansible-playbook -i inventory.yml playbook.yml -v
    
    cd ..
    
    print_status "Ansible deployment completed"
}

# Verify deployment
verify_deployment() {
    print_status "Verifying deployment..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        print_status "Attempt $attempt/$max_attempts: Checking application health..."
        
        if curl -f "http://$EC2_HOST:8000/health" >/dev/null 2>&1; then
            print_status "Application is healthy! 🎉"
            return 0
        fi
        
        if [[ $attempt -lt $max_attempts ]]; then
            print_warning "Application not ready yet, waiting 10 seconds..."
            sleep 10
        fi
        
        ((attempt++))
    done
    
    print_error "Application failed to become healthy after $max_attempts attempts"
    return 1
}

# Display deployment information
show_deployment_info() {
    print_status "Deployment completed successfully! 🚀"
    echo ""
    echo "Application Information:"
    echo "  - Application URL: http://$EC2_HOST:8000"
    echo "  - Health Check: http://$EC2_HOST:8000/health"
    echo "  - Admin API: http://$EC2_HOST:8000/admin"
    echo "  - Swagger Docs: http://$EC2_HOST:8000/docs"
    echo "  - Ngrok Status: http://$EC2_HOST:4040"
    echo ""
    echo "Next steps:"
    echo "  1. Test the application endpoints"
    echo "  2. Verify Telegram webhook is working"
    echo "  3. Test admin API with your API key"
    echo ""
}

# Main deployment function
main() {
    print_status "Starting TinyVault deployment to EC2..."
    echo ""
    
    # Check environment variables
    check_env_vars
    print_status "Environment variables validated"
    
    # Setup SSH
    setup_ssh
    
    # Deploy with Ansible
    deploy_with_ansible
    
    # Verify deployment
    verify_deployment
    
    # Show deployment information
    show_deployment_info
    
    # Cleanup
    cleanup_ssh
    
    print_status "Deployment completed successfully! 🎉"
}

# Trap to ensure cleanup on exit
trap cleanup_ssh EXIT

# Run main function
main "$@" 