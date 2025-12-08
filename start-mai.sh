#!/usr/bin/env bash
# MAI Framework V2 - Master Start Script
# Bridges Docker services with bare-metal MLX engine

set -o errexit
set -o nounset
set -o pipefail

# ============================================
# CONFIGURATION
# ============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/host_engine/.venv"
MLX_PORT="${MLX_PORT:-8081}"
MLX_HOST="${MLX_HOST:-0.0.0.0}"
MLX_MODEL="${MLX_MODEL:-mlx-community/Qwen2.5-7B-Instruct-4bit}"
MLX_MAX_TOKENS="${MLX_MAX_TOKENS:-32768}"
LOG_DIR="${SCRIPT_DIR}/logs"
MLX_LOG="${LOG_DIR}/mlx-server.log"
DOCKER_LOG="${LOG_DIR}/docker.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# HELPER FUNCTIONS
# ============================================
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

cleanup() {
    print_info "Shutting down MAI Framework..."

    # Kill MLX server if running
    if [[ -n "${MLX_PID:-}" ]]; then
        print_info "Stopping MLX server (PID: $MLX_PID)..."
        kill "$MLX_PID" 2>/dev/null || true
        wait "$MLX_PID" 2>/dev/null || true
    fi

    # Stop Docker services
    print_info "Stopping Docker services..."
    docker compose down

    print_success "MAI Framework stopped."
}

trap cleanup EXIT INT TERM

# ============================================
# PRE-FLIGHT CHECKS
# ============================================
preflight_checks() {
    print_info "Running pre-flight checks..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker Desktop for Mac."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker Desktop."
        exit 1
    fi

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed."
        exit 1
    fi

    # Check Tailscale (optional warning)
    if command -v tailscale &> /dev/null; then
        backend_state=$(tailscale status --json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('BackendState','Unknown'))" 2>/dev/null || echo "Unknown")

        if [[ "$backend_state" == "Running" ]]; then
            tailscale_ip=$(tailscale ip -4 2>/dev/null || echo "unknown")
            print_success "Tailscale is running (IP: $tailscale_ip)"
        else
            print_warning "Tailscale is not running. Remote access will not be available."
            print_warning "Start Tailscale for iPhone access: open /Applications/Tailscale.app"
        fi
    else
        print_warning "Tailscale is not installed. Remote access will not be available."
    fi

    print_success "Pre-flight checks passed."
}

# ============================================
# SETUP MLX VIRTUAL ENVIRONMENT
# ============================================
setup_mlx_venv() {
    print_info "Setting up MLX virtual environment..."

    # Create host_engine directory if it doesn't exist
    mkdir -p "${SCRIPT_DIR}/host_engine"

    # Create venv if it doesn't exist
    if [[ ! -d "$VENV_DIR" ]]; then
        print_info "Creating virtual environment at $VENV_DIR..."
        python3 -m venv "$VENV_DIR"
    fi

    # Activate venv
    source "${VENV_DIR}/bin/activate"

    # Install/upgrade dependencies
    print_info "Installing MLX dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet --upgrade \
        mlx-lm==0.28.4 \
        fastapi \
        uvicorn \
        httpx

    print_success "MLX virtual environment ready."
}

# ============================================
# START MLX SERVER
# ============================================
start_mlx_server() {
    print_info "Starting MLX-LM server..."
    print_info "  Model: $MLX_MODEL"
    print_info "  Host: $MLX_HOST"
    print_info "  Port: $MLX_PORT"
    print_info "  Max Tokens: $MLX_MAX_TOKENS"

    # Ensure log directory exists
    mkdir -p "$LOG_DIR"

    # Check if port is already in use
    if lsof -Pi ":$MLX_PORT" -sTCP:LISTEN -t &> /dev/null; then
        print_warning "Port $MLX_PORT is already in use. Attempting to stop existing process..."
        lsof -Pi ":$MLX_PORT" -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
        sleep 2
    fi

    # Start MLX server in background
    source "${VENV_DIR}/bin/activate"

    mlx_lm.server \
        --model "$MLX_MODEL" \
        --host "$MLX_HOST" \
        --port "$MLX_PORT" \
        --max-tokens "$MLX_MAX_TOKENS" \
        --log-level INFO \
        > "$MLX_LOG" 2>&1 &

    MLX_PID=$!

    # Wait for server to be ready (allow time for model download on first run)
    print_info "Waiting for MLX server to be ready (this may take a few minutes on first run)..."
    local retries=120
    while [[ $retries -gt 0 ]]; do
        if curl -s "http://localhost:${MLX_PORT}/v1/models" &> /dev/null; then
            print_success "MLX server is ready (PID: $MLX_PID)"
            return 0
        fi
        sleep 3
        ((retries--))
    done

    print_error "MLX server failed to start. Check logs at $MLX_LOG"
    exit 1
}

# ============================================
# START DOCKER SERVICES
# ============================================
start_docker_services() {
    print_info "Starting Docker services..."

    # Ensure log directory exists
    mkdir -p "$LOG_DIR"

    # Build and start services
    docker compose build --quiet
    docker compose up -d

    # Wait for services to be healthy
    print_info "Waiting for Docker services to be healthy..."
    local retries=60
    while [[ $retries -gt 0 ]]; do
        local healthy=$(docker compose ps --format json 2>/dev/null | python3 -c "
import sys, json
services = [json.loads(line) for line in sys.stdin if line.strip()]
healthy = all(s.get('Health', 'healthy') == 'healthy' or s.get('State') == 'running' for s in services)
print('true' if healthy and services else 'false')
" 2>/dev/null || echo "false")

        if [[ "$healthy" == "true" ]]; then
            print_success "All Docker services are healthy"
            return 0
        fi
        sleep 2
        ((retries--))
    done

    print_warning "Some services may not be fully healthy. Check with: docker compose ps"
}

# ============================================
# STREAM LOGS
# ============================================
stream_logs() {
    print_info "Streaming logs (Ctrl+C to stop)..."
    echo ""
    echo "================================================"
    echo "  MAI Framework V2 is running!"
    echo "================================================"
    echo ""
    echo "  Local access:    http://localhost"

    if command -v tailscale &> /dev/null; then
        tailscale_ip=$(tailscale ip -4 2>/dev/null || echo "")
        if [[ -n "$tailscale_ip" ]]; then
            echo "  Tailscale:       http://${tailscale_ip}"
        fi
    fi

    echo ""
    echo "  MLX Server:      http://localhost:${MLX_PORT}/v1"
    echo "  MLX Logs:        $MLX_LOG"
    echo ""
    echo "================================================"
    echo ""

    # Stream both Docker and MLX logs
    (
        # Docker logs in background
        docker compose logs -f &
        DOCKER_LOGS_PID=$!

        # MLX logs in background
        tail -f "$MLX_LOG" 2>/dev/null &
        MLX_LOGS_PID=$!

        # Wait for either to exit
        wait
    )
}

# ============================================
# MAIN
# ============================================
main() {
    echo ""
    echo "================================================"
    echo "  MAI Framework V2 - Mac Studio Hybrid Edition"
    echo "================================================"
    echo ""

    cd "$SCRIPT_DIR"

    preflight_checks
    setup_mlx_venv
    start_mlx_server
    start_docker_services
    stream_logs
}

main "$@"
