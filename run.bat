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
echo [ERROR] necesitas tener instalado Python , instalalo y inicia de nuevo el Run
echo.
echo Redireccionando a la pagina oficial de descargas de Python...
start https://www.python.org/downloads/
echo.
pause
exit /b

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

