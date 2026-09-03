@echo off
rem Ban Windows cua cap-nhat-local.sh — bam dup la chay.
rem Keo ma moi, dung lai docker compose, bao dam co du lieu mau.
cd /d "%~dp0.."

docker info >nul 2>&1
if errorlevel 1 (
  echo Docker chua chay - mo Docker Desktop roi chay lai.
  pause
  exit /b 1
)

if not "%~1"=="" (
  git fetch origin
  git checkout %~1
)
git pull

docker compose -f deploy/docker-compose.yml up -d --build
docker compose -f deploy/docker-compose.yml exec web python manage.py du_lieu_mau

echo.
echo Xong - mo http://localhost:8020 (he thong) va http://localhost:8021/bang-tinh/ (Bang tinh, van don)
pause
