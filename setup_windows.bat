@echo off
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo.
echo =====================================================
echo   ParleyAI - Windows Setup (NVIDIA CUDA)
echo =====================================================
echo.
echo IMPORTANT:
echo   Run this script from "x64 Native Tools Command Prompt for VS 2022"
echo   and launch that terminal as Administrator.
echo.

:: ========================================
:: Check for winget (built into Win 10/11)
:: ========================================
set HAS_WINGET=0
where winget >nul 2>&1
if !ERRORLEVEL!==0 set HAS_WINGET=1

:: ========================================
:: Check and Auto-Install Prerequisites
:: ========================================
echo Checking prerequisites...
echo.
set NEED_PATH_REFRESH=0
set NEED_RESTART=0

:: ---- Python ----
python --version >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo [X] Python - NOT FOUND
    if !HAS_WINGET!==1 (
        echo     Installing Python via winget...
        winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
        if !ERRORLEVEL!==0 (
            echo     [OK] Python installed
            set NEED_PATH_REFRESH=1
        ) else (
            echo     [!] winget install failed — install manually: https://www.python.org/downloads/
            echo         Make sure to check "Add Python to PATH" during installation
            set MISSING_CRITICAL=1
        )
    ) else (
        echo     Install from: https://www.python.org/downloads/
        echo     Make sure to check "Add Python to PATH" during installation
        set MISSING_CRITICAL=1
    )
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo [OK] Python %%i
)

:: ---- Node.js ----
node --version >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo [X] Node.js - NOT FOUND
    if !HAS_WINGET!==1 (
        echo     Installing Node.js LTS via winget...
        winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements
        if !ERRORLEVEL!==0 (
            echo     [OK] Node.js installed
            set NEED_PATH_REFRESH=1
        ) else (
            echo     [!] winget install failed — install manually: https://nodejs.org/
            set MISSING_CRITICAL=1
        )
    ) else (
        echo     Install from: https://nodejs.org/
        set MISSING_CRITICAL=1
    )
) else (
    for /f "tokens=1" %%i in ('node --version 2^>^&1') do echo [OK] Node.js %%i
)

:: ---- NVIDIA Driver ----
nvidia-smi >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo [X] NVIDIA Driver - NOT FOUND
    echo     Install from: https://www.nvidia.com/Download/index.aspx
    echo     ^(Driver is GPU-specific — automatic install is not recommended^)
    set MISSING_CRITICAL=1
) else (
    for /f "tokens=3" %%i in ('nvidia-smi --query-gpu=driver_version --format=csv,noheader 2^>^&1') do echo [OK] NVIDIA Driver
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
)

:: ---- CMake ----
cmake --version >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo [X] CMake - NOT FOUND
    if !HAS_WINGET!==1 (
        echo     Installing CMake via winget...
        winget install -e --id Kitware.CMake --accept-source-agreements --accept-package-agreements
        if !ERRORLEVEL!==0 (
            echo     [OK] CMake installed
            set NEED_PATH_REFRESH=1
        ) else (
            echo     [!] winget install failed — install manually: https://cmake.org/download/
            set MISSING_CRITICAL=1
        )
    ) else (
        echo     Install from: https://cmake.org/download/
        set MISSING_CRITICAL=1
    )
) else (
    for /f "tokens=3" %%i in ('cmake --version 2^>^&1 ^| findstr version') do echo [OK] CMake %%i
)

:: ---- CUDA Toolkit ----
nvcc --version >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo [X] CUDA Toolkit - NOT FOUND
    if !HAS_WINGET!==1 (
        echo     Installing CUDA Toolkit via winget ^(~3 GB, may take a while^)...
        winget install -e --id Nvidia.CUDA --accept-source-agreements --accept-package-agreements
        if !ERRORLEVEL!==0 (
            echo     [OK] CUDA Toolkit installed
            set NEED_PATH_REFRESH=1
        ) else (
            echo     [!] winget install failed
            echo     Install CUDA 12.x manually: https://developer.nvidia.com/cuda-downloads
            set MISSING_CUDA=1
        )
    ) else (
        echo     Install CUDA 12.x from: https://developer.nvidia.com/cuda-downloads
        set MISSING_CUDA=1
    )
) else (
    for /f "tokens=5" %%i in ('nvcc --version 2^>^&1 ^| findstr release') do echo [OK] CUDA Toolkit %%i
)

:: ---- Visual Studio Build Tools ----
where cl >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo [X] Visual Studio Build Tools - NOT FOUND or not in PATH
    call :try_load_vs_env
    where cl >nul 2>&1
    if !ERRORLEVEL!==0 (
        echo [OK] Visual Studio Build Tools ^(cl.exe loaded via VS environment^)
    ) else (
        if !HAS_WINGET!==1 (
            echo     Installing VS Build Tools with C++ workload via winget...
            echo     ^(This is a large download and may take 10-20 minutes^)
            winget install -e --id Microsoft.VisualStudio.2022.BuildTools --override "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --passive --wait" --accept-source-agreements --accept-package-agreements >nul 2>&1
            call :try_load_vs_env
            where cl >nul 2>&1
            if !ERRORLEVEL!==0 (
                echo     [OK] VS Build Tools ready
                set NEED_PATH_REFRESH=1
                set NEED_RESTART=1
            ) else (
                echo     [!] VS Build Tools still unavailable in this shell
                echo     Open "x64 Native Tools Command Prompt for VS 2022"
                echo     and run setup_windows.bat again.
                set MISSING_VS=1
            )
        ) else (
            echo     Install "Desktop development with C++" from:
            echo     https://visualstudio.microsoft.com/visual-cpp-build-tools/
            set MISSING_VS=1
        )
    )
) else (
    echo [OK] Visual Studio Build Tools ^(cl.exe found^)
)

echo.

:: ========================================
:: Refresh PATH if we installed anything
:: ========================================
if !NEED_PATH_REFRESH!==1 (
    echo Refreshing PATH to pick up new installations...
    for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%b"
    for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USR_PATH=%%b"
    set "PATH=!SYS_PATH!;!USR_PATH!"
    echo.
)

:: ========================================
:: Re-verify after installs
:: ========================================
if !NEED_PATH_REFRESH!==1 (
    echo Re-checking after installation...
    echo.
    set STILL_MISSING=0

    python --version >nul 2>&1
    if !ERRORLEVEL! neq 0 (
        echo [X] Python still not in PATH
        set STILL_MISSING=1
    ) else (
        for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo [OK] Python %%i
    )

    node --version >nul 2>&1
    if !ERRORLEVEL! neq 0 (
        echo [X] Node.js still not in PATH
        set STILL_MISSING=1
    ) else (
        for /f "tokens=1" %%i in ('node --version 2^>^&1') do echo [OK] Node.js %%i
    )

    cmake --version >nul 2>&1
    if !ERRORLEVEL! neq 0 (
        echo [X] CMake still not in PATH
        set STILL_MISSING=1
    ) else (
        for /f "tokens=3" %%i in ('cmake --version 2^>^&1 ^| findstr version') do echo [OK] CMake %%i
    )

    nvcc --version >nul 2>&1
    if !ERRORLEVEL! neq 0 (
        echo [  ] CUDA nvcc not yet in PATH ^(may need terminal restart^)
    ) else (
        for /f "tokens=5" %%i in ('nvcc --version 2^>^&1 ^| findstr release') do echo [OK] CUDA Toolkit %%i
    )

    echo.
    if !STILL_MISSING!==1 (
        echo =====================================================
        echo   Some tools were installed but not yet in PATH.
        echo   Close this terminal, open a NEW terminal, and
        echo   run setup_windows.bat again.
        echo =====================================================
        pause
        exit /b 1
    )
)

:: Check for hard failures (no winget + missing tools)
if defined MISSING_CRITICAL (
    echo =====================================================
    echo   ERROR: Missing required dependencies.
    echo   Install the components marked [X] above, then
    echo   run this script again.
    echo =====================================================
    pause
    exit /b 1
)

if !NEED_RESTART!==1 (
    echo =====================================================
    echo   VS Build Tools were just installed.
    echo   Please close this terminal, open:
    echo     "x64 Native Tools Command Prompt for VS 2022"
    echo   and run setup_windows.bat again.
    echo =====================================================
    pause
    exit /b 0
)

if defined MISSING_VS (
    echo =====================================================
    echo   WARNING: Visual Studio Build Tools not in PATH
    echo.
    echo   You have two options:
    echo   1. Run this script from "x64 Native Tools Command Prompt"
    echo      ^(Search for it in Start Menu after installing VS Build Tools^)
    echo.
    echo   2. Try installing pre-built wheel ^(no compilation needed^)
    echo      We'll attempt this first...
    echo =====================================================
    echo.
    set TRY_PREBUILT=1
)

if defined MISSING_CUDA (
    echo =====================================================
    echo   WARNING: CUDA Toolkit not found
    echo   Will try pre-built CUDA wheel instead...
    echo =====================================================
    echo.
    set TRY_PREBUILT=1
)

echo ========================================
echo   Setting up Backend...
echo ========================================
cd backend

:: Create virtual environment if missing
if exist venv (
    echo [OK] Virtual environment exists
) else (
    echo Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

:: Activate venv
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Check if llama-cpp-python is already installed
python -c "import llama_cpp" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [OK] llama-cpp-python already installed
    goto :install_success
)

echo.
echo ========================================
echo Installing llama-cpp-python with CUDA...
echo ========================================
echo.

echo Upgrading pip...
python -m pip install --upgrade pip

:: Try pre-built CUDA wheel first (no compilation needed!)
echo Attempting to install pre-built CUDA wheel...
echo.

pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
if %ERRORLEVEL%==0 (
    echo.
    echo [OK] Successfully installed pre-built CUDA wheel!
    goto :install_success
)

echo.
echo Pre-built wheel failed. Trying alternative wheel sources...
echo.

:: Try CUDA 12.1 wheel
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
if %ERRORLEVEL%==0 (
    echo.
    echo [OK] Successfully installed pre-built CUDA 12.1 wheel!
    goto :install_success
)

:: Try jllllll's wheels (community builds)
echo.
echo Trying community pre-built wheels...
pip install llama-cpp-python --extra-index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu124
if %ERRORLEVEL%==0 (
    echo.
    echo [OK] Successfully installed community CUDA wheel!
    goto :install_success
)

:: If pre-built wheels all failed, try building from source
echo.
echo =====================================================
echo Pre-built wheels not available for your configuration.
echo Attempting to build from source...
echo =====================================================
echo.

if defined MISSING_VS (
    echo ERROR: Cannot build from source without Visual Studio Build Tools!
    echo.
    echo Please install Visual Studio Build Tools:
    echo   1. Go to: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo   2. Download and run the installer
    echo   3. Select "Desktop development with C++" workload
    echo   4. Install and restart your computer
    echo   5. Open "x64 Native Tools Command Prompt for VS 2022"
    echo   6. Navigate to this directory and run setup_windows.bat again
    echo.
    pause
    exit /b 1
)

if defined MISSING_CUDA (
    echo ERROR: Cannot build from source without CUDA Toolkit!
    echo.
    echo Please install CUDA Toolkit 12.x:
    echo   1. Go to: https://developer.nvidia.com/cuda-downloads
    echo   2. Select Windows ^> x86_64 ^> Your Windows version
    echo   3. Download and install
    echo   4. Add CUDA to PATH:
    echo      set PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\bin;%%PATH%%
    echo   5. Restart command prompt and run setup_windows.bat again
    echo.
    pause
    exit /b 1
)

echo Building llama-cpp-python from source with CUDA...
echo This will take 10-20 minutes...
echo.

set CMAKE_ARGS=-DGGML_CUDA=on
set FORCE_CMAKE=1
pip install llama-cpp-python --force-reinstall --no-cache-dir --verbose

if %ERRORLEVEL% neq 0 (
    echo.
    echo =====================================================
    echo   ERROR: Failed to build llama-cpp-python
    echo =====================================================
    echo.
    echo Common fixes:
    echo.
    echo 1. Run from "x64 Native Tools Command Prompt for VS 2022"
    echo    ^(Search for it in Start Menu^)
    echo.
    echo 2. Make sure CUDA is in PATH:
    echo    set PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin;%%PATH%%
    echo.
    echo 3. Try installing without CUDA ^(CPU-only, slower^):
    echo    pip install llama-cpp-python
    echo.
    echo 4. Check GitHub issues:
    echo    https://github.com/abetlen/llama-cpp-python/issues
    echo.
    pause
    exit /b 1
)

:install_success
echo.
echo [OK] llama-cpp-python ready

echo Checking Python dependencies...
pip install -q --upgrade -r requirements.txt

call deactivate
cd ..
echo [OK] Backend ready
echo.

echo ========================================
echo   Setting up Frontend...
echo ========================================
cd frontend

if exist node_modules (
    echo Checking for updates...
    call npm install --prefer-offline
) else (
    echo Installing npm dependencies...
    call npm install
)

if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install frontend dependencies
    pause
    exit /b 1
)

cd ..
echo [OK] Frontend ready

:: Install tunnel tools (optional, for TUNNEL=on)
echo.
echo ========================================
echo   Setting up tunnel tools
echo ========================================

:: cloudflared
where cloudflared >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [OK] cloudflared already installed
) else (
    where choco >nul 2>&1
    if !ERRORLEVEL!==0 (
        echo Installing cloudflared via Chocolatey...
        choco install cloudflared -y
        if !ERRORLEVEL!==0 (
            echo [OK] cloudflared installed
        ) else (
            echo [SKIP] cloudflared install failed
        )
    ) else (
        where winget >nul 2>&1
        if !ERRORLEVEL!==0 (
            echo Installing cloudflared via winget...
            winget install --id Cloudflare.cloudflared --accept-source-agreements --accept-package-agreements
        ) else (
            echo [SKIP] No package manager found for cloudflared
        )
    )
)

:: localtunnel
where lt >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [OK] localtunnel already installed
) else (
    echo Installing localtunnel...
    call npm install -g localtunnel
    if !ERRORLEVEL!==0 (
        echo [OK] localtunnel installed
    ) else (
        echo [SKIP] Could not install localtunnel
    )
)

:: llama-server (required for LFM2 model family)
echo.
echo ========================================
echo   Setting up llama-server (LFM2)
echo ========================================
if not exist "llama-cpp" mkdir "llama-cpp"
if exist "llama-cpp\llama-server.exe" (
    echo [OK] llama-server already present: %CD%\llama-cpp\llama-server.exe
) else (
    echo Detecting best llama.cpp Windows bundle...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "$ErrorActionPreference='Stop';" ^
      "$api='https://api.github.com/repos/ggml-org/llama.cpp/releases/latest';" ^
      "$rel=Invoke-RestMethod -Uri $api -Headers @{ 'User-Agent'='ParleyAI-Setup' };" ^
      "$gpuName=''; $allGpus=@(); try { $allGpus=(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) } catch {};" ^
      "if ($allGpus) { $pick=$allGpus | Where-Object { $_ -match 'NVIDIA|GeForce|RTX|Quadro' } | Select-Object -First 1; if (-not $pick) { $pick=$allGpus | Select-Object -First 1 }; if ($pick) { $gpuName=$pick.ToLowerInvariant() } };" ^
      "$isNvidia = $gpuName -match 'nvidia|geforce|rtx|quadro';" ^
      "$isAmd = $gpuName -match 'amd|radeon';" ^
      "$isIntel = $gpuName -match 'intel';" ^
      "$cpuArch = (Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Architecture);" ^
      "$isX64 = $cpuArch -eq 9;" ^
      "$cudaMajor='';" ^
      "try { $nvcc=(nvcc --version 2>$null | Out-String); if ($nvcc -match 'release\s+([0-9]+)\.([0-9]+)') { $cudaMajor=$Matches[1] } } catch {};" ^
      "$preferred=@();" ^
      "if (-not $isX64) { throw 'Unsupported CPU architecture for this script: expected x64 Windows' };" ^
      "if ($isNvidia) {" ^
      "  if ($cudaMajor -eq '13') { $preferred = @('cudart-llama-bin-win-cuda-13.1-x64.zip','cudart-llama-bin-win-cuda-12.4-x64.zip') }" ^
      "  elseif ($cudaMajor -eq '12') { $preferred = @('cudart-llama-bin-win-cuda-12.4-x64.zip','cudart-llama-bin-win-cuda-13.1-x64.zip') }" ^
      "  else { $preferred = @('cudart-llama-bin-win-cuda-12.4-x64.zip','cudart-llama-bin-win-cuda-13.1-x64.zip','llama-b*-bin-win-vulkan-x64.zip','llama-b*-bin-win-cpu-x64.zip') }" ^
      "} elseif ($isAmd -or $isIntel) {" ^
      "  $preferred = @('llama-b*-bin-win-vulkan-x64.zip','llama-b*-bin-win-cpu-x64.zip')" ^
      "} else {" ^
      "  $preferred = @('llama-b*-bin-win-cpu-x64.zip','llama-b*-bin-win-vulkan-x64.zip')" ^
      "}" ^
      "$asset=$null;" ^
      "foreach ($name in $preferred) {" ^
      "  if ($name.Contains('*')) { $asset = $rel.assets | Where-Object { $_.name -like $name } | Select-Object -First 1 }" ^
      "  else { $asset = $rel.assets | Where-Object { $_.name -eq $name } | Select-Object -First 1 }" ^
      "  if ($asset) { break }" ^
      "};" ^
      "if (-not $asset) { $asset=$rel.assets | Where-Object { $_.name -match '^cudart-llama-bin-win-cuda-.*-x64\.zip$' } | Select-Object -First 1 };" ^
      "if (-not $asset) { $asset=$rel.assets | Where-Object { $_.name -match '^llama-b[0-9]+-bin-win-(cpu|vulkan|sycl|hip)-x64\.(zip|tar\.gz)$' } | Select-Object -First 1 };" ^
      "if (-not $asset) { throw 'No supported Windows binary asset found for llama.cpp release' };" ^
      "$archivePath=Join-Path '%CD%' $asset.name;" ^
      "$extractTmp=Join-Path $env:TEMP 'llama_cpp_win_extract';" ^
      "$targetDir=Join-Path '%CD%' 'llama-cpp';" ^
      "$cpuArchName = switch ($cpuArch) { 9 {'x64'} 12 {'arm64'} default {$cpuArch} };" ^
      "$cudaShown='not-detected'; if ($cudaMajor -ne '') { $cudaShown=$cudaMajor };" ^
      "Write-Host ('All GPUs: ' + (($allGpus -join ' | ')));" ^
      "Write-Host ('Selected GPU: ' + $gpuName);" ^
      "Write-Host ('CPU arch: ' + $cpuArchName);" ^
      "Write-Host ('isNvidia=' + $isNvidia + ', isAmd=' + $isAmd + ', isIntel=' + $isIntel);" ^
      "Write-Host ('CUDA major: ' + $cudaShown);" ^
      "Write-Host ('Preferred candidates: ' + ($preferred -join ', '));" ^
      "Write-Host ('Selected asset: ' + $asset.name);" ^
      "Write-Host ('Archive path: ' + $archivePath);" ^
      "Write-Host ('Install dir: ' + $targetDir);" ^
      "$expectedSize = [int64]$asset.size;" ^
      "Write-Host ('Expected size: ' + $expectedSize + ' bytes');" ^
      "$needDownload = $true;" ^
      "if (Test-Path $archivePath) {" ^
      "  try { $existingSize=(Get-Item $archivePath).Length } catch { $existingSize=0 };" ^
      "  if ($existingSize -eq $expectedSize -and $existingSize -gt 0) {" ^
      "    $needDownload=$false;" ^
      "    Write-Host ('Using existing archive (name+size match): ' + $archivePath + ' (' + $existingSize + ' bytes)')" ^
      "  } else {" ^
      "    Write-Host ('Archive mismatch, re-downloading. Existing=' + $existingSize + ' bytes, Expected=' + $expectedSize + ' bytes')" ^
      "  }" ^
      "};" ^
      "if (Test-Path $extractTmp) { Remove-Item $extractTmp -Recurse -Force };" ^
      "if (Test-Path $targetDir) { Remove-Item $targetDir -Recurse -Force };" ^
      "New-Item -ItemType Directory -Path $targetDir -Force | Out-Null;" ^
      "if ($needDownload) { Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $archivePath -UseBasicParsing };" ^
      "if ($asset.name -like '*.zip') {" ^
      "  $ok=$false;" ^
      "  try { Expand-Archive -Path $archivePath -DestinationPath $extractTmp -Force; $ok=$true } catch { Write-Host ('Expand-Archive failed: ' + $_.Exception.Message) };" ^
      "  if (-not $ok) { try { New-Item -ItemType Directory -Path $extractTmp -Force | Out-Null; tar -xf $archivePath -C $extractTmp; $ok=$true } catch { Write-Host ('tar extract failed: ' + $_.Exception.Message) } };" ^
      "  if (-not $ok) { throw ('Failed to extract zip archive: ' + $archivePath) }" ^
      "} elseif ($asset.name -like '*.tar.gz' -or $asset.name -like '*.tgz') {" ^
      "  New-Item -ItemType Directory -Path $extractTmp -Force | Out-Null; tar -xzf $archivePath -C $extractTmp" ^
      "} elseif ($asset.name -like '*.exe') {" ^
      "  Copy-Item $archivePath -Destination (Join-Path $targetDir 'llama-server.exe') -Force" ^
      "} else { throw ('Unsupported archive format: ' + $asset.name) };" ^
      "$searchRoot = if ($asset.name -like '*.exe') { $targetDir } else { $extractTmp };" ^
      "$exe=Get-ChildItem -Path $searchRoot -Recurse -File | Where-Object { $_.Name -ieq 'llama-server.exe' -or $_.Name -ieq 'llama-server' } | Select-Object -First 1;" ^
      "if (-not $exe) {" ^
      "  $exeList=(Get-ChildItem -Path $searchRoot -Recurse -File -Filter '*.exe' | Select-Object -ExpandProperty Name | Sort-Object -Unique) -join ', ';" ^
      "  throw ('llama-server executable not found. EXEs discovered: ' + $exeList)" ^
      "};" ^
      "$exeDir=Split-Path -Parent $exe.FullName;" ^
      "Get-ChildItem -Path $exeDir -File | ForEach-Object { Copy-Item $_.FullName -Destination (Join-Path $targetDir $_.Name) -Force };" ^
      "$candidateLibDirs=@($exeDir);" ^
      "Get-ChildItem -Path $searchRoot -Recurse -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'bin|lib|cuda|vulkan' } | ForEach-Object { $candidateLibDirs += $_.FullName };" ^
      "$candidateLibDirs = $candidateLibDirs | Select-Object -Unique;" ^
      "foreach ($d in $candidateLibDirs) { Get-ChildItem -Path $d -File -Filter '*.dll' -ErrorAction SilentlyContinue | ForEach-Object { Copy-Item $_.FullName -Destination (Join-Path $targetDir $_.Name) -Force } };" ^
      "Write-Host ('Downloaded asset: ' + $asset.name);" ^
      "Write-Host ('Saved archive: ' + $archivePath);" ^
      "Write-Host ('Installed in: ' + $targetDir);"
    if !ERRORLEVEL!==0 (
        echo [OK] llama-server downloaded to: %CD%\llama-cpp\
        echo     Includes llama-server.exe and required runtime files.
    ) else (
        echo [SKIP] Could not auto-download llama-server bundle
        echo       It now prints all detection parameters above.
        echo        Download manually from:
        echo        https://github.com/ggml-org/llama.cpp/releases
        echo        and extract into: .\llama-cpp\
    )
)

echo.
echo =====================================================
echo   Setup Complete!
echo =====================================================
echo.
echo Run commands based on your shell:
echo.
echo [1] CMD / x64 Native Tools Command Prompt:
echo   .\start_windows.bat
echo.
echo   :: Expose to internet
echo   set TUNNEL=on
echo   set TUNNEL_TOOL=cloudflared
echo   .\start_windows.bat
echo.
echo   :: Custom model / lower VRAM
echo   set MODEL_PATH=C:\path\to\models
echo   set QUANT=IQ2_XXS
echo   set GPU_LAYERS=20
echo   .\start_windows.bat
echo.
echo [2] Windows PowerShell:
echo   .\start_windows.bat
echo.
echo   # Expose to internet
echo   $env:TUNNEL='on'
echo   $env:TUNNEL_TOOL='cloudflared'
echo   .\start_windows.bat
echo.
echo   # Custom model / lower VRAM
echo   $env:MODEL_PATH='C:\path\to\models'
echo   $env:QUANT='IQ2_XXS'
echo   $env:GPU_LAYERS='20'
echo   .\start_windows.bat
echo.
echo Tip: CMD uses "set VAR=value", PowerShell uses "$env:VAR='value'".
echo.
echo See README.md for GPU and model recommendations.
echo.

pause
exit /b 0

:try_load_vs_env
set "VSDEV="
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" set "VSDEV=%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"
if not defined VSDEV if exist "%ProgramFiles%\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" set "VSDEV=%ProgramFiles%\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"
if not defined VSDEV if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" (
    for /f "usebackq delims=" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath 2^>nul`) do (
        if exist "%%i\Common7\Tools\VsDevCmd.bat" set "VSDEV=%%i\Common7\Tools\VsDevCmd.bat"
    )
)
if defined VSDEV (
    call "%VSDEV%" -no_logo -arch=x64 -host_arch=x64 >nul 2>&1
)
exit /b 0
