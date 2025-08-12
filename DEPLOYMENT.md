# TinyVault Deployment Guide

This guide explains how to deploy TinyVault to an EC2 instance using the simplified setup.

## Prerequisites

- EC2 instance running Ubuntu
- SSH access to the EC2 instance
- GitHub repository with your TinyVault code

## Simplified Deployment

The deployment process has been simplified to focus on the essentials:

1. **Install Docker** on the EC2 instance
2. **Clone the repository** from GitHub
3. **Build and run** the Docker container
4. **Configure environment** variables

## GitHub Secrets Setup

Set these secrets in your GitHub repository:

| Secret Name | Description |
|-------------|-------------|
| `EC2_HOST` | Your EC2 instance public IP or domain |
| `SSH_PRIVATE_KEY` | Your EC2 SSH private key content |
| `DB_URL` | Database connection string |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token |
| `ADMIN_API_KEY` | Your admin API key |
| `WEBHOOK_SECRET` | Your webhook secret |

## Automatic Deployment

1. Push to `main` or `master` branch
2. GitHub Actions will automatically:
   - Connect to your EC2 instance
   - Install Docker if needed
   - Clone your repository
   - Build and run the container
   - Wait for the application to be healthy

## Manual Deployment

1. Set environment variables:
   ```bash
   export EC2_HOST="your-ec2-ip"
   export SSH_PRIVATE_KEY="your-private-key-content"
   export DB_URL="your-database-url"
   export TELEGRAM_BOT_TOKEN="your-bot-token"
   export ADMIN_API_KEY="your-admin-key"
   export WEBHOOK_SECRET="your-webhook-secret"
   ```

2. Run the deployment script:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

## What Gets Deployed

- **Application**: TinyVault FastAPI application
- **Database**: SQLite database (or your configured database)
- **Ports**: Application runs on port 8000
- **Volumes**: Data and logs are persisted in Docker volumes

## Post-Deployment

After successful deployment:

- Application: `http://your-ec2-ip:8000`
- Health Check: `http://your-ec2-ip:8000/health`
- Admin API: `http://your-ec2-ip:8000/admin`
- Swagger Docs: `http://your-ec2-ip:8000/docs`

## Notes

- **Ngrok**: Already configured on your server, no additional setup needed
- **User Management**: No custom users created, runs as root (for testing)
- **Security**: For production, consider creating a dedicated user and proper security measures
- **Database**: Uses SQLite by default, can be configured for other databases

## Troubleshooting

### Common Issues

1. **SSH Connection Failed**
   - Verify EC2_HOST is correct
   - Check SSH_PRIVATE_KEY content
   - Ensure security group allows SSH (port 22)

2. **Docker Build Failed**
   - Check requirements.txt
   - Verify Dockerfile syntax
   - Check available disk space

3. **Application Not Starting**
   - Check container logs: `docker logs tinyvault-app`
   - Verify environment variables
   - Check port 8000 is not in use

### Logs

- **Application logs**: `docker logs tinyvault-app`
- **Container status**: `docker ps`
- **System logs**: `journalctl -u docker`

## Testing

Run the test script to verify your setup:

```bash
chmod +x test_deployment.sh
./test_deployment.sh
```

This will check all required files and configurations without deploying. 