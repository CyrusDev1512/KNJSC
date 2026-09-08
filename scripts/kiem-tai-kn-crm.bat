@echo off
rem Kiem tai KN CRM tren may nay - AC-10.8, docs/06 tang 9. Nhay dup la chay, chay lai duoc.
rem   kiem-tai-kn-crm.bat                 nap 100 nghin dong, do don le, 100 nguoi 5 phut
rem   kiem-tai-kn-crm.bat --giu-du-lieu   da nap roi thi do luon
rem   kiem-tai-kn-crm.bat --nhanh         100 nguoi 1 phut, bo buoc tinh lai 100 nghin dong
rem Bat lai web (KN ERP) va bangtinh (KN CRM) o che do GUNICORN 3 worker (nhu may chu
rem that) -> seed_perf -> do_hieu_nang -> Locust 100 nguoi -> in DAT / KHONG DAT -> tra
rem container ve runserver. Bao cao o storage\perf\<ngay>-*.md. Du lieu gia mang ma PERF-*.
setlocal
cd /d "%~dp0.."
set "COMPOSE=docker compose -f deploy\docker-compose.yml"
set "NAP=1"
set "THOI_LUONG=5m"
set "BO_LON="
for %%t in (%*) do (
  if /i "%%~t"=="--giu-du-lieu" set "NAP=0"
  if /i "%%~t"=="--nhanh" set "THOI_LUONG=1m" & set "BO_LON=--bo-tinh-lai-lon"
)

docker info >nul 2>&1
if errorlevel 1 (
  echo Docker chua chay - nhay dup "KN JSC.bat" truoc roi chay lai.
  goto :loi
)

echo == 1/5 Bat KN ERP va KN CRM o che do gunicorn (3 tien trinh x 4 luong, nhu Dockerfile) ==
set "KNJSC_LENH_WEB=gunicorn knjsc.wsgi:application --bind 0.0.0.0:8000 --workers 3 --threads 4 --worker-class gthread --keep-alive 5"
%COMPOSE% up -d --force-recreate web bangtinh
set "KNJSC_LENH_WEB="
set /a DEM=0
:doi_web
curl -s -o nul http://127.0.0.1:8021/dang-nhap/ >nul 2>&1
if not errorlevel 1 goto :web_ok
set /a DEM+=1
if %DEM% geq 60 (
  echo KN CRM khong len sau 2 phut. Xem: %COMPOSE% logs bangtinh --tail 50
  goto :loi
)
timeout /t 2 /nobreak >nul
goto :doi_web
:web_ok
%COMPOSE% exec -T bangtinh python manage.py migrate --noinput >nul
%COMPOSE% exec -T bangtinh python manage.py du_lieu_mau >nul

if "%NAP%"=="1" (
  echo == 2/5 Nap du lieu: 100.000 dong van don + bang Sale 20.000 dong ==
  %COMPOSE% exec -T bangtinh python manage.py seed_perf --xoa-cu --so-dong 100000 --so-thang 24 --dien-day --bang-sale
) else (
  echo == 2/5 Giu du lieu da nap ==
)

echo == 3/5 Do don le (mot nguoi, khong tai) ==
%COMPOSE% exec -T bangtinh python manage.py do_hieu_nang --giai-thich %BO_LON%

echo == 4/5 Locust 100 nguoi trong %THOI_LUONG% ==
%COMPOSE% exec -T -e ERP_HOST=http://web:8000 -e KNJSC_PERF_DIR=/storage/perf bangtinh locust -f tests/perf/locustfile_kn_crm.py --host http://localhost:8000 --users 100 --spawn-rate 10 --run-time %THOI_LUONG% --headless --only-summary --reset-stats
set "KQ=%errorlevel%"

echo == 5/5 Tra container ve che do runserver ==
%COMPOSE% up -d --force-recreate web bangtinh >nul

echo.
if "%KQ%"=="0" (echo KET QUA: DAT) else (echo KET QUA: KHONG DAT - xem tung dong o tren)
echo Bao cao: storage\perf\ (tep -don-le.md va -tai-100.md cua hom nay)
start "" "storage\perf"
pause
exit /b %KQ%

:loi
pause
exit /b 1
