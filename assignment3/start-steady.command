#!/bin/bash
# Double-click to run Steady (backend :8001 + frontend :5174). Close this window to stop both.
# Adapted from Expedia Lite's start-app.command.
cd "$(dirname "$0")"
ROOT="$(pwd)"
for port in 8001 5174; do
  pids=$(lsof -ti tcp:$port -sTCP:LISTEN 2>/dev/null)
  for pid in $pids; do
    cmd=$(ps -o command= -p $pid)
    if [[ "$cmd" == *uvicorn* || "$cmd" == *vite* ]]; then
      echo "Stopping old Steady process on :$port (pid $pid)"; kill $pid
    else
      echo "Port $port is used by another program ($cmd) -- leaving it alone."
    fi
  done
done
sleep 1
cd "$ROOT/backend"
[ -f .env ] || cp .env.example .env
PY=python3; command -v python3 >/dev/null || PY=python
$PY -c "import fastapi, httpx, dotenv" 2>/dev/null || $PY -m pip install -r requirements.txt || $PY -m pip install --user -r requirements.txt
$PY -m uvicorn main:app --reload --port 8001 &
BACK=$!
trap 'kill $BACK 2>/dev/null' EXIT
cd "$ROOT/frontend"
[ -d node_modules ] || npm install
sleep 2
open "http://127.0.0.1:5174"
npm run dev
