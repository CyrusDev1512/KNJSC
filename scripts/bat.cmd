@echo off
rem Bật hệ thống trên máy cá nhân bằng một lệnh (Windows).
rem Mac và Linux dùng scripts/bat.sh.
rem
rem   scripts\bat.cmd      (hoặc nháy đúp vào tệp này)
rem
rem Làm lần lượt: mở Docker Desktop nếu chưa chạy, dựng các container, đợi
rem web sẵn sàng, nạp dữ liệu mẫu (12 tài khoản, chạy lại không sao), rồi mở
rem trình duyệt ở http://127.0.0.1:8020/
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
echo Dang dung cac container ...
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
  echo Web khong len sau 2 phut. Xem nhat ky bang:
  echo   %COMPOSE% logs web --tail 50
  goto :loi
)
goto :doi_web

:web_ok
echo Nap du lieu mau ...
%COMPOSE% exec -T web python manage.py du_lieu_mau

echo Mo trinh duyet ...
start "" %DIA_CHI%
echo Xong. Dang nhap tai %DIA_CHI%
pause
exit /b 0

:loi
pause
exit /b 1
