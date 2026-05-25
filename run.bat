@echo off
title Lanzador - Merli Downloader v1.0.0
echo Iniciando el Descargador Autonomo de Merli...
echo.

:: 1. Verificar si Python esta instalado en el PATH
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] No se encontro Python instalado en el sistema o no esta en el PATH.
    echo.
    echo Para solucionar esto:
    echo 1. Descarga e instala Python desde: https://www.python.org/downloads/
    echo 2. DURANTE LA INSTALACION, asegurese de marcar la casilla:
    echo    "Add python.exe to PATH" o "Agregar python.exe al PATH".
    echo.
    pause
    exit /b
)

:: 2. Verificar si las dependencias estan instaladas
python -c "import requests, bs4, yt_dlp" 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Detectando que faltan librerias requeridas.
    echo Instalando dependencias de forma automatica y portable...
    echo.
    
    python -m pip install --user requests beautifulsoup4 yt-dlp
    if %errorlevel% neq 0 (
        rem Intento de respaldo si la instalacion con --user falla
        python -m pip install requests beautifulsoup4 yt-dlp
    )
    
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] No se pudieron instalar las dependencias automaticamente.
        echo Compruebe su conexion a internet y que tenga permisos adecuados.
        echo.
        pause
        exit /b
    )
    echo.
    echo [OK] Dependencias instaladas con exito. Iniciando aplicacion...
    echo.
)

:: 3. Lanzar la aplicacion
python "%~dp0downloader.py"
if %errorlevel% neq 0 (
    echo.
    echo La aplicacion se cerro de forma inesperada.
    pause
)

