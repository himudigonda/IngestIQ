#!/bin/bash

# ==============================================================================
# IngestIQ - Project Management Script
#
# A centralized CLI for managing the IngestIQ local development environment.
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
clean_all() {
    log_action "Initiating full data, log, and environment teardown..."
    echo -e "${COLOR_RED}WARNING:${COLOR_RESET} This will permanently delete all local data, logs, and stop all services."
    read -p "Are you sure you want to proceed? (y/N): " final_confirm
    if [[ ! "$final_confirm" =~ ^[Yy]$ ]]; then
        error "Cleanup cancelled by user."
        exit 1
    fi

    log_action "Stopping containers and removing Docker volumes..."
    docker compose down --volumes

    log_action "Deleting local data directories..."
    rm -rf ./local_data

    log_action "Deleting Airflow log directories..."
    rm -rf ./airflow/logs

    log_action "Purging Python artifacts and caches..."
    find . -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name "*.egg-info" \) -exec rm -rf {} +

    log_success "Full cleanup complete."
}

# --- Main Logic ---
usage() {
    echo "Usage: $0 [COMMAND]"
    echo "Project utility script for IngestIQ."
    echo
    echo "Commands:"
    echo "  up            Build and start all services in detached mode."
    echo "  down          Stop all running services."
    echo "  logs          Follow the logs of all services."
    echo "  clean-data    DANGER: Stop services and delete all local data and logs."
    echo "  reset         DANGER: Wipes all data and logs, then rebuilds and starts the environment."
    echo "  help          Display this help message."
    echo
}

main() {
    local command="${1:-up}"
    shift || true

    case "$command" in
    up)
        if [ ! -f .env ]; then
            error "Security Check Failed: .env file missing. Please copy .env.example and configure secrets."
            exit 1
        fi
        log_action "Building and starting all IngestIQ services..."
        docker compose up --build -d
        
        log_action "Waiting for database..."
        sleep 10
        
        log_action "Initializing Security (Admin User)..."
        # Run the script inside the API container to access DB
        docker compose exec -T api python scripts/create_admin.py
        
        log_success "System is up and secured."
        ;;

    down)
        log_action "Stopping all IngestIQ services..."
        docker compose down
        log_success "Services stopped."
        ;;

    logs)
        log_action "Following logs for all services. Press Ctrl+C to exit."
        docker compose logs -f
        ;;

    clean-data)
        clean_all
        ;;
    
    reset)
        log_action "--- Starting Full Environment Reset ---"
        clean_all
        if [ ! -f .env ]; then
            error "Security Check Failed: .env file missing. Please copy .env.example and configure secrets."
            exit 1
        fi
        log_action "Building and starting all IngestIQ services..."
        docker compose up --build -d
        
        log_action "Waiting for database..."
        sleep 10
        
        log_action "Initializing Security (Admin User)..."
        docker compose exec -T api python scripts/create_admin.py
        
        log_success "--- Environment Reset Complete ---"
        log "System is up and secured."
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

