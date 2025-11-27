@echo off
REM Test script to verify API key validation using curl

echo.
echo ============================================================
echo API Key Validation Tests
echo ============================================================

setlocal enabledelayedexpansion

set API_KEY=test-api-key-12345
set BASE_URL=http://127.0.0.1:8000

echo.
echo [Test 1] Request WITHOUT X-API-Key header (should return 401):
curl -s -w "\nStatus: %%{http_code}\n" %BASE_URL%/api/movies
timeout /t 1 /nobreak > nul

echo.
echo [Test 2] Request with INVALID X-API-Key header (should return 401):
curl -s -w "\nStatus: %%{http_code}\n" -H "X-API-Key: wrong-key" %BASE_URL%/api/movies
timeout /t 1 /nobreak > nul

echo.
echo [Test 3] Request with VALID X-API-Key header (should return 200):
curl -s -w "\nStatus: %%{http_code}\n" -H "X-API-Key: %API_KEY%" %BASE_URL%/api/movies
timeout /t 1 /nobreak > nul

echo.
echo [Test 4] Health endpoint (no API key required):
curl -s -w "\nStatus: %%{http_code}\n" %BASE_URL%/health
timeout /t 1 /nobreak > nul

echo.
echo ============================================================
echo Tests complete!
echo ============================================================
