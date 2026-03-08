# ParleyAI - Download and install llama-server (Windows)
# Called by setup_windows.bat. Uses $PSScriptRoot as repo root, $env:LLAMA_CPP_RELEASE_TAG for optional release tag.
$ErrorActionPreference = 'Stop'
$repoRoot = $PSScriptRoot
$tag = $env:LLAMA_CPP_RELEASE_TAG
$api = 'https://api.github.com/repos/ggml-org/llama.cpp/releases/latest'
if (-not [string]::IsNullOrWhiteSpace($tag)) { $api = "https://api.github.com/repos/ggml-org/llama.cpp/releases/tags/$tag" }

$gpuName = ''
$allGpus = @()
try { $allGpus = (Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) } catch {}
if ($allGpus) {
    $pick = $allGpus | Where-Object { $_ -match 'NVIDIA|GeForce|RTX|Quadro' } | Select-Object -First 1
    if (-not $pick) { $pick = $allGpus | Select-Object -First 1 }
    if ($pick) { $gpuName = $pick.ToLowerInvariant() }
}
$isNvidia = $gpuName -match 'nvidia|geforce|rtx|quadro'
$isAmd = $gpuName -match 'amd|radeon'
$isIntel = $gpuName -match 'intel'
$cpuArch = (Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Architecture)
$isX64 = $cpuArch -eq 9
$cudaMajor = ''
try {
    $nvcc = (nvcc --version 2>$null | Out-String)
    if ($nvcc -match 'release\s+([0-9]+)\.([0-9]+)') { $cudaMajor = $Matches[1] }
} catch {}

$preferred = @()
if (-not $isX64) { throw 'Unsupported CPU architecture for this script: expected x64 Windows' }
if ($isNvidia) {
    if ($cudaMajor -eq '13') { $preferred = @('llama-b*-bin-win-cuda-13.1-x64.zip','llama-b*-bin-win-cuda-12.4-x64.zip','cudart-llama-bin-win-cuda-13.1-x64.zip','cudart-llama-bin-win-cuda-12.4-x64.zip') }
    elseif ($cudaMajor -eq '12') { $preferred = @('llama-b*-bin-win-cuda-12.4-x64.zip','llama-b*-bin-win-cuda-13.1-x64.zip','cudart-llama-bin-win-cuda-12.4-x64.zip','cudart-llama-bin-win-cuda-13.1-x64.zip') }
    else { $preferred = @('llama-b*-bin-win-cuda-12.4-x64.zip','llama-b*-bin-win-cuda-13.1-x64.zip','cudart-llama-bin-win-cuda-12.4-x64.zip','cudart-llama-bin-win-cuda-13.1-x64.zip','llama-b*-bin-win-vulkan-x64.zip','llama-b*-bin-win-cpu-x64.zip') }
} elseif ($isAmd -or $isIntel) {
    $preferred = @('llama-b*-bin-win-vulkan-x64.zip','llama-b*-bin-win-cpu-x64.zip')
} else {
    $preferred = @('llama-b*-bin-win-cpu-x64.zip','llama-b*-bin-win-vulkan-x64.zip')
}

$rel = Invoke-RestMethod -Uri $api -Headers @{ 'User-Agent' = 'ParleyAI-Setup' }
$asset = $null
foreach ($name in $preferred) {
    if ($name.Contains('*')) { $asset = $rel.assets | Where-Object { $_.name -like $name } | Select-Object -First 1 }
    else { $asset = $rel.assets | Where-Object { $_.name -eq $name } | Select-Object -First 1 }
    if ($asset) { break }
}
if (-not $asset) { $asset = $rel.assets | Where-Object { $_.name -match '^llama-b[0-9]+-bin-win-cuda-(12\.4|13\.1)-x64\.zip$' } | Select-Object -First 1 }
if (-not $asset) { $asset = $rel.assets | Where-Object { $_.name -match '^cudart-llama-bin-win-cuda-.*-x64\.zip$' } | Select-Object -First 1 }
if (-not $asset) { $asset = $rel.assets | Where-Object { $_.name -match '^llama-b[0-9]+-bin-win-(cpu|vulkan|sycl|hip)-x64\.(zip|tar\.gz)$' } | Select-Object -First 1 }
if (-not $asset) { throw 'No supported Windows binary asset found for llama.cpp release' }

$archivePath = Join-Path $repoRoot $asset.name
$extractTmp = Join-Path $env:TEMP 'llama_cpp_win_extract'
$targetDir = Join-Path $repoRoot 'llama-cpp'
$cpuArchName = switch ($cpuArch) { 9 { 'x64' } 12 { 'arm64' } default { $cpuArch } }
$cudaShown = if ($cudaMajor -ne '') { $cudaMajor } else { 'not-detected' }

Write-Host ('All GPUs: ' + (($allGpus -join ' | ')))
Write-Host ('Selected GPU: ' + $gpuName)
Write-Host ('CPU arch: ' + $cpuArchName)
Write-Host ('isNvidia=' + $isNvidia + ', isAmd=' + $isAmd + ', isIntel=' + $isIntel)
Write-Host ('CUDA major: ' + $cudaShown)
Write-Host ('Preferred candidates: ' + ($preferred -join ', '))
Write-Host ('Selected asset: ' + $asset.name)
if (-not [string]::IsNullOrWhiteSpace($tag)) { Write-Host ('Release tag override: ' + $tag) } else { Write-Host 'Release tag override: latest' }
Write-Host ('Archive path: ' + $archivePath)
Write-Host ('Install dir: ' + $targetDir)
$expectedSize = [int64]$asset.size
Write-Host ('Expected size: ' + $expectedSize + ' bytes')
$needDownload = $true
if (Test-Path $archivePath) {
    try { $existingSize = (Get-Item $archivePath).Length } catch { $existingSize = 0 }
    if ($existingSize -eq $expectedSize -and $existingSize -gt 0) {
        $needDownload = $false
        Write-Host ('Using existing archive (name+size match): ' + $archivePath + ' (' + $existingSize + ' bytes)')
    } else {
        Write-Host ('Archive mismatch, re-downloading. Existing=' + $existingSize + ' bytes, Expected=' + $expectedSize + ' bytes')
    }
}
if (Test-Path $extractTmp) { Remove-Item $extractTmp -Recurse -Force }
if (Test-Path $targetDir) { Remove-Item $targetDir -Recurse -Force }
New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
if ($needDownload) {
    Write-Host ('Downloading ' + [math]::Round($expectedSize/1MB,1) + ' MB ...')
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $archivePath -UseBasicParsing
    Write-Host 'Download complete.'
}
Write-Host ('Extracting: ' + $archivePath + ' (' + [math]::Round((Get-Item $archivePath).Length/1MB,1) + ' MB)')
New-Item -ItemType Directory -Path $extractTmp -Force | Out-Null
if ($asset.name -like '*.zip') {
    $ok = $false
    $errs = @()
    if (-not $ok) {
        try {
            $p = Start-Process -FilePath 'tar' -ArgumentList @('-xf',$archivePath,'-C',$extractTmp) -Wait -PassThru -NoNewWindow
            if ($p.ExitCode -eq 0) { $ok = $true; Write-Host 'Extracted via: tar' } else { $errs += ('tar exit code ' + $p.ExitCode) }
        } catch { $errs += ('tar: ' + $_.Exception.Message) }
    }
    if (-not $ok) {
        try {
            $p = Start-Process -FilePath 'python' -ArgumentList @('-c','import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])',$archivePath,$extractTmp) -Wait -PassThru -NoNewWindow
            if ($p.ExitCode -eq 0) { $ok = $true; Write-Host 'Extracted via: python zipfile' } else { $errs += ('python zipfile exit code ' + $p.ExitCode) }
        } catch { $errs += ('python zipfile: ' + $_.Exception.Message) }
    }
    if (-not $ok) {
        foreach ($e in $errs) { Write-Host ('  FAIL: ' + $e) }
        throw ('All extraction methods failed for: ' + $archivePath)
    }
} elseif ($asset.name -like '*.tar.gz' -or $asset.name -like '*.tgz') {
    New-Item -ItemType Directory -Path $extractTmp -Force | Out-Null
    tar -xzf $archivePath -C $extractTmp
} elseif ($asset.name -like '*.exe') {
    Copy-Item $archivePath -Destination (Join-Path $targetDir 'llama-server.exe') -Force
} else {
    throw ('Unsupported archive format: ' + $asset.name)
}
$searchRoot = if ($asset.name -like '*.exe') { $targetDir } else { $extractTmp }
$exe = Get-ChildItem -Path $searchRoot -Recurse -File | Where-Object { $_.Name -ieq 'llama-server.exe' -or $_.Name -ieq 'llama-server' } | Select-Object -First 1
if (-not $exe) {
    $exeList = (Get-ChildItem -Path $searchRoot -Recurse -File -Filter '*.exe' | Select-Object -ExpandProperty Name | Sort-Object -Unique) -join ', '
    throw ('llama-server executable not found. EXEs discovered: ' + $exeList)
}
$exeDir = Split-Path -Parent $exe.FullName
Get-ChildItem -Path $exeDir -File | ForEach-Object { Copy-Item $_.FullName -Destination (Join-Path $targetDir $_.Name) -Force }
$candidateLibDirs = @($exeDir)
Get-ChildItem -Path $searchRoot -Recurse -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'bin|lib|cuda|vulkan' } | ForEach-Object { $candidateLibDirs += $_.FullName }
$candidateLibDirs = $candidateLibDirs | Select-Object -Unique
foreach ($d in $candidateLibDirs) {
    Get-ChildItem -Path $d -File -Filter '*.dll' -ErrorAction SilentlyContinue | ForEach-Object { Copy-Item $_.FullName -Destination (Join-Path $targetDir $_.Name) -Force }
}
Write-Host ('Downloaded asset: ' + $asset.name)
Write-Host ('Saved archive: ' + $archivePath)
Write-Host ('Installed in: ' + $targetDir)
