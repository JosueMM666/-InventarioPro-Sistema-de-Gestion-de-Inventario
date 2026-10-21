@echo off
setlocal
cd /d "%~dp0"
echo ===========================================
echo  InventarioPro - Preparacion de ejecutable
echo ===========================================
py -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo ERROR instalando dependencias.
  pause
  exit /b 1
)
python -m PyInstaller --noconfirm --clean --windowed --onedir --name InventarioPro inventario_pro.py
if errorlevel 1 (
  echo.
  echo ERROR creando el ejecutable.
  pause
  exit /b 1
)
echo.
echo Ejecutable creado en: dist\InventarioPro\InventarioPro.exe
echo Copia y distribuye la carpeta completa dist\InventarioPro.
pause
