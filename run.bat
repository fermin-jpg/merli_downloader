@echo off
title Lanzador - Merli Downloader v1.0.0
echo Iniciando el Descargador Autonomo de Merli...
echo.

:: Determinar si hay un Python real instalado y funcional
set "PYTHON_EXE="

echo [1/4] Buscando interprete de Python...
:: 1. Probar py.exe (Lanzador oficial de Python)
py -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=py"
    echo     - Detectado: py.exe
    goto python_found
)

:: 2. Probar python.exe
python -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python"
    echo     - Detectado: python.exe
    goto python_found
)

:: 3. Probar python3.exe
python3 -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python3"
    echo     - Detectado: python3.exe
    goto python_found
)

:: Si no se encontro ningun Python valido
echo [ERROR] necesitas tener instalado Python , instalalo y inicia de nuevo el Run
echo.
set /p "RESPUESTA=Quieres que te redirijamos a la pagina de descarga de Python? (S/N): "
if /i "%RESPUESTA%"=="S" (
    echo.
    echo Abriendo la pagina oficial de Python en tu navegador...
    start https://www.python.org/downloads/
    echo Una vez instalado Python, vuelve a ejecutar el Run.bat
) else (
    echo.
    echo Recuerda instalar Python manualmente desde: https://www.python.org/downloads/
)
echo.
pause
exit /b

:python_found
echo.
echo [2/4] Verificando librerias instaladas...
echo     - Comprobando modulos: requests, bs4, yt_dlp...
"%PYTHON_EXE%" -c "import requests; print('      * requests: OK'); import bs4; print('      * bs4: OK'); import yt_dlp; print('      * yt_dlp: OK')" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [3/4] Instalando librerias faltantes...
    echo     - Ejecutando: %PYTHON_EXE% -m pip install requests beautifulsoup4 yt-dlp
    "%PYTHON_EXE%" -m pip install requests beautifulsoup4 yt-dlp --no-warn-script-location
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] No se pudieron instalar las dependencias necesarias.
        echo Asegurese de estar conectado a Internet.
        echo.
        pause
        exit /b
    )
    echo [OK] Dependencias instaladas con exito.
    echo.
) else (
    echo     - Todas las librerias estan presentes.
)

echo.
echo [4/4] Lanzando la aplicacion grafica...
echo     - Ejecutando: %PYTHON_EXE% "%~dp0downloader.py"
echo.

"%PYTHON_EXE%" "%~dp0downloader.py"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] La aplicacion finalizo inesperadamente (Codigo de salida: %errorlevel%).
    pause
)

