@echo off
chcp 65001 >nul
title DealHub 수동 업데이트
cd /d "%~dp0"

echo.
echo ========================================
echo   DealHub 핫딜 업데이트를 시작합니다.
echo ========================================
echo.

py scripts\collect.py
if errorlevel 1 (
  echo.
  echo [실패] 핫딜 수집 중 오류가 발생했습니다.
  echo 창을 캡처해서 ChatGPT에 보내주세요.
  pause
  exit /b 1
)

git add data/deals.json data/history.json
git diff --cached --quiet
if %errorlevel%==0 (
  echo.
  echo [완료] 새로 변경된 데이터가 없습니다.
  pause
  exit /b 0
)

git commit -m "Manual update DealHub data"
if errorlevel 1 (
  echo.
  echo [실패] Git 저장 중 오류가 발생했습니다.
  pause
  exit /b 1
)

git push origin main
if errorlevel 1 (
  echo.
  echo [실패] GitHub 업로드 중 오류가 발생했습니다.
  pause
  exit /b 1
)

echo.
echo ========================================
echo   완료! DealHub 데이터가 업데이트됐습니다.
echo   잠시 후 사이트를 새로고침하세요.
echo ========================================
echo.
pause
