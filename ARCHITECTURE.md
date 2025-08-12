# TinyVault Architecture Documentation

## Overview

TinyVault follows a **Clean Architecture** pattern with clear separation of concerns across multiple layers. Each layer has a specific responsibility and communicates with other layers through well-defined interfaces.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                           │
│                    (FastAPI Endpoints)                     │
├─────────────────────────────────────────────────────────────┤
│                     Service Layer                          │
│                  (Business Logic)                          │
├─────────────────────────────────────────────────────────────┤
│                   Repository Layer                         │
│                 (Data Access Logic)                        │
├─────────────────────────────────────────────────────────────┤
│                      Data Layer                            │
│                (Database Management)                        │
├─────────────────────────────────────────────────────────────┤
│                     Model Layer                            │
│                  (SQLAlchemy Models)                       │
└─────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### 1. Model Layer (`app/models.py`)
- **Purpose**: Define database entities and their relationships
- **Responsibilities**:
  - SQLAlchemy ORM model definitions
  - Database schema representation
  - Entity relationships and constraints
- **Dependencies**: None (base layer)
- **Example**: `User`, `Item` models

### 2. Data Layer (`app/data/`)
- **Purpose**: Manage database connections and sessions
- **Responsibilities**:
  - Database session management
  - Connection pooling
  - Transaction handling
- **Dependencies**: Models, Database configuration
- **Components**:
  - `session_manager.py`: Database session management
  - `__init__.py`: Package exports

### 3. Repository Layer (`app/repositories/`)
- **Purpose**: Abstract data access operations
- **Responsibilities**:
  - CRUD operations for entities
  - Query building and execution
  - Data persistence logic
- **Dependencies**: Data layer, Models
- **Components**:
  - `base_repository.py`: Generic repository interface
  - `user_repository.py`: User-specific operations
  - `item_repository.py`: Item-specific operations

### 4. Service Layer (`app/services/`)
- **Purpose**: Implement business logic and orchestrate operations
- **Responsibilities**:
  - Business rule validation
  - Transaction coordination
  - Complex business operations
  - Integration with external services
- **Dependencies**: Repository layer
- **Components**:
  - `user_service.py`: User business logic
  - `item_service.py`: Item business logic
  - `telegram_service.py`: Telegram bot logic

### 5. API Layer (`app/api/`)
- **Purpose**: Handle HTTP requests and responses
- **Responsibilities**:
  - Request/response handling
  - Input validation
  - Authentication/authorization
  - Error handling
- **Dependencies**: Service layer
- **Components**:
  - `admin.py`: Admin API endpoints
  - `telegram.py`: Telegram webhook endpoints

## Dependency Injection

The application uses **constructor injection** to manage dependencies between layers. This ensures:

- **Loose coupling** between components
- **Easy testing** through mock injection
- **Clear dependency flow**
- **Maintainable code structure**

### Dependency Flow

```
API Layer → Service Layer → Repository Layer → Data Layer → Models
```

### Example: User Creation Flow

```python
# 1. API receives request
@router.post("/users")
async def create_user(
    user_service: UserService = Depends(get_user_service)  # ← DI
):
    return await user_service.create_user(...)

# 2. Service processes business logic
class UserService:
    def __init__(self, user_repository: UserRepository):  # ← Constructor injection
        self.user_repository = user_repository
    
    async def create_user(self, user_data):
        # Business logic here
        return await self.user_repository.create(user)

# 3. Repository handles data persistence
class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):  # ← Constructor injection
        self.session = session
    
    async def create(self, user: User):
        # Data access logic here
        self.session.add(user)
        await self.session.flush()
        return user
```

## Key Design Principles

### 1. Single Responsibility Principle
Each class has one reason to change:
- **Models**: Data structure and validation
- **Repositories**: Data access operations
- **Services**: Business logic
- **APIs**: HTTP handling

### 2. Dependency Inversion
High-level modules don't depend on low-level modules:
- Services depend on repository interfaces, not implementations
- APIs depend on service interfaces, not implementations

### 3. Interface Segregation
Clients only depend on methods they use:
- `BaseRepository` provides common CRUD operations
- Specific repositories extend with domain-specific methods

### 4. Open/Closed Principle
Open for extension, closed for modification:
- New repository types can extend `BaseRepository`
- New services can implement existing interfaces
- New API endpoints can use existing services

## File Structure

```
app/
├── __init__.py
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration settings
├── dependencies.py        # Dependency injection container
├── models.py              # SQLAlchemy models
├── schemas.py             # Pydantic schemas
├── database.py            # Database configuration
├── api/                   # API Layer
│   ├── __init__.py
│   ├── admin.py          # Admin API endpoints
│   └── telegram.py       # Telegram webhook endpoints
├── services/              # Service Layer
│   ├── __init__.py
│   ├── user_service.py   # User business logic
│   ├── item_service.py   # Item business logic
│   └── telegram_service.py # Telegram bot logic
├── repositories/          # Repository Layer
│   ├── __init__.py
│   ├── base_repository.py # Generic repository interface
│   ├── user_repository.py # User data access
│   └── item_repository.py # Item data access
└── data/                  # Data Layer
    ├── __init__.py
    └── session_manager.py # Database session management
```

## Benefits of This Architecture

### 1. **Maintainability**
- Clear separation of concerns
- Easy to locate and modify specific functionality
- Consistent patterns across the codebase

### 2. **Testability**
- Each layer can be tested independently
- Dependencies can be easily mocked
- Unit tests are focused and fast

### 3. **Scalability**
- New features can be added without affecting existing code
- Services can be easily extended or replaced
- Repository pattern allows for different data sources

### 4. **Flexibility**
- Easy to swap implementations (e.g., different databases)
- Business logic is independent of data access
- API changes don't affect business logic

## Testing Strategy

### Unit Testing
- **Models**: Test validation and relationships
- **Repositories**: Test data access operations
- **Services**: Test business logic with mocked repositories
- **APIs**: Test request/response handling with mocked services

### Integration Testing
- Test complete workflows across layers
- Verify database operations with test database
- Test API endpoints with real services

### Mocking Strategy
```python
# Example: Testing UserService with mocked repository
async def test_create_user():
    mock_repo = Mock(spec=UserRepository)
    mock_repo.create.return_value = User(id=1, telegram_user_id=123)
    
    service = UserService(mock_repo)
    result = await service.create_user(123)
    
    assert result.id == 1
    mock_repo.create.assert_called_once()
```

## Migration Strategy

When adding new features:

1. **Add Models** → Update `app/models.py`
2. **Create Repository** → Extend `BaseRepository`
3. **Implement Service** → Add business logic
4. **Create API Endpoints** → Handle HTTP requests
5. **Update Dependencies** → Wire up new components

## Performance Considerations

### 1. **Database Optimization**
- Use appropriate indexes
- Implement pagination for large datasets
- Consider query optimization

### 2. **Caching Strategy**
- Cache frequently accessed data
- Implement cache invalidation
- Use Redis for distributed caching

### 3. **Async Operations**
- All database operations are async
- Use connection pooling
- Implement proper error handling

## Security Considerations

### 1. **Authentication**
- Admin API key validation
- Webhook secret verification
- User permission checks

### 2. **Data Validation**
- Input sanitization
- SQL injection prevention
- XSS protection

### 3. **Error Handling**
- Don't expose internal errors
- Log security events
- Implement rate limiting

## Future Enhancements

### 1. **Event-Driven Architecture**
- Implement domain events
- Use message queues for async processing
- Add event sourcing capabilities

### 2. **Microservices**
- Split into separate services
- Implement service discovery
- Add API gateway

### 3. **Monitoring & Observability**
- Add metrics collection
- Implement distributed tracing
- Add health checks and alerts

## Conclusion

This layered architecture provides a solid foundation for the TinyVault application. It ensures:

- **Clean separation of concerns**
- **Easy testing and maintenance**
- **Scalable and flexible design**
- **Professional code quality**

The architecture follows industry best practices and can easily accommodate future enhancements while maintaining code quality and performance. 