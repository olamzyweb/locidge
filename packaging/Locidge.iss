#define MyAppName "Locidge"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Locidge"
#define MyAppExeName "Locidge.exe"

[Setup]
AppId={{A5A743D3-6C63-4CF0-BF43-1C221DBE0A2E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=Locidge-Installer
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
SetupIconFile=locidge.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "..\dist\Locidge.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "locidge.ico"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\uploads"

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\locidge.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\locidge.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
