# Start Development Services for Windows PowerShell
Write-Host "Starting PostgreSQL, Redis, and MinIO..." -ForegroundColor Cyan
docker compose up -d postgres redis minio
Write-Host "Infrastructure started!" -ForegroundColor Green
Write-Host "Terminal 1: cd backend; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload"
Write-Host "Terminal 2: cd frontend; npm run dev"
