# MAI Framework V2

A self-hosted AI assistant framework optimized for Apple Silicon, featuring local LLM inference via MLX with a modern web interface.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            MAC STUDIO HOST                                   │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     DOCKER COMPOSE STACK                                │ │
│  │                                                                         │ │
│  │  ┌─────────────┐                                                        │ │
│  │  │   Caddy     │ :80/:443                                               │ │
│  │  │  (Reverse   │◄──── HTTPS/HTTP3 ────► Internet / Tailscale           │ │
│  │  │   Proxy)    │                                                        │ │
│  │  └──────┬──────┘                                                        │ │
│  │         │                                                               │ │
│  │         ├─── /* ──────────►┌──────────────┐                             │ │
│  │         │                  │ mai-frontend │ React + Vite                │ │
│  │         │                  │  (nginx:80)  │                             │ │
│  │         │                  └──────────────┘                             │ │
│  │         │                                                               │ │
│  │         └─── /api/* ──────►┌──────────────┐                             │ │
│  │                            │ mai-backend  │ FastAPI                     │ │
│  │                            │   (:8000)    │                             │ │
│  │                            └──────┬───────┘                             │ │
│  │                                   │                                     │ │
│  │         ┌─────────────────────────┼─────────────────────────┐           │ │
│  │         │                         │                         │           │ │
│  │         ▼                         ▼                         ▼           │ │
│  │  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐      │ │
│  │  │ PostgreSQL  │          │    Redis    │          │   Qdrant    │      │ │
│  │  │ + pgvector  │          │   (Cache)   │          │  (Vectors)  │      │ │
│  │  │   (:5432)   │          │   (:6379)   │          │   (:6333)   │      │ │
│  │  └─────────────┘          └─────────────┘          └─────────────┘      │ │
│  │                                                                         │ │
│  └─────────────────────────────────┬───────────────────────────────────────┘ │
│                                    │                                         │
│                                    │ host.docker.internal                    │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    BARE METAL (Native macOS)                            │ │
│  │                                                                         │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │ │
│  │  │                    MLX Intelligence Engine                        │  │ │
│  │  │                         (:8081)                                   │  │ │
│  │  │                                                                   │  │ │
│  │  │   ┌─────────────────┐    ┌─────────────────────────────────┐     │  │ │
│  │  │   │  FastAPI Proxy  │───►│      mlx_lm.server (:8082)      │     │  │ │
│  │  │   │  + Hot-Swap API │    │  GPU/Neural Engine via Metal    │     │  │ │
│  │  │   └─────────────────┘    └─────────────────────────────────┘     │  │ │
│  │  │                                                                   │  │ │
│  │  │   Features:                                                       │  │ │
│  │  │   • OpenAI-compatible API                                         │  │ │
│  │  │   • Hot-swap model loading                                        │  │ │
│  │  │   • Unified memory access                                         │  │ │
│  │  │   • Metal GPU acceleration                                        │  │ │
│  │  └──────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Features

- **Local LLM Inference**: Run large language models locally using Apple's MLX framework
- **Hot-Swap Models**: Switch between models without restarting the server
- **OpenAI-Compatible API**: Drop-in replacement for OpenAI API calls
- **Modern Web UI**: React-based frontend with real-time streaming
- **Vector Search**: Qdrant for semantic search and RAG capabilities
- **Persistent Storage**: PostgreSQL with pgvector extension
- **Caching**: Redis for session and response caching
- **Secure Access**: Caddy reverse proxy with automatic HTTPS
- **Remote Access**: Optional Tailscale integration for secure remote access

## Requirements

- macOS with Apple Silicon (M1/M2/M3/M4)
- Docker Desktop for Mac
- Python 3.11+
- 32GB+ RAM recommended for larger models

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/travelinman1013/MAI-v2.git
cd MAI-v2
```

### 2. Configure Environment

```bash
# Copy and edit environment files
cp .env.docker.example .env.docker
cp .env.host.example .env.host

# Edit with your settings
vim .env.docker
vim .env.host
```

### 3. Set Up Host Engine (MLX)

```bash
# Create virtual environment for MLX
cd host_engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
```

### 4. Start the Stack

```bash
# Make start script executable
chmod +x start-mai.sh

# Start everything
./start-mai.sh
```

### 5. Verify Installation

```bash
# Check health
curl http://localhost/health

# Test chat
curl http://localhost/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}], "max_tokens": 50}'
```

## Project Structure

```
mai-v2/
├── docker-compose.yml      # Docker orchestration
├── Dockerfile              # Backend container
├── Caddyfile               # Reverse proxy config
├── start-mai.sh            # Startup script
├── requirements.txt        # Python dependencies
├── .env.docker             # Docker environment
├── .env.host               # Host environment
│
├── src/                    # Backend application
│   ├── main.py             # FastAPI entrypoint
│   ├── core/
│   │   └── utils/
│   │       ├── config.py   # Configuration management
│   │       └── logging.py  # Logging setup
│   └── infrastructure/
│       └── llm/
│           └── mlxlm_client.py  # MLX client
│
├── frontend/               # React application
│   ├── Dockerfile          # Frontend container
│   ├── nginx.conf          # Nginx config
│   ├── vite.config.ts      # Vite build config
│   ├── package.json        # Dependencies
│   └── src/
│       ├── App.tsx         # Main component
│       └── services/
│           └── api.ts      # API client
│
└── host_engine/            # MLX server (runs on host)
    ├── server.py           # FastAPI + MLX wrapper
    ├── config.py           # Engine configuration
    └── requirements.txt    # MLX dependencies
```

## API Endpoints

### Health & Status

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Basic health check |
| `/health/detailed` | GET | Detailed service status |

### Chat API (OpenAI-Compatible)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/chat/completions` | POST | Chat completion |
| `/api/v1/models` | GET | List available models |

### Model Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/agents/llm-status` | GET | Current LLM status |
| `http://localhost:8081/load` | POST | Hot-swap model |
| `http://localhost:8081/models/available` | GET | List local models |

## Configuration

### Environment Variables

#### Docker (.env.docker)

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | Database user | `mai` |
| `POSTGRES_PASSWORD` | Database password | `mai_secret` |
| `POSTGRES_DB` | Database name | `mai_framework` |
| `MLXLM__BASE_URL` | MLX server URL | `http://host.docker.internal:8081/v1` |

#### Host (.env.host)

| Variable | Description | Default |
|----------|-------------|---------|
| `MLX_PORT` | External server port | `8081` |
| `MLX_DEFAULT_MODEL` | Default model to load | `mlx-community/Qwen2.5-7B-Instruct-4bit` |
| `MLX_MODEL_DIRECTORY` | Path to models | `/path/to/models` |
| `MLX_MAX_TOKENS` | Maximum context | `32768` |

## Troubleshooting

### Check Service Status

```bash
# Docker services
docker compose ps
docker compose logs mai-backend

# MLX server
curl http://localhost:8081/status
tail -f logs/mlx-server.log
```

### Common Issues

**MLX server won't start**
- Ensure you're running on Apple Silicon
- Check that mlx-lm is installed in the host venv
- Verify the model path exists

**Backend can't connect to MLX**
- Verify `host.docker.internal` is resolving
- Check MLX server is running on port 8081
- Test: `docker compose exec mai-backend curl http://host.docker.internal:8081/v1/models`

**Database connection errors**
- Wait for PostgreSQL healthcheck to pass
- Check credentials in .env.docker

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
