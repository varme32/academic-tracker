# Query Portal Backend API

This is the backend API for the Academic Tracker Query Portal built with FastAPI and SQLite3.

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── database.py          # Database configuration and session management
├── init_db.py          # Database initialization script
├── requirements.txt     # Python dependencies
├── start_server.bat    # Windows batch file to start server
├── models/
│   ├── __init__.py
│   ├── user.py         # User database model
│   └── query.py        # Query database model
├── schemas/
│   ├── __init__.py
│   ├── user.py         # Pydantic schemas for User API
│   └── query.py        # Pydantic schemas for Query API
└── endpoints/
    ├── __init__.py
    ├── auth.py         # Authentication endpoints
    └── query.py        # Query management endpoints
```

## Setup Instructions

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize the database:**
   ```bash
   python init_db.py
   ```

3. **Start the server:**
   ```bash
   python main.py
   ```
   
   Or use the batch file on Windows:
   ```bash
   start_server.bat
   ```

4. **The API will be available at:**
   - Main API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Authentication

- **POST /auth/signup** - Create a new user account
  - Body: `{full_name, email, password, confirm_password}`
  - Response: `{message, user}`

- **POST /auth/login** - User login
  - Body: `{email, password}`
  - Response: `{message, user}`

- **GET /auth/users** - Get all users with pagination
  - Query params: `skip` (default: 0), `limit` (default: 100)
  - Response: `{users: [...], total: number}`

- **GET /auth/users/{user_id}** - Get user by ID
  - Path param: `user_id` (integer)
  - Response: `{id, full_name, email, created_at}`

- **GET /auth/users/email/{email}** - Get user by email
  - Path param: `email` (string)
  - Response: `{id, full_name, email, created_at}`

### Queries

- **POST /queries/** - Create a new query
  - Query param: `user_id` (integer)
  - Body: `{category, subject, description, priority, attachment_filename?}`
  - Response: `{message, query}`

- **GET /queries/** - Get all queries with pagination and filters
  - Query params: `page`, `per_page`, `user_id?`, `category?`, `status?`, `priority?`
  - Response: `{queries: [...], total, page, per_page, total_pages}`

- **GET /queries/user/{user_id}** - Get queries for a specific user
  - Path param: `user_id` (integer)
  - Query params: `page`, `per_page`, `status?`
  - Response: `{queries: [...], total, page, per_page, total_pages}`

- **GET /queries/{query_id}** - Get query by ID
  - Path param: `query_id` (integer)
  - Response: `{id, user_id, category, subject, description, priority, status, ...}`

- **PUT /queries/{query_id}** - Update a query
  - Path param: `query_id` (integer)
  - Body: `{subject?, description?, priority?, status?, assigned_to?, resolution_notes?}`
  - Response: Updated query object

- **DELETE /queries/{query_id}** - Delete a query
  - Path param: `query_id` (integer)
  - Response: `{message}`

- **GET /queries/stats/overview** - Get query statistics
  - Response: `{total_queries, pending_queries, ..., by_category, by_priority}`

- **POST /queries/{query_id}/upload** - Upload attachment for a query
  - Path param: `query_id` (integer)
  - Body: File upload (multipart/form-data)
  - Response: `{message, filename, unique_filename}`

### General

- **GET /** - Root endpoint
- **GET /health** - Health check
- **GET /api/info** - API information and endpoints list

## Database

The application uses SQLite3 database with the following table:

### Users Table
- `id` (Integer, Primary Key)
- `full_name` (String)
- `email` (String, Unique)
- `password_hash` (String)
- `created_at` (DateTime)

### Queries Table
- `id` (Integer, Primary Key)
- `user_id` (Integer, Foreign Key to users.id)
- `category` (Enum: IT, Maintenance, Rector, Warden, Administration)
- `subject` (String)
- `description` (Text)
- `priority` (Enum: low, medium, high)
- `status` (Enum: pending, in_progress, resolved, closed)
- `attachment_filename` (String, Optional)
- `attachment_path` (String, Optional)
- `created_at` (DateTime)
- `updated_at` (DateTime)
- `resolved_at` (DateTime, Optional)
- `assigned_to` (String, Optional)
- `resolution_notes` (Text, Optional)

## Frontend Integration

The frontend uses the `auth.js` file to communicate with the backend API. Make sure the backend server is running before testing the frontend.

## Development

- The database file `query_portal.db` will be created automatically in the backend directory
- CORS is enabled for all origins (change this in production)
- Passwords are hashed using SHA256
- The API includes automatic validation using Pydantic schemas

## Deploying to Render

This project is ready to deploy to Render (https://render.com). The application entrypoint is `main:app`.

Recommended production start command (used in `Procfile` or Render service settings):

web: gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT

Notes:
Notes:
- This repository has been prepared for deployment to Render. All serverless-specific configuration and sample files have been removed from the `backend/` directory.
- Ensure `requirements.txt` includes `gunicorn` and `uvicorn` (add them if missing) so Render can install necessary dependencies.
