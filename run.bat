@echo off
title Lanzador - Merli Downloader v1.0.0
echo Iniciando el Descargador Autonomo de Merli...
echo.

:: Determinar si hay un Python real instalado y funcional
set "PYTHON_EXE="

:: 1. Probar py.exe (Lanzador oficial de Python)
py -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=py"
    goto python_found
)

:: 2. Probar python.exe
python -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python"
    goto python_found
)

:: 3. Probar python3.exe
python3 -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python3"
    goto python_found
)

:: Si llegamos aqui, no hay Python real instalado (o es el alias vacio de Windows Store)
echo [INFO] No se detecto ninguna instalacion de Python en este equipo.
echo [INFO] Procediendo a descargar y configurar Python Portable automaticamente...
echo Esto permitira ejecutar la aplicacion sin instalar nada.
echo.

set "PORTABLE_DIR=%~dp0python_portable"
set "PORTABLE_ZIP=%temp%\python_portable.zip"
set "PYTHON_EXE=%PORTABLE_DIR%\python.exe"

if exist "%PYTHON_EXE%" goto python_found

echo [1/3] Creando carpeta para Python Portable...
mkdir "%PORTABLE_DIR%" >nul 2>nul

echo [2/3] Descargando Python 3.10 Portable desde python.org...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip' -OutFile '%PORTABLE_ZIP%'"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se pudo descargar Python. Verifique su conexion a Internet.
    pause
    exit /b
)

echo [3/3] Descomprimiendo archivos...
powershell -Command "Expand-Archive -Path '%PORTABLE_ZIP%' -DestinationPath '%PORTABLE_DIR%' -Force"
del "%PORTABLE_ZIP%" 2>nul

:: Habilitar soporte de librerias de terceros (pip) descomentando "import site"
set "PTH_FILE=%PORTABLE_DIR%\python310._pth"
if exist "%PTH_FILE%" (
    powershell -Command "(Get-Content '%PTH_FILE%') -replace '#import site', 'import site' | Set-Content '%PTH_FILE%'"
)

:: Descargar e instalar pip
echo [INFO] Descargando instalador de pip...
powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%PORTABLE_DIR%\get-pip.py'"
echo [INFO] Configurando gestor de paquetes pip...
"%PYTHON_EXE%" "%PORTABLE_DIR%\get-pip.py" --no-warn-script-location >nul 2>&1
del "%PORTABLE_DIR%\get-pip.py" 2>nul

:python_found
echo.
echo [OK] Python esta listo para usarse.
echo.

:: Verificar e instalar dependencias
"%PYTHON_EXE%" -c "import requests, bs4, yt_dlp" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Instalando dependencias necesarias (requests, beautifulsoup4, yt-dlp)...
    echo Esto puede tardar unos minutos, por favor espere...
    echo.
    "%PYTHON_EXE%" -m pip install requests beautifulsoup4 yt-dlp --no-warn-script-location
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] No se pudieron instalar las dependencias necesarias.
        echo Asegurese de estar conectado a Internet.
        echo.
        pause
        exit /b
    )
    echo.
    echo [OK] Dependencias instaladas con exito.
    echo.
)

:: Lanzar la aplicacion
"%PYTHON_EXE%" "%~dp0downloader.py"
if %errorlevel% neq 0 (
    echo.
    echo La aplicacion finalizo inesperadamente.
    pause
)

