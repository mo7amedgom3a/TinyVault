# TinyVault

A service for storing and retrieving short notes and links via Telegram bot with admin API access.

## Features

- **Telegram Bot Integration**: Save URLs and notes with unique short codes
- **Admin REST API**: Monitor users and manage items
- **SQLite Database**: Lightweight, file-based storage
- **Docker Support**: Easy deployment with docker-compose
- **Layered Architecture**: Clean, modular design with services and repositories

## System Architecture

The TinyVault system follows a modern microservices architecture with clear separation of concerns:

![System Architecture](images/architecture.png)

**Key Components:**
- **User Interface**: Telegram Bot for end-user interactions
- **Backend Service**: FastAPI-based REST API handling business logic
- **Database Layer**: SQLite database with SQLAlchemy ORM
- **Admin Interface**: REST API for administrative operations
- **Webhook System**: Real-time Telegram update processing

## Database Design

The database uses a normalized schema with proper foreign key relationships:

![Database Schema](images/erd.png)

**Table Relationships:**
- **Users** table stores Telegram user information
- **Items** table contains user-generated content (URLs/notes)
- One-to-many relationship: One user can have multiple items
- Soft delete support with `deleted_at` timestamp

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Telegram Bot Token

### 1. Clone and Setup

```bash
git clone <repository-url>
cd TinyVault

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env with your values
TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_API_KEY=your_secure_api_key
WEBHOOK_SECRET=optional_webhook_secret
```

### 3. Run with Docker

```bash
# Start the application
docker-compose up -d

# Check logs
docker-compose logs -f app

# View running containers
docker-compose ps
```

### 4. Run Locally

```bash
# Create data directory
mkdir -p data logs

# Initialize database (SQLite will be created automatically)
python -m app.main

# Or run with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Telegram Webhook
- `POST /telegram/webhook` - Handle Telegram bot updates

### Admin API (requires `X-API-Key` header)
- `GET /admin/users` - List all users with item counts
- `GET /admin/items?user_id=X` - Get items for specific user
- `DELETE /admin/items/{short_code}` - Delete any item

### Public
- `GET /` - API information
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)

## Telegram Bot Commands

- `/start` - Welcome message and help
- `/help` - Show available commands
- `/list` - Show your 5 most recent items
- `/get <code>` - Retrieve item by short code
- `/del <code>` - Delete item by short code

## Database Schema

### Users Table
- `id` - Primary key (auto-increment)
- `telegram_user_id` - Unique Telegram user ID (BIGINT)
- `first_seen_at` - First interaction timestamp
- `last_seen_at` - Last interaction timestamp (auto-updated)

### Items Table
- `id` - Primary key (auto-increment)
- `owner_user_id` - Foreign key to users table
- `short_code` - Unique short code for retrieval
- `kind` - Either 'url' or 'note'
- `content` - The actual URL or note content
- `created_at` - Creation timestamp
- `deleted_at` - Soft delete timestamp (nullable)

### Indexes and Constraints
- Unique constraint on `users.telegram_user_id`
- Unique constraint on `items.short_code`
- Foreign key constraint: `items.owner_user_id` → `users.id`
- Automatic trigger to update `last_seen_at` on user updates

## Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DB_URL` | Database connection string | Yes | SQLite path |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | Yes | - |
| `ADMIN_API_KEY` | Secret key for admin API | Yes | - |
| `WEBHOOK_SECRET` | Webhook verification secret | No | - |
| `DEBUG` | Enable debug mode | No | false |

## Development

### Project Structure

```
app/
├── api/           # API endpoints and dependencies
│   ├── admin.py   # Admin API endpoints
│   ├── telegram.py # Telegram webhook handler
│   └── deps.py    # Dependency injection
├── services/      # Business logic layer
│   ├── item_service.py    # Item management logic
│   └── user_service.py    # User management logic
├── models.py      # SQLAlchemy ORM models
├── schemas.py     # Pydantic validation schemas
├── database.py    # Database configuration
├── config.py      # Application settings
└── main.py        # FastAPI application
```

### Key Features

1. **Idempotency**: Prevents duplicate processing of Telegram updates
2. **Short Code Uniqueness**: Generates unique codes with conflict resolution
3. **URL Validation**: Automatically detects and validates URLs
4. **Soft Deletes**: Items are marked as deleted rather than removed
5. **Async Operations**: Full async/await support throughout
6. **Security**: Non-root Docker containers with proper user permissions

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_item_service.py
```

## Deployment

### Docker

```bash
# Build and run
docker-compose up --build

# Production build
docker build -t tinyvault .
docker run -p 8000:8000 --env-file .env tinyvault

# View container logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Environment Variables

Ensure all required environment variables are set in production:
- `TELEGRAM_BOT_TOKEN`
- `ADMIN_API_KEY`
- `DB_URL` (for production databases)
- `WEBHOOK_SECRET` (recommended for production)

## Webhook Setup

1. Set your bot's webhook URL:
   ```
   https://api.telegram.org/bot<BOT_TOKEN>/setWebhook?url=https://yourdomain.com/telegram/webhook
   ```

2. If using `WEBHOOK_SECRET`, include it in the webhook URL:
   ```
   https://yourdomain.com/telegram/webhook?secret=<WEBHOOK_SECRET>
   ```

## Troubleshooting

### Common Issues

1. **Database Connection**: Ensure data directory exists and is writable
2. **Telegram Webhook**: Verify bot token and webhook URL
3. **Admin API**: Check `X-API-Key` header is set correctly
4. **Port Conflicts**: Ensure port 8000 is available
5. **Docker Issues**: Check container logs with `docker-compose logs`

### Logs

```bash
# Docker logs
docker-compose logs app

# Local logs
tail -f logs/app.log

# View all container status
docker-compose ps
```

### Health Checks

The application includes built-in health checks:
- **Docker Health Check**: Monitors container health every 30 seconds
- **API Health Endpoint**: `/health` endpoint for external monitoring
- **Database Connectivity**: Automatic database connection validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License. 