#!/bin/bash

echo "=== Network Frames Launcher ==="

if [ "$EUID" -ne 0 ]; then
  echo "[ERROR] The application requires low-level network access."
  echo "Please run the script using the following command:"
  echo "sudo -E ./run.sh"
  exit 1
fi

if [ ! -d ".venv" ]; then
    echo "[INFO] Creating an isolated Python environment (.venv)..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create venv. Do you have the 'python3-venv' package installed?"
        exit 1
    fi
fi

echo "[INFO] Checking and installing dependencies from requirements.txt..."
source .venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

echo "[INFO] Starting the application..."
python3 main.py

deactivate
echo "=== App Closed ==="