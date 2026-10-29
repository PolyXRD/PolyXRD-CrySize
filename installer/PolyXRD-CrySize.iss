; Inno Setup 6 script - PolyXRD CrySize REGISTERED edition installer.
; APP_VER is passed by build_setup.bat as /DAPP_VER=vX.Y.Z (from crysize/version.py).
; Payload: PyInstaller onedir output in ..\dist\PolyXRD-CrySize\ (build first!).
; Keep comments ASCII-only to stay safe under any compiler codepage.

#define MyAppName "PolyXRD CrySize"
#ifndef APP_VER
#define APP_VER "v0.0.0"
#endif

[Setup]
AppId=PolyXRD-CrySize
AppName={#MyAppName}
AppVersion={#APP_VER}
AppPublisher=PolyXRD Team
AppPublisherURL=https://github.com/PolyXRD
AppUpdatesURL=https://github.com/PolyXRD
DefaultDirName={autopf}\PolyXRD-CrySize
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE-CN
SetupIconFile=..\resources\app-icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
OutputDir=..\dist
OutputBaseFilename=PolyXRD-CrySize-{#APP_VER}-Setup
Uninstallable=yes
CloseApplications=no

[Languages]
Name: "zh"; MessagesFile: "Languages\ChineseSimplified.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\PolyXRD-CrySize\*"; DestDir: "{app}"; \
    Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\PolyXRD-CrySize.exe"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\PolyXRD-CrySize.exe"; \
    Tasks: desktopicon

[Run]
Filename: "{app}\PolyXRD-CrySize.exe"; \
    Description: "{cm:LaunchProgram,{#MyAppName}}"; \
    Flags: nowait postinstall skipifsilent
