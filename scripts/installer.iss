[Setup]
AppId={{7A122C49-A049-4CE2-A0A4-BD947A3A8095}
AppName=VEX AI Video Generator
AppVersion=0.1.0
DefaultDirName={localappdata}\Programs\VEXVideo
DefaultGroupName=VEX Video
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist\installer
OutputBaseFilename=VEXVideo-0.1.0-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\VEXVideo.exe

[Files]
Source: "..\dist\VEXVideo\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\VEX Video"; Filename: "{app}\VEXVideo.exe"
Name: "{autodesktop}\VEX Video"; Filename: "{app}\VEXVideo.exe"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Masaüstü kısayolu oluştur"; Flags: unchecked

[Run]
Filename: "{app}\VEXVideo.exe"; Description: "VEX Video uygulamasını aç"; Flags: nowait postinstall skipifsilent
