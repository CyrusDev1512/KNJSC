@echo off
rem KN JSC - mo he thong tren may nay: nhay dup la chay, chay lai bao nhieu
rem lan cung duoc. Lan dau chay tu tao loi tat "KN JSC" ngoai Desktop (bieu
rem tuong la KN JSC.ico cung thu muc); tu do nhay dup loi tat la du.
rem
rem Khac voi cap-nhat-local.bat: KHONG keo ma moi, KHONG dung lai image, KHONG
rem nap lai du lieu mau (tru lan dau tren may sach) - nen container da co thi
rem vai giay la len. Viec no lam: mo Docker Desktop neu chua chay, bat
rem container, doi web tra loi, roi mo trinh duyet.
rem
rem Muon cap nhat ma moi thi chay cap-nhat-local.bat.
setlocal
chcp 65001 >nul
title KN JSC
cd /d "%~dp0.."
set "COMPOSE=docker compose -f deploy\docker-compose.yml"
set "DIA_CHI=http://127.0.0.1:8020/"
set "DOCKER_DESKTOP=%ProgramFiles%\Docker\Docker\Docker Desktop.exe"

rem --- 0. Loi tat ngoai Desktop. Chi tao khi chua co, de ai da xoa thi khong
rem bi moc lai; muon tao lai thi xoa loi tat roi chay tep nay. Duong dan
rem Desktop lay tu Registry vi may dung OneDrive thi Desktop khong nam trong
rem thu muc nguoi dung ---
set "MAN_HINH="
for /f "tokens=2,*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop 2^>nul ^| find "REG_SZ"') do set "MAN_HINH=%%b"
if not defined MAN_HINH set "MAN_HINH=%USERPROFILE%\Desktop"
set "LOI_TAT=%MAN_HINH%\KN JSC.lnk"
set "TEP_BAT=%~f0"
set "THU_MUC=%~dp0"
set "BIEU_TUONG=%~dp0KN JSC.ico"
if exist "%LOI_TAT%" goto :co_loi_tat
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:LOI_TAT);$s.TargetPath=$env:TEP_BAT;$s.WorkingDirectory=$env:THU_MUC;$s.IconLocation=$env:BIEU_TUONG+',0';$s.Description='Mo he thong KN JSC';$s.Save()" >nul 2>&1
if exist "%LOI_TAT%" (echo Da tao loi tat "KN JSC" ngoai Desktop.) else (echo Khong tao duoc loi tat ngoai Desktop - bo qua, he thong van mo binh thuong.)

:co_loi_tat
rem --- 1. Co Docker chua? Vua cai xong thi PATH cua cua so nay co the chua co ---
where docker >nul 2>&1
if not errorlevel 1 goto :co_docker
if not exist "%ProgramFiles%\Docker\Docker\resources\bin\docker.exe" goto :chua_cai_docker
set "PATH=%ProgramFiles%\Docker\Docker\resources\bin;%PATH%"
goto :co_docker

:chua_cai_docker
echo Chua cai Docker. Tai Docker Desktop tai https://www.docker.com/products/docker-desktop/
goto :loi

:co_docker
rem --- 2. Docker dang chay chua? Chua thi mo Docker Desktop roi doi ---
docker info >nul 2>&1
if not errorlevel 1 goto :docker_ok
echo Docker chua chay, dang mo Docker Desktop ...
if exist "%DOCKER_DESKTOP%" goto :mo_docker
rem Cai o thu muc khac: hoi Registry xem Docker Desktop nam o dau
for /f "tokens=2,*" %%a in ('reg query "HKLM\SOFTWARE\Docker Inc.\Docker\1.0" /v AppPath 2^>nul ^| find "AppPath"') do set "DOCKER_DESKTOP=%%b\Docker Desktop.exe"
if exist "%DOCKER_DESKTOP%" goto :mo_docker
echo Khong tim thay Docker Desktop.exe. Mo Docker Desktop bang tay roi chay lai.
goto :loi

:mo_docker
start "" "%DOCKER_DESKTOP%"
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

rem --- 3. Lan dau tren may nay? Chua co container web nghia la co so du lieu
rem trong, phai nap tai khoan mau truoc khi mo trinh duyet - khong thi khong
rem co tai khoan nao de dang nhap ---
set "LAN_DAU=1"
for /f %%i in ('%COMPOSE% ps -a -q web 2^>nul') do set "LAN_DAU=0"

rem --- 4. Bat container. Khong --build: image da co thi dung lai, chua co
rem (lan dau) thi compose tu dung. Container khoi dong lai thi entrypoint tu
rem chay migrate va tao_bang_van_don ---
%COMPOSE% up -d
if errorlevel 1 goto :loi

rem --- 5. Doi web tra loi. Kiem ngay truoc khi ngu, vi container dang chay
rem san thi khong phai doi giay nao ---
echo Doi web tai %DIA_CHI% ...
set /a DEM=0
:doi_web
curl -s -o nul --max-time 3 %DIA_CHI% >nul 2>&1
if not errorlevel 1 goto :web_ok
set /a DEM+=1
if %DEM% geq 120 (
  echo Web khong len sau 2 phut. Xem nhat ky bang: %COMPOSE% logs web --tail 50
  goto :loi
)
timeout /t 1 /nobreak >nul
goto :doi_web

:web_ok
if "%LAN_DAU%"=="1" (
  echo May moi, dang nap tai khoan mau - mat khau in ra cuoi lenh ...
  %COMPOSE% exec -T web python manage.py du_lieu_mau
)
start "" %DIA_CHI%
echo.
echo Da mo http://localhost:8020 (he thong). Bang tinh van don: http://localhost:8021/bang-tinh/
echo Tai khoan mau xem o docs\tai-khoan-mau.md
if "%LAN_DAU%"=="1" (
  pause
  exit /b 0
)
timeout /t 5
exit /b 0

:loi
pause
exit /b 1
