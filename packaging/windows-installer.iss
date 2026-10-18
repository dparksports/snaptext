; Inno Setup script -> snaptext-setup.exe
; Requires: Inno Setup 6+ (https://jrsoftware.org/isinfo.php)
; Run after `pyinstaller snaptext.spec` produced dist\snaptext\
;
;   iscc packaging\windows-installer.iss
;
; The installer is unsigned; SmartScreen will warn on first run
; ("More info" > "Run anyway").

#define MyAppName "snaptext"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "snaptext contributors"

[Setup]
AppId={{7C1A0B64-9D3E-4F2A-8E55-snaptext0001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=snaptext-setup
Compression=lzma2/max
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Files]
Source: "..\dist\snaptext\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\snaptext.exe"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\snaptext.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"

[Messages]
FinishedLabelNoIcons=Setup has installed [name]. Open a terminal and run "snaptext" to start, or see BUILDING.md for the verify steps.
