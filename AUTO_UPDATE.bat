@echo off
setlocal
cd /d "%~dp0"

echo [%date% %time%] DealHub update started
py scripts\collect.py
if errorlevel 1 (
  echo Collector failed.
  exit /b 1
)

git add data/deals.json data/history.json
git diff --cached --quiet
if %errorlevel%==0 (
  echo No data changes. Nothing to push.
  exit /b 0
)

git commit -m "Auto update DealHub data"
if errorlevel 1 exit /b 1

git push origin main
if errorlevel 1 (
  echo Push failed.
  exit /b 1
)

echo DealHub update completed.
endlocal
