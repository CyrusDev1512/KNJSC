@echo off
rem Ban Windows cua cap-nhat-local.sh — bam dup la chay, chay lai nhieu lan duoc.
rem Mo Docker Desktop neu chua chay, keo ma moi, dung lai docker compose,
rem doi web len, bao dam co du lieu mau, mo trinh duyet.
setlocal
cd /d "%~dp0.."
set "COMPOSE=docker compose -f deploy\docker-compose.yml"
set "DIA_CHI=http://127.0.0.1:8020/"

where docker >nul 2>&1
if errorlevel 1 (
  echo Chua cai Docker. Tai Docker Desktop tai https://www.docker.com/products/docker-desktop/
  goto :loi
)

docker info >nul 2>&1
if not errorlevel 1 goto :docker_ok
echo Docker chua chay, dang mo Docker Desktop ...
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
  start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
) else (
  echo Khong tim thay Docker Desktop.exe. Mo Docker Desktop bang tay roi chay lai.
  goto :loi
)
set /a DEM=0
:doi_docker
timeout /t 2 /nobreak >nul
docker info >nul 2>&1
if not errorlevel 1 goto :docker_ok
set /a DEM+=1
if %DEM% geq 90 (
  echo Doi 3 phut ma Docker van chua len. Mo Docker Desktop bang tay roi chay lai.
  goto :loi
)
goto :doi_docker

:docker_ok
echo Docker da san sang.
if not "%~1"=="" (
  git fetch origin
  git checkout %~1
)
git pull

%COMPOSE% up -d --build
if errorlevel 1 goto :loi

echo Doi web san sang tai %DIA_CHI% ...
set /a DEM=0
:doi_web
timeout /t 2 /nobreak >nul
curl -s -o nul %DIA_CHI% >nul 2>&1
if not errorlevel 1 goto :web_ok
set /a DEM+=1
if %DEM% geq 60 (
  echo Web khong len sau 2 phut. Xem nhat ky bang: %COMPOSE% logs web --tail 50
  goto :loi
)
goto :doi_web

:web_ok
%COMPOSE% exec -T web python manage.py du_lieu_mau
start "" %DIA_CHI%
echo.
echo Xong - mo http://localhost:8020 (he thong) va http://localhost:8021/bang-tinh/ (Bang tinh, van don)
pause
exit /b 0

:loi
pause
exit /b 1
