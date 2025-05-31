[Setup]
AppName=SQL Metadata Viewer
AppVersion=1.0
DefaultDirName={pf}\SQLMetadataViewer
DefaultGroupName=SQL Metadata Viewer
OutputDir=dist
OutputBaseFilename=SQLMetadataViewerInstaller
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\SQLMetadataViewer.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SQL Metadata Viewer"; Filename: "{app}\SQLMetadataViewer.exe"
Name: "{userdesktop}\SQL Metadata Viewer"; Filename: "{app}\SQLMetadataViewer.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"
