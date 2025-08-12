# GitHub Secrets Configuration for TinyVault Deployment

This document outlines the required GitHub secrets for automated deployment of TinyVault to EC2.

## Required Secrets

### Infrastructure Secrets
- **`EC2_HOST`** - The public IP address or hostname of your EC2 instance
  - Example: `23.20.100.106`
  - Required: Yes

- **`SSH_PRIVATE_KEY`** - The private SSH key for connecting to your EC2 instance
  - This should be the content of your `.pem` file (e.g., `aws_keys.pem`)
  - Required: Yes
  - Format: Include the full private key including headers
    ```
    -----BEGIN RSA PRIVATE KEY-----
    [your private key content]
    -----END RSA PRIVATE KEY-----
    ```

### Application Secrets
- **`TELEGRAM_BOT_TOKEN`** - Your Telegram bot token from BotFather
  - Example: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
  - Required: Yes

- **`ADMIN_API_KEY`** - API key for administrative access
  - Generate a secure random string
  - Required: Yes

- **`WEBHOOK_SECRET`** - Secret for webhook security
  - Generate a secure random string
  - Required: Yes

### Optional Secrets
- **`DB_URL`** - Database connection URL
  - Default: `sqlite+aiosqlite:///./data/tinyvault.db`
  - Required: No (uses SQLite by default)

- **`DEBUG`** - Enable debug mode
  - Default: `false`
  - Required: No

- **`APP_NAME`** - Application name
  - Default: `TinyVault`
  - Required: No

## How to Set GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with the exact name listed above
5. Save each secret

## Security Considerations

- Never commit secrets directly to your repository
- Use strong, randomly generated values for API keys and webhook secrets
- Rotate secrets regularly
- Ensure your EC2 instance security group only allows SSH access from trusted IPs

## Testing the Deployment

After setting up the secrets:

1. Push to the `main` branch or manually trigger the workflow
2. Monitor the Actions tab for deployment progress
3. Check that the application is accessible at `http://[EC2_HOST]:8000`

## Troubleshooting

- **SSH Connection Failed**: Check that `EC2_HOST` and `SSH_PRIVATE_KEY` are correct
- **Deployment Failed**: Check the Actions logs for specific error messages
- **Application Not Accessible**: Verify EC2 security groups allow HTTP traffic on port 8000 