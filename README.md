# Vortex Python Demo App

A demo FastAPI application showcasing the Vortex Python SDK integration. This demo mirrors the functionality of the Express and Fastify demos but uses Python/FastAPI.

## Features

- **Authentication System**: Demo login/logout with JWT sessions
- **Vortex Integration**: Complete API routes matching Express/Fastify demos
- **Identical Frontend**: Same React-based UI as other demos
- **FastAPI Framework**: Modern Python web framework with automatic API docs

## Prerequisites

- **Python 3.8+** (check with `python --version`)
- **pip** (Python package installer)

## Quick Start

### 1. Install Python Dependencies

From the demo-python directory:

```bash
cd apps/demo-python

# Create virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install Vortex Python SDK

The demo uses the local Vortex Python SDK. Install it in development mode:

```bash
# From the demo-python directory
pip install -e ../../packages/vortex-python-sdk
```

### 3. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file if needed (optional for demo)
# VORTEX_API_KEY=your-api-key-here
# PORT=8000
```

### 4. Run the Server

```bash
# Start the development server
python src/server.py
```

The server will start on http://localhost:8000

**🎯 Quick Test**: After starting, visit http://localhost:8000/docs to see the interactive API documentation with all working routes!

> **Note**: This demo uses SHA256 hashing and simplified JWT for Python 3.13 compatibility. Perfect for demo purposes and development.

## Usage

### Access the Demo

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (FastAPI auto-generated docs)
- **Health Check**: http://localhost:8000/health

### Demo Users

The demo includes pre-configured users:

- **Admin**: `admin@example.com` / `password123`
  - Role: admin
  - Groups: Engineering team, Acme Corp organization

- **User**: `user@example.com` / `userpass`
  - Role: user
  - Groups: Engineering team

### Available API Routes

#### Authentication Routes
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user info

#### Demo Routes
- `GET /api/demo/users` - Get demo users list
- `GET /api/demo/protected` - Protected route (requires login)

#### Vortex Routes
- `POST /api/vortex/jwt` - Generate Vortex JWT
- `GET /api/vortex/invitations/by-target` - Get invitations by target
- `GET /api/vortex/invitations/{id}` - Get specific invitation
- `POST /api/vortex/invitations/accept` - Accept invitations
- `DELETE /api/vortex/invitations/{id}` - Revoke invitation
- `GET /api/vortex/invitations/by-group/{type}/{id}` - Get group invitations
- `DELETE /api/vortex/invitations/by-group/{type}/{id}` - Delete group invitations
- `POST /api/vortex/invitations/{id}/reinvite` - Reinvite

## Development

### Project Structure

```
apps/demo-python/
├── src/
│   ├── server.py          # Main FastAPI application
│   ├── auth.py            # Demo authentication system
│   └── __init__.py        # Python package marker
├── public/
│   └── index.html         # Frontend (identical to Express demo)
├── requirements.txt       # Python dependencies
├── pyproject.toml        # Python project configuration
├── .env.example          # Environment template
└── README.md            # This file
```

### Key Features

#### FastAPI Integration
- Modern Python web framework with automatic API documentation
- Pydantic models for request/response validation
- Dependency injection for authentication
- Exception handling with proper HTTP status codes

#### Vortex SDK Integration
- Direct import and usage of the Vortex Python SDK
- Both sync and async methods available (demo uses sync for simplicity)
- Proper error handling with VortexApiError exceptions
- JWT generation and invitation management

#### Authentication System
- Bcrypt password hashing
- JWT session tokens in HTTP-only cookies
- Dependency injection for protected routes
- Demo users with different roles and groups

### Running in Production Mode

```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn src.server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Environment Variables

- `VORTEX_API_KEY` - Your Vortex API key (default: "demo-api-key")
- `PORT` - Server port (default: 8000)
- `JWT_SECRET` - JWT signing secret (default: "demo-secret-key")

## Testing the Demo

1. **Start the server** following the Quick Start guide
2. **Open http://localhost:8000** in your browser
3. **Log in** using one of the demo users
4. **Test Vortex features** using the web interface
5. **Check API docs** at http://localhost:8000/docs for interactive testing

## API Compatibility

This demo provides **identical API compatibility** with the Express and Fastify demos:

- Same route paths and HTTP methods
- Same request/response formats
- Same authentication flow
- Same frontend interface

The only differences are:
- Python/FastAPI server implementation
- FastAPI automatic API documentation
- Pydantic validation instead of TypeScript types

## Troubleshooting

### Common Issues

1. **Python version issues**:
   - **Too old**: Ensure Python 3.8+
   - **Python 3.13**: Fully supported with simplified dependencies

2. **Module not found errors**:
   - Make sure virtual environment is activated: `source venv/bin/activate`
   - Install dependencies: `pip install -r requirements.txt`

3. **Port already in use**: Change PORT in .env or kill the process using the port

4. **Vortex SDK import error**: Ensure the SDK is installed with `pip install -e ../../packages/vortex-python-sdk`

5. **API returns demo data**: This is normal! Configure VORTEX_API_KEY environment variable for real API data

### Debug Mode

The server runs in debug mode by default with auto-reload. Check the console output for detailed error messages.

### Logs

FastAPI provides detailed request/response logging. Check the console where you started the server for debugging information.

## Next Steps

- **Custom Integration**: Use this demo as a template for your FastAPI applications
- **Database Integration**: Replace demo users with real database models
- **Production Setup**: Configure proper environment variables and security settings
- **Testing**: Add pytest tests following the patterns in the Vortex SDK