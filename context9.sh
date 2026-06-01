#!/usr/bin/env bash
# MCP-Context9 Server 管理脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
SERVER_MODULE="src.server"
LOG_FILE="/tmp/server_out.txt"
PID=

get_pid() {
    PID=$(ps aux | grep "$SERVER_MODULE" | grep -v grep | awk '{print $2}' | head -1)
}

is_running() {
    get_pid
    [ -n "$PID" ]
}

start() {
    if is_running; then
        echo "Server is already running (PID: $PID)"
        return 1
    fi
    echo "Starting server..."
    PYTHONUNBUFFERED=1 "$VENV_PYTHON" -m "$SERVER_MODULE" > "$LOG_FILE" 2>&1 &
    sleep 2
    get_pid
    if is_running; then
        echo "Server started (PID: $PID)"
    else
        echo "Server failed to start. Check $LOG_FILE"
        return 1
    fi
}

stop() {
    if ! is_running; then
        echo "Server is not running"
        return 0
    fi
    echo "Stopping server (PID: $PID)..."
    kill "$PID" 2>/dev/null || true
    sleep 2
    if is_running; then
        echo "Server did not stop gracefully, killing..."
        kill -9 "$PID" 2>/dev/null || true
    fi
    echo "Server stopped"
}

status() {
    if is_running; then
        echo "Server is running (PID: $PID)"
    else
        echo "Server is not running"
    fi
}

case "${1:-start}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 1
        start
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
