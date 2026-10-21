; Plantilla opcional para Inno Setup. Primero ejecuta crear_ejecutable_windows.bat.
#define MyAppName "InventarioPro"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "InventarioPro"
#define MyAppExeName "InventarioPro.exe"

[Setup]
AppId={{8B2A5F9D-5C6D-4E15-8A61-0E9E8E7B1001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\InventarioPro
DefaultGroupName={#MyAppName}
OutputDir=installer_output
OutputBaseFilename=InventarioPro-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Files]
Source: "dist\InventarioPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"
