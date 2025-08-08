# Synapse AI - Complete Full-Stack Application

A sophisticated SaaS application for AI-powered prompt optimization and generation, featuring a React/TypeScript frontend and FastAPI backend with comprehensive authentication, billing, and LLM integration.

## 🚀 Features

### Core Functionality
- **Synapse Core Prompt Builder**: Advanced prompt generation system with dynamic enhancement levels
- **Hybrid Optimization**: Cloud API (default) or local Ollama for prompt optimization
- **LLM Routing Engine**: Tiered model selection (Low/Med/High/Pro) with task-type optimization
- **Execution Engine**: OpenAI, Anthropic, and Ollama API integration with streaming responses
- **No Setup Required**: Works out-of-the-box with cloud APIs, optional local Ollama for advanced users

### User Management
- **JWT Authentication**: Secure user registration and login
- **API Key Management**: Generate and manage API keys for programmatic access
- **Credit System**: Usage-based billing with credit tracking
- **Subscription Management**: Multiple subscription tiers with Stripe integration

### Technical Features
- **Real-time Streaming**: Live streaming responses from LLM APIs
- **Caching System**: In-memory caching for improved performance
- **Database Persistence**: Complete data persistence with SQLAlchemy
- **Responsive UI**: Modern React/Tailwind CSS interface

## 🏗️ Architecture

### Backend (FastAPI)
- **Authentication**: JWT-based with password hashing
- **Database**: SQLAlchemy with SQLite (dev) / PostgreSQL (prod)
- **LLM Integration**: OpenAI, Anthropic, Ollama APIs
- **Billing**: Stripe integration for subscriptions and payments
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

### Frontend (React/TypeScript)
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS with responsive design
- **Routing**: React Router for SPA navigation
- **State Management**: React hooks and context
- **Build Tool**: Vite for fast development and building

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.12+
- Node.js 18+
- Poetry (Python package manager)
- npm/yarn/pnpm

### Backend Setup
```bash
cd backend
poetry install
cp .env.example .env
# Edit .env with your API keys
poetry run fastapi dev app/main.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables
Copy `backend/.env.example` to `backend/.env` and configure:
- `JWT_SECRET_KEY`: Secret key for JWT tokens
- `DATABASE_URL`: Database connection string
- `OPENAI_API_KEY`: OpenAI API key (required for cloud optimization)
- `ANTHROPIC_API_KEY`: Anthropic API key (optional)
- `STRIPE_SECRET_KEY`: Stripe secret key (optional)
- `USE_LOCAL_OLLAMA`: Set to "true" for local Ollama, "false" for cloud API (default: false)

### 🔄 Hybrid Optimization Modes

**Cloud API Mode (Default - No Setup Required)**
- Uses `gpt-4o-mini` for prompt optimization (~$0.0006/request)
- No local installation required
- Reliable 99.9% uptime
- Automatic scaling
- Set `USE_LOCAL_OLLAMA=false` (default)

**Local Ollama Mode (Advanced Users)**
- Uses local `phi3:mini` model for privacy and speed
- Requires Ollama installation and model download
- Zero per-request costs after setup
- Complete data privacy
- Set `USE_LOCAL_OLLAMA=true`

**Setup Local Ollama (Optional):**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the phi3:mini model
ollama pull phi3:mini

# Verify it's running
curl http://localhost:11434/api/version
```

## 📚 API Documentation

Once the backend is running, visit:
- API Documentation: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

## 🔧 Development

### Key Endpoints
- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication
- `POST /optimize` - Generate optimized prompts
- `POST /execute` - Execute prompts with LLMs
- `GET /users/me` - Get current user info
- `POST /stripe/create-checkout` - Create payment session

### Database Models
- **Users**: Authentication and profile data
- **Prompts**: User prompts and optimizations
- **Responses**: LLM responses and metadata
- **ApiKeys**: User API key management
- **Billing**: Subscription and payment records

## 🚀 Deployment

### Backend (Fly.io)
```bash
cd backend
fly deploy
```

### Frontend (Vercel)
```bash
cd frontend
npm run build
# Deploy to Vercel
```

## 📝 License

This project is proprietary software developed for Synapse AI.

## 🤝 Contributing

This is a private repository. For development guidelines and contribution instructions, please contact the development team.

---

**Link to Devin run**: https://app.devin.ai/sessions/d686cb7555c54e34a4bfd7f830e578a9
**Requested by**: Sharon Miller (smillerny@yahoo.com)
