#!/bin/bash

# ==============================================================================
# IngestIQ - Project Management Script
#
# A centralized CLI for managing the IngestIQ local development environment,
# running tests, and performing quality checks.
# ==============================================================================

set -euo pipefail

# --- Configuration & Colors ---
readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[0;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_RED='\033[0;31m'
readonly COLOR_RESET='\033[0m'

# --- Logging Functions ---
log() { echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} $1"; }
log_action() { echo -e "${COLOR_YELLOW}[ACTION]${COLOR_RESET} $1"; }
log_success() { echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_RESET} $1"; }
error() { echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1" >&2; }

# --- Helper Functions ---
clean_artifacts() {
    log_action "Purging Python artifacts and caches..."
    find . -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name "*.egg-info" \) -exec rm -rf {} +
    log_success "Project is clean."
}

clean_data() {
    log_action "Initiating full data and environment teardown..."
    echo -e "${COLOR_RED}WARNING:${COLOR_RESET} This will permanently delete all local database data (Postgres, Mongo, Chroma) and stop all services."
    read -p "Are you sure you want to proceed? (y/N): " final_confirm
    if [[ ! "$final_confirm" =~ ^[Yy]$ ]]; then
        error "Data cleanup cancelled by user."
        exit 1
    fi
    docker compose down --volumes
    log_success "All services stopped and data volumes removed."
}

run_checks() {
    log_action "Running quality checks inside the 'api' container..."
    log "Step 1: Checking code formatting with black..."
    if ! docker compose run --rm api black --check .; then
        error "Code formatting check failed. Run './run.sh format' to fix."
        exit 1
    fi
    log_success "Formatting is correct."

    log "Step 2: Running linting with ruff..."
    if ! docker compose run --rm api ruff check .; then
        error "Linting failed. Run './run.sh lint' to fix."
        exit 1
    fi
    log_success "Linting passed."

    log "Step 3: Running test suite with pytest..."
    if ! docker compose run --rm api pytest; then
        error "Tests failed."
        exit 1
    fi
    log_success "All tests passed."
}

# --- Main Logic ---
usage() {
    echo "Usage: $0 [COMMAND]"
    echo "Project utility script for IngestIQ."
    echo
    echo "Commands:"
    echo "  up            Build and start all services in detached mode (default)."
    echo "  down          Stop all running services."
    echo "  logs          Follow the logs of the api and airflow-worker services."
    echo "  test          Run the full quality suite (format check, linting, pytest)."
    echo "  format        Auto-format code using black."
    echo "  lint          Auto-lint and fix code using ruff."
    echo "  clean         Remove Python build artifacts and caches."
    echo "  clean-data    DANGER: Stop all services and delete all local database data."
    echo "  help          Display this help message."
    echo
}

main() {
    local command="${1:-up}"
    shift || true

    case "$command" in
    up)
        log_action "Building and starting all IngestIQ services..."
        docker compose up --build -d
        log_success "All services are starting. Use './run.sh logs' to monitor."
        ;;

    down)
        log_action "Stopping all IngestIQ services..."
        docker compose down
        log_success "Services stopped."
        ;;

    logs)
        log_action "Following logs for 'api' and 'airflow-worker'. Press Ctrl+C to exit."
        docker compose logs -f api airflow-worker
        ;;

    test)
        run_checks
        ;;

    format)
        log_action "Auto-formatting code with black..."
        docker compose run --rm api black .
        log_success "Formatting complete."
        ;;

    lint)
        log_action "Auto-linting and fixing code with ruff..."
        docker compose run --rm api ruff check . --fix
        log_success "Linting complete."
        ;;

    clean)
        clean_artifacts
        ;;

    clean-data)
        clean_data
        ;;

    help|--help|-h)
        usage
        ;;

    *)
        error "Invalid command: '$command'"
        usage
        exit 1
        ;;
    esac
}

main "$@"

