@echo off
rem Ban Windows cua cap-nhat-local.sh - bam dup la chay, chay lai nhieu lan duoc.
rem Mo Docker Desktop neu chua chay, keo ma moi, dung lai docker compose,
rem doi web len, bao dam co du lieu mau, mo trinh duyet.
rem Hang ngay chi can nhay dup "KN JSC.bat" o thu muc goc (no tu keo ma, tu
rem migrate). Tep nay la ban "lam het cho chac": chuyen nhanh, LUON dung lai
rem image, migrate, nap du lieu mau - dung khi doi nhanh hay khi KN JSC.bat len
rem ma man hinh loi.
rem
rem Tham so: ten nhanh muon chuyen sang, khong bat buoc. "da-keo" la tham so
rem noi bo, GIU NGUYEN TEN: keo ma xong tep goi lai chinh no, vi cmd doc tep
rem .bat theo vi tri byte, keo ma doi chinh tep nay thi doc tiep se lech dong.
rem Nen phan keo ma nam tron trong mot khoi ( ... ) da doc het truoc khi chay.
setlocal
cd /d "%~dp0.."
set "COMPOSE=docker compose -f deploy\docker-compose.yml"
set "DIA_CHI=http://127.0.0.1:8020/"
if /i "%~1"=="da-keo" goto :sau_keo

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
rem Keo ma trong mot khoi, keo xong goi lai ban moi cua tep roi thoat ngay
(
  if not "%~1"=="" (
    git fetch origin
    git checkout %~1
  )
  git pull
  call "%~f0" da-keo
  exit /b
)

:sau_keo
rem ======= Tu day tro di chay tren ban moi nhat cua tep =======
rem Loi tat "KN JSC" ngoai Desktop (bieu tuong scripts\KN JSC.ico) - de keo ma
rem xong la thay logo ngay; tu do nhay dup logo la mo he thong
if exist "%~dp0..\KN JSC.bat" call "%~dp0..\KN JSC.bat" loi-tat

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
rem Ma moi vao container qua thu muc gan ngoai, container khong dung lai nen
rem migrate trong entrypoint khong chay lai - goi tuong minh
%COMPOSE% exec -T web python manage.py migrate --noinput
%COMPOSE% exec -T web python manage.py tao_bang_van_don
%COMPOSE% exec -T web python manage.py du_lieu_mau
start "" %DIA_CHI%
echo.
echo Xong - mo http://localhost:8020 (KN ERP) va http://localhost:8021/ (KN CRM, bang tinh)
pause
exit /b 0

:loi
pause
exit /b 1
