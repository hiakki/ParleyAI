@echo off
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

if "%1"=="--help" goto show_help
if "%1"=="-h" goto show_help
goto start

:show_help
echo.
echo ParleyAI - Local Chat
echo.
echo Usage:
echo   .\start_windows.bat                Start with defaults
echo   set MODEL_FAMILY=lfm2_24b          Use LFM2 model
echo   set TUNNEL=on                       Expose over the internet
echo.
echo Environment variables:
echo.
echo   Model
echo     MODEL_FAMILY    llama_70b or lfm2_24b           (default: llama_70b)
echo     QUANT           Quantization level               (default: Q4_K_M)
echo     CTX             Context window in tokens          (default: 2048)
echo     MODEL_PATH      Path to GGUF file or directory    (default: auto-download)
echo.
echo   Hardware
echo     GPU_LAYERS      Layers offloaded to GPU           (default: -1, all)
echo     BATCH_SIZE      Batch size for inference           (default: 512)
echo.
echo   Network
echo     TUNNEL          on/off - expose via tunnel         (default: off)
echo     TUNNEL_TOOL     auto, cloudflared, or localtunnel  (default: auto)
echo     SUBDOMAIN       Custom subdomain for localtunnel   (e.g. parley-ai)
echo.
echo   LFM2 specific
echo     LFM_IDLE_TIMEOUT  Seconds before llama-server auto-stops  (default: 300)
echo.
echo Examples:
echo.
echo   :: LFM2-24B on 32GB machine
echo   set MODEL_FAMILY=lfm2_24b
echo   set QUANT=Q4_K_M
echo   .\start_windows.bat
echo.
echo   :: Expose to the internet
echo   set TUNNEL=on
echo   .\start_windows.bat
echo.
echo   :: localtunnel with custom subdomain
echo   set TUNNEL=on
echo   set TUNNEL_TOOL=localtunnel
echo   set SUBDOMAIN=parley-ai
echo   .\start_windows.bat
echo.
echo   :: NVIDIA GPU with limited VRAM
echo   set GPU_LAYERS=20
echo   set QUANT=IQ2_XXS
echo   set CTX=512
echo   .\start_windows.bat
echo.
exit /b 0

:start
echo.
echo ========================================
echo   ParleyAI - Windows Startup
echo ========================================
echo.

:: Set defaults if not provided
if "%MODEL_FAMILY%"=="" set MODEL_FAMILY=llama_70b
if "%QUANT%"=="" set QUANT=Q4_K_M
if "%CTX%"=="" set CTX=2048
if "%GPU_LAYERS%"=="" set GPU_LAYERS=-1
if "%BATCH_SIZE%"=="" set BATCH_SIZE=512
if "%TUNNEL%"=="" set TUNNEL=off
if "%TUNNEL_TOOL%"=="" set TUNNEL_TOOL=auto

:: Display configuration
echo Configuration:
echo   Model family: %MODEL_FAMILY%
echo   Quantization: %QUANT%
echo   Context:      %CTX% tokens
echo   GPU Layers:   %GPU_LAYERS%
echo   Batch Size:   %BATCH_SIZE%
if defined MODEL_PATH echo   Model Path:   %MODEL_PATH%
echo.

:: Check if backend venv exists
if not exist "backend\venv\Scripts\activate.bat" (
    echo ERROR: Backend virtual environment not found!
    echo Please run setup first. See README.md for instructions.
    echo.
    pause
    exit /b 1
)

:: Check if frontend node_modules exists
if not exist "frontend\node_modules" (
    echo ERROR: Frontend dependencies not installed!
    echo Run: cd frontend ^&^& npm install
    echo.
    pause
    exit /b 1
)

:: Get local IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    for /f "tokens=*" %%b in ("%%a") do set LOCAL_IP=%%b
)
if "%LOCAL_IP%"=="" set LOCAL_IP=?.?.?.?

:: Start backend server
echo Starting backend server...
if not exist "backend\logs" mkdir "backend\logs"
set "BACKEND_LOG=%CD%\backend\logs\windows_backend_runtime.log"
if not exist "%BACKEND_LOG%" type nul > "%BACKEND_LOG%"
cd backend
start "ParleyAI Backend" cmd /c "call venv\Scripts\activate.bat ^&^& python -u -m uvicorn server:app --host 127.0.0.1 --port 8000 >> ""%BACKEND_LOG%"" 2>&1"
cd ..

:: Wait for backend to be ready
echo Waiting for backend to initialize...
set BACKEND_READY=0
set ATTEMPTS=0
set MAX_ATTEMPTS=120

:wait_loop
if %ATTEMPTS% geq %MAX_ATTEMPTS% (
    echo ERROR: Backend failed to start within 5 minutes
    echo Check the backend window for errors.
    pause
    exit /b 1
)

timeout /t 3 /nobreak >nul
set /a ATTEMPTS+=1

:: Check if backend is responding
curl -s http://localhost:8000/api/models >nul 2>&1
if %ERRORLEVEL%==0 (
    set BACKEND_READY=1
    goto backend_ready
)

:: Show progress
set /a ELAPSED=ATTEMPTS*3
echo   Still loading... (%ELAPSED%s elapsed)
goto wait_loop

:backend_ready
echo.
echo Backend is ready!
echo.

:: Write env file for Claude Code CLI
echo set ANTHROPIC_BASE_URL=http://localhost:8000> .claude_env.bat
echo set ANTHROPIC_AUTH_TOKEN=not-needed>> .claude_env.bat
echo set ANTHROPIC_MODEL=parleyai>> .claude_env.bat

:: Start frontend
echo Starting frontend...
set "FRONTEND_LOG=%CD%\frontend\windows_frontend_runtime.log"
if not exist "%FRONTEND_LOG%" type nul > "%FRONTEND_LOG%"
cd frontend
start "ParleyAI Frontend" cmd /c "npm run dev >> ""%FRONTEND_LOG%"" 2>&1"
cd ..

:: Start tunnel if requested
set TUNNEL_URL=
if /i "%TUNNEL%"=="on" (
    echo.
    echo Starting internet tunnel ^(TUNNEL_TOOL=%TUNNEL_TOOL%^)...

    set USE_CF=0
    set USE_LT=0
    if /i "%TUNNEL_TOOL%"=="cloudflared" (
        set USE_CF=1
    ) else if /i "%TUNNEL_TOOL%"=="localtunnel" (
        set USE_LT=1
    ) else (
        where cloudflared >nul 2>&1
        if !ERRORLEVEL!==0 (
            set USE_CF=1
        ) else (
            where lt >nul 2>&1
            if !ERRORLEVEL!==0 (
                set USE_LT=1
            ) else (
                set USE_CF=1
            )
        )
    )

    if !USE_CF!==1 (
        where cloudflared >nul 2>&1
        if !ERRORLEVEL!==0 (
            start "ParleyAI Tunnel" cmd /c "cloudflared tunnel --url http://localhost:5173 --protocol http2 --no-autoupdate 2>.tunnel.log"
            timeout /t 8 /nobreak >nul
            echo   Cloudflare tunnel started. Check .tunnel.log for URL.
        ) else (
            echo   cloudflared not found. Install: choco install cloudflared
        )
    )

    if !USE_LT!==1 (
        where lt >nul 2>&1
        if !ERRORLEVEL!==0 (
            set LT_ARGS=--port 5173
            if defined SUBDOMAIN (
                echo   Requesting subdomain: %SUBDOMAIN%
                set LT_ARGS=!LT_ARGS! --subdomain %SUBDOMAIN%
            )
            start "ParleyAI Tunnel" cmd /c "lt !LT_ARGS! > .tunnel.log 2>&1"
            timeout /t 5 /nobreak >nul
            echo   localtunnel started. Check .tunnel.log for URL.
        ) else (
            echo   localtunnel not found. Install: npm install -g localtunnel
        )
    )
    echo.
)

echo.
echo ========================================
echo   Application Started!
echo ========================================
echo.
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000  (localhost only)
echo.
echo   Network (LAN):
echo     Frontend: http://%LOCAL_IP%:5173
if /i "%TUNNEL%"=="on" (
echo.
echo   Internet:
echo     See .tunnel.log for the public URL
)
echo.
echo   Claude Code CLI (in another terminal):
echo     .claude_env.bat ^&^& claude
echo.
echo   Runtime logs:
echo     Backend:  %BACKEND_LOG%
echo     Frontend: %FRONTEND_LOG%
echo.
echo   Tail logs live:
echo     PowerShell: Get-Content "%BACKEND_LOG%" -Wait
echo     CMD:        powershell -NoProfile -Command "Get-Content '%BACKEND_LOG%' -Wait"
echo.
echo   Press Ctrl+C in each window to stop.
echo.

pause
