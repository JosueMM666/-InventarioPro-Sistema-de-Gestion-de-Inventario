# InventarioPro — Sistema de inventarios de escritorio

## Funciones incluidas
- Panel con conteo de productos, unidades, valor a costo y stock bajo.
- Catálogo con SKU único, código de barras, nombre, categoría, proveedor, costo, precio, stock mínimo y ubicación.
- Alta, edición y búsqueda de productos.
- Entradas, salidas y ajustes de inventario con historial.
- Prevención de salidas superiores al stock disponible.
- Exportación del catálogo a CSV compatible con Excel.
- Respaldo manual de la base de datos SQLite.
- Persistencia de datos en `%LOCALAPPDATA%\InventarioPro\inventario.db`.

## Requisitos para desarrollar
- Windows 10/11
- Python 3.10 o superior
- Visual Studio Code (opcional)

## Ejecutar desde VS Code
1. Abre esta carpeta en VS Code.
2. Abre Terminal > Nueva terminal.
3. Ejecuta:
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   python inventario_pro.py
   ```
4. Si PowerShell bloquea la activación, ejecuta directamente:
   ```powershell
   .venv\Scripts\python.exe inventario_pro.py
   ```

## Crear ejecutable
Haz doble clic en `crear_ejecutable_windows.bat` o ejecútalo desde CMD. Al finalizar, encontrarás:
`dist\InventarioPro\InventarioPro.exe`

Distribuye **la carpeta completa** `dist\InventarioPro`, no solo el `.exe`, porque se usa el modo `--onedir` para una distribución más fácil de diagnosticar y mantener.

## Datos y respaldos
La base de datos se guarda por usuario de Windows en:
`%LOCALAPPDATA%\InventarioPro\inventario.db`

Por eso, actualizar o reinstalar el programa no debería borrar los datos. Aun así, crea respaldos periódicos desde el botón del panel principal. El respaldo debe guardarse fuera del equipo para protegerlo ante fallos del disco.

## Alcance y siguientes mejoras recomendadas para una tienda grande
Esta versión es una base funcional de escritorio, adecuada para validar el flujo de inventario. Antes de usarla como sistema crítico de una tienda grande, conviene agregar:
- usuarios, contraseñas, roles y bitácora de auditoría;
- base de datos centralizada (PostgreSQL o SQL Server) para varias cajas/almacenes simultáneos;
- sucursales, transferencias, compras, proveedores y órdenes de compra;
- lectores de códigos de barras y pruebas con el hardware real;
- importación masiva desde Excel/CSV;
- reportes por fechas, márgenes, rotación y valoración;
- respaldos automáticos, migraciones y pruebas de recuperación;
- instalador firmado y pruebas en Windows limpio.

No se incluye facturación fiscal, punto de venta, sincronización entre equipos ni control multiusuario en red en esta primera versión.
