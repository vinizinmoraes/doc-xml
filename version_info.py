# Version info for Windows executable
# This file is used by PyInstaller for Windows executable metadata

from PyInstaller.utils.win32.versioninfo import (
    VSVersionInfo,
    FixedFileInfo,
    StringFileInfo,
    StringTable,
    StringStruct,
    VarFileInfo,
    VarStruct
)

VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1, 0, 0, 0),
        prodvers=(1, 0, 0, 0),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo([
            StringTable(
                '040904B0',
                [
                    StringStruct('CompanyName', 'XML Watcher Service'),
                    StringStruct('FileDescription', 'Monitors folders for XML files and uploads to API'),
                    StringStruct('FileVersion', '1.0.0.0'),
                    StringStruct('InternalName', 'xml-watcher'),
                    StringStruct('LegalCopyright', 'Copyright (c) 2024'),
                    StringStruct('OriginalFilename', 'xml-watcher.exe'),
                    StringStruct('ProductName', 'XML Watcher Service'),
                    StringStruct('ProductVersion', '1.0.0.0')
                ]
            )
        ]),
        VarFileInfo([VarStruct('Translation', [1033, 1200])])
    ]
)
