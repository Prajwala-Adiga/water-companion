#define AppName "Fahadh Water Companion"
#ifndef AppVersion
  #error AppVersion must be supplied by BUILD_RELEASE.bat
#endif
#define AppPublisher "Prajwala Adiga"
#define AppExeName "FahadhWaterCompanion.exe"

[Setup]
AppId={{C30E3193-A262-4AF5-9B91-522A07AA97C9}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\FahadhWaterCompanion
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=release
OutputBaseFilename=FahadhWaterCompanion-Setup-{#AppVersion}
SetupIconFile=assets\fahadh.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
SetupLogging=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional options:"
Name: "startup"; Description: "Start quietly when I sign in to Windows"; GroupDescription: "Additional options:"

[Files]
Source: "dist\FahadhWaterCompanion\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: startup

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
