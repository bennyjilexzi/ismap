#!/bin/bash
set -e

# --- Configuration ---
PROJECT_DIR="$(pwd)"
SERVICE_NAME="ismap"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

echo "🚀 Starting ISMAP Native Linux Deployment (without Docker)..."

# 1. Install/Update Dependencies
echo "📦 Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt gunicorn

# 2. Build Frontend
echo "⚛️ Building Frontend..."
cd frontend
npm install
npm run build
cd ..

# 3. Create Systemd Service File
echo "📝 Configuring Background Service..."
sudo bash -c "cat << EOF > $SERVICE_FILE
[Unit]
Description=ISMAP Subdomain Scanner
After=network.target

[Service]
User=$(whoami)
Group=$(id -gn)
WorkingDirectory=$PROJECT_DIR
Environment=\"PATH=$PROJECT_DIR/venv/bin\"
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --bind 0.0.0.0:5000 --timeout 120 --workers 1 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF"

# 4. Finalize
echo "⚙️ Reloading services..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

echo "✅ SUCCESS! ISMAP is now running as a background service."
echo "🌍 URL: http://localhost:5000"
echo "🛠️ COMMANDS:"
echo "   Stop: sudo systemctl stop $SERVICE_NAME"
echo "   Log: journalctl -u $SERVICE_NAME -f"
echo "   Restart: sudo systemctl restart $SERVICE_NAME"
