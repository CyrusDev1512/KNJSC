@echo off
rem Ban Windows cua cap-nhat-local.sh — bam dup la chay, hoac trong cmd:
rem
rem   scripts\cap-nhat-local.bat            keo nhanh hien tai
rem   scripts\cap-nhat-local.bat <nhanh>    chuyen sang nhanh khac roi keo
rem
rem Viec no lam: tu mo Docker Desktop neu chua chay va cho san sang -> keo ma
rem moi -> dung lai sau container -> bao dam co du lieu mau -> mo trinh duyet.
rem Dung o buoc nao thi in ro buoc do; gui man hinh cho Claude la du de sua.
setlocal
cd /d "%~dp0.."
set COMPOSE=docker compose -f deploy/docker-compose.yml

echo [1/5] Kiem Docker ...
docker info >nul 2>&1
if not errorlevel 1 goto docker_ok

set "DD="
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" set "DD=%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
if not defined DD if exist "%LocalAppData%\Docker\Docker Desktop.exe" set "DD=%LocalAppData%\Docker\Docker Desktop.exe"
if not defined DD (
  echo Docker chua chay va khong tim thay Docker Desktop o:
  echo   %ProgramFiles%\Docker\Docker\Docker Desktop.exe
  echo   %LocalAppData%\Docker\Docker Desktop.exe
  echo Mo Docker Desktop bang tay roi chay lai lenh nay.
  goto loi
)
echo Docker chua chay - dang mo Docker Desktop, cho toi da 3 phut ...
start "" "%DD%"
set /a LAN=0
:cho_docker
set /a LAN+=1
if %LAN% gtr 36 (
  echo Docker Desktop van chua san sang sau 3 phut. Mo Docker Desktop, cho bieu tuong
  echo ca voi dung yen roi chay lai lenh nay.
  goto loi
)
timeout /t 5 /nobreak >nul
docker info >nul 2>&1
if errorlevel 1 (
  <nul set /p =.
  goto cho_docker
)
echo.
:docker_ok
echo Docker san sang.

echo [2/5] Keo ma moi ...
if not "%~1"=="" (
  git fetch origin
  if errorlevel 1 goto loi_git
  git checkout %~1
  if errorlevel 1 goto loi_git
)
git pull --ff-only
if errorlevel 1 goto loi_git

echo [3/5] Dung lai container (lan dau tai image, 5-10 phut) ...
%COMPOSE% up -d --build
if errorlevel 1 (
  echo Dung container that bai - xem dong loi ngay tren.
  goto loi
)

echo [4/5] Bao dam co du lieu mau ...
%COMPOSE% exec web python manage.py du_lieu_mau
if errorlevel 1 (
  echo Nap du lieu mau that bai - xem dong loi ngay tren.
  goto loi
)

echo [5/5] Trang thai sau container:
%COMPOSE% ps

echo.
echo Xong - dang mo http://localhost:8020 (he thong) va http://localhost:8021/bang-tinh/ (Bang tinh, van don)
start "" http://localhost:8020
start "" http://localhost:8021/bang-tinh/
pause
exit /b 0

:loi_git
echo Keo ma that bai. Thuong do co sua doi cuc bo chua luu, hoac chua co mang.
echo Gui man hinh nay cho Claude.
:loi
echo.
pause
exit /b 1
