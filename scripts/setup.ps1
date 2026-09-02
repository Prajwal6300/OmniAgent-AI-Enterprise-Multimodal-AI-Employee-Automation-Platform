# OmniAgent AI Setup Script for Windows PowerShell
$ErrorActionPreference = "Stop"
Write-Host "Setting up OmniAgent AI environment..." -ForegroundColor Cyan

# 1. Backend setup
Set-Location backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Set-Location ..

# 2. Frontend setup
Set-Location frontend
npm install
Set-Location ..

Write-Host "Setup complete! Run .\scripts\dev.ps1 to start development." -ForegroundColor Green
