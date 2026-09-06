@echo off
rem KN JSC - nhay dup la mo he thong tren may nay. Chay lai bao nhieu lan cung
rem duoc, may nao cung duoc: clone kho ma ve, nhay dup tep nay, xong.
rem
rem No lam gi:
rem   1. Keo ma moi tu GitHub - co git va co mang thi keo, khong thi bo qua.
rem      Keo khong duoc - dang gop do, sua tay chua commit, mat mang - thi NOI
rem      RO tren man hinh roi van bat ban dang co; khong nuot loi.
rem   2. Tao (hoac lam moi) loi tat "KN JSC" co logo ngoai Desktop, tu do
rem      nhay dup logo la du.
rem   3. Mo Docker Desktop neu chua chay, bat container.
rem   4. Co ma moi thi chay migrate va tao_bang_van_don, khoi dong lai worker;
rem      dung lai image chi khi Dockerfile, requirements hay entrypoint doi.
rem      Khong co ma moi thi vai giay la len.
rem   5. May sach thi nap tai khoan mau - du_lieu_mau. Roi mo trinh duyet.
rem
rem Tham so "loi-tat": chi tao loi tat roi thoat - cap-nhat-local.bat dung.
rem Tham so "da-keo" la noi bo, GIU NGUYEN TEN khi sua tep nay.
rem
rem Vi sao tep goi lai chinh no sau khi keo ma: cmd doc tep .bat theo vi tri
rem byte, keo ma co the doi chinh tep nay, doc tiep se lech dong. Nen phan keo
rem ma nam tron trong mot khoi ( ... ) da duoc doc het truoc khi chay: keo xong
rem thi call lai tep - luc nay la ban moi - roi thoat, khong doc them dong nao
rem cua ban cu nua.
setlocal
chcp 65001 >nul
title KN JSC
cd /d "%~dp0"
set "CHE_DO=%~1"
if /i "%~1"=="da-keo" set "CHE_DO=%~2"
if /i "%~1"=="da-keo" goto :bat_dau
if /i "%CHE_DO%"=="loi-tat" goto :bat_dau

rem --- Keo ma moi. TRUOC va SAU la ma commit truoc va sau khi keo ---
set "TRUOC="
set "SAU="
set "GIT_TERMINAL_PROMPT=0"
if not exist ".git" goto :khong_keo
where git >nul 2>&1
if errorlevel 1 goto :khong_keo
for /f %%h in ('git rev-parse HEAD 2^>nul') do set "TRUOC=%%h"
rem Kho ma dang do dang mot lan gop hay rebase - xung dot chua giai - thi git
rem pull tu choi. Noi ro va khong keo. Truoc day pull -q nuot loi nay, nguoi
rem dung tuong da co ma moi ma van chay ban cu - 06.09.2026
if exist ".git\MERGE_HEAD" goto :gop_do
if exist ".git\rebase-merge" goto :gop_do
if exist ".git\rebase-apply" goto :gop_do
set "NHANH="
for /f %%b in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "NHANH=%%b"
echo Nhanh dang dung: %NHANH%
if /i not "%NHANH%"=="main" echo   Khong phai main - chi keo ban moi cua nhanh nay. Ve main: scripts\cap-nhat-local.bat main
rem Tep nay chua duoc git theo doi - nguoi dung tai ve roi tha vao thu muc -
rem thi git pull se tu choi ghi de. Tam doi no ra ngoai, keo xong dung ban tu
rem GitHub; keo khong duoc thi tra lai. Ca khoi da doc het truoc khi chay.
set "DA_THEO_DOI="
git ls-files --error-unmatch "KN JSC.bat" >nul 2>&1 && set "DA_THEO_DOI=1"
echo Kiem tra ma moi tren GitHub ...
(
  if not defined DA_THEO_DOI move /y "%~f0" "%TEMP%\KN JSC.bat.cu" >nul
  git pull --ff-only
  if errorlevel 1 (
    echo.
    echo KHONG KEO DUOC MA MOI - xem loi git ngay tren. He thong se chay ban dang co tren may.
    echo Thu: scripts\cap-nhat-local.bat main
    timeout /t 8
  )
  if not exist "%~f0" move /y "%TEMP%\KN JSC.bat.cu" "%~f0" >nul
  for /f %%h in ('git rev-parse HEAD 2^>nul') do set "SAU=%%h"
  call "%~f0" da-keo %*
  exit /b
)
:gop_do
echo.
echo Kho ma dang do dang mot lan gop - xung dot chua giai - nen khong keo duoc ma moi.
echo He thong se chay ban dang co tren may. De go, mo cmd tai thu muc nay va chay:
echo     git merge --abort
echo     git checkout main
echo     git pull --ff-only
echo roi nhay dup lai KN JSC.bat
timeout /t 10
:khong_keo
call "%~f0" da-keo %*
exit /b

:bat_dau
rem ======= Tu day tro di chay tren ban moi nhat cua tep =======
set "COMPOSE=docker compose -f deploy\docker-compose.yml"
set "DIA_CHI=http://127.0.0.1:8020/"
set "DOCKER_DESKTOP=%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
set "CO_MA_MOI="
if defined SAU if not "%TRUOC%"=="%SAU%" set "CO_MA_MOI=1"
if defined CO_MA_MOI echo Da keo ma moi ve.

rem --- 0. Loi tat ngoai Desktop: lam moi moi lan chay de luon tro dung cho,
rem ke ca khi thu muc kho ma doi ten hay chuyen cho. Duong dan Desktop lay tu
rem Registry vi may dung OneDrive thi Desktop khong nam trong thu muc nguoi dung ---
set "MAN_HINH="
for /f "tokens=2,*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop 2^>nul ^| find "REG_SZ"') do set "MAN_HINH=%%b"
if not defined MAN_HINH set "MAN_HINH=%USERPROFILE%\Desktop"
set "LOI_TAT=%MAN_HINH%\KN JSC.lnk"
set "TEP_BAT=%~f0"
set "THU_MUC=%~dp0"
set "BIEU_TUONG=%~dp0scripts\KN JSC.ico"
set "LOI_TAT_MOI=1"
if exist "%LOI_TAT%" set "LOI_TAT_MOI="
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:LOI_TAT);$s.TargetPath=$env:TEP_BAT;$s.WorkingDirectory=$env:THU_MUC;$s.IconLocation=$env:BIEU_TUONG+',0';$s.Description='Mo he thong KN JSC';$s.Save()" >nul 2>&1
if exist "%LOI_TAT%" (
  if defined LOI_TAT_MOI echo Da tao loi tat "KN JSC" ngoai Desktop - tu mai nhay dup logo do la du.
) else (
  echo Khong tao duoc loi tat ngoai Desktop - bo qua, he thong van mo binh thuong.
)
if /i "%CHE_DO%"=="loi-tat" exit /b 0

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

rem --- 4. Bat container. Dung lai image chi khi thu vien hay Dockerfile doi;
rem con lai image da co thi dung lai, chua co thi compose tu dung. Container
rem khoi dong lai thi entrypoint tu chay migrate va tao_bang_van_don ---
set "DUNG_LAI="
if defined CO_MA_MOI for /f %%x in ('git diff --name-only %TRUOC% %SAU% -- app/requirements.txt app/requirements-dev.txt deploy/Dockerfile deploy/entrypoint.sh 2^>nul') do set "DUNG_LAI=--build"
if defined DUNG_LAI echo Thu vien hay Dockerfile doi, dang dung lai image - mat vai phut ...
%COMPOSE% up -d %DUNG_LAI%
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
rem Ma moi vao container qua thu muc gan ngoai, container khong dung lai nen
rem migrate trong entrypoint khong chay - goi tuong minh. Worker va beat khong
rem tu nap lai ma nhu runserver nen khoi dong lai
if defined CO_MA_MOI (
  echo Cap nhat cau truc du lieu theo ma moi ...
  %COMPOSE% exec -T web python manage.py migrate --noinput
  %COMPOSE% exec -T web python manage.py tao_bang_van_don
  %COMPOSE% restart worker beat
)
if "%LAN_DAU%"=="1" (
  echo May moi, dang nap tai khoan mau - mat khau in ra cuoi lenh ...
  %COMPOSE% exec -T web python manage.py du_lieu_mau
)
start "" %DIA_CHI%
echo.
echo Da mo http://localhost:8020 - KN ERP. KN CRM - bang tinh: http://localhost:8021/
if not defined CO_MA_MOI echo Khong co ma moi - neu vua gop code tren GitHub ma khong thay doi, xem dong Nhanh dang dung o tren.
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
