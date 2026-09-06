@echo off
rem Cai dat nut "KN JSC" ngoai Desktop - nhay dup tep nay MOT LAN, o bat ky dau
rem (thu muc Downloads cung duoc). No tu tim thu muc ma nguon KNJSC tren may,
rem keo ma moi nhat, tao loi tat KN JSC (co logo) ngoai Desktop roi mo he thong
rem luon. Tu hom sau chi can nhay dup logo KN JSC tren Desktop, khong go gi ca.
setlocal
chcp 65001 >nul
title Cai dat KN JSC
set "KHO="

rem --- 1. Tep nay dang nam ngay trong kho ma? ---
if exist "%~dp0scripts\cap-nhat-local.bat" set "KHO=%~dp0"
if not defined KHO if exist "%~dp0cap-nhat-local.bat" set "KHO=%~dp0..\"
if defined KHO goto :thay_kho

rem --- 2. Nhung cho hay clone ve ---
for %%d in ("%USERPROFILE%" "%USERPROFILE%\Desktop" "%USERPROFILE%\Documents" "%USERPROFILE%\Downloads" "%USERPROFILE%\source\repos" "%USERPROFILE%\OneDrive\Desktop" "%USERPROFILE%\OneDrive\Documents" "%USERPROFILE%\OneDrive" "C:\" "D:\" "E:\" "C:\Projects" "C:\Code" "D:\Projects" "D:\Code") do (
  for %%t in (KNJSC knjsc kim-ngan-jsc) do (
    if not defined KHO if exist "%%~d\%%t\scripts\cap-nhat-local.bat" set "KHO=%%~d\%%t\"
  )
)
if defined KHO goto :thay_kho

rem --- 3. Tim sau hon: quet thu muc nguoi dung roi tung o dia, co the mat mot phut ---
echo Dang tim thu muc ma nguon KNJSC tren may, cho mot chut ...
for /f "delims=" %%f in ('dir /s /b "%USERPROFILE%\cap-nhat-local.bat" 2^>nul') do if not defined KHO set "KHO=%%~dpf..\"
if defined KHO goto :thay_kho
for %%d in (C D E F) do (
  if not defined KHO for /f "delims=" %%f in ('dir /s /b "%%d:\cap-nhat-local.bat" 2^>nul') do if not defined KHO set "KHO=%%~dpf..\"
)
if defined KHO goto :thay_kho
echo Khong tim thay thu muc ma nguon KNJSC tren may nay.
echo Chep tep nay vao thu muc KNJSC (canh thu muc scripts) roi nhay dup lai.
goto :loi

:thay_kho
rem Rut gon duong dan (bo "..\") cho de doc
for %%k in ("%KHO%.") do set "KHO=%%~fk\"
echo Thay kho ma o: %KHO%
echo Dang keo ma moi nhat ...
git -C "%KHO%." pull
if not exist "%KHO%KN JSC.bat" (
  echo Keo ma xong van chua thay KN JSC.bat. Chup man hinh cua so nay gui nguoi ho tro.
  goto :loi
)
rem KN JSC.bat tu tao loi tat ngoai Desktop neu chua co, roi mo he thong
call "%KHO%KN JSC.bat"
exit /b 0

:loi
pause
exit /b 1
