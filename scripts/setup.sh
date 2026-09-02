#!/usr/bin/env bash
set -e
echo "Setting up OmniAgent AI environment..."

# 1. Backend venv and packages
cd backend
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# 2. Frontend dependencies
cd frontend
npm install
cd ..

echo "Setup complete! Run ./scripts/dev.sh to start development."
