Unicode True
!include "MUI2.nsh"
!include "WinMessages.nsh"

Name "Chimpi3D 0.3.0"
OutFile "Chimpi3D-Setup-Windows.exe"
InstallDir "$LOCALAPPDATA\Programs\Chimpi3D"
RequestExecutionLevel user
SetCompressor /SOLID lzma

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "PortugueseBR"

Section "Instalar" SEC01
  SetOutPath "$INSTDIR"
  File "dist\Chimpi3D.exe"
  File "dist\of.exe"
  WriteUninstaller "$INSTDIR\Desinstalar.exe"
  CreateDirectory "$SMPROGRAMS\Chimpi3D"
  CreateShortcut "$SMPROGRAMS\Chimpi3D\Chimpi3D.lnk" "$INSTDIR\Chimpi3D.exe"
  CreateShortcut "$SMPROGRAMS\Chimpi3D\Desinstalar.lnk" "$INSTDIR\Desinstalar.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Chimpi3D" "DisplayName" "Chimpi3D 0.3.0"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Chimpi3D" "UninstallString" '"$INSTDIR\Desinstalar.exe"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Chimpi3D" "InstallLocation" "$INSTDIR"

  ; Inclui o comando 'of' no PATH do usuário, sem exigir administrador
  ReadRegStr $0 HKCU "Environment" "Path"
  ; Procura a pasta no PATH sem dependências de macros externas
  StrLen $2 "$INSTDIR"
  StrLen $3 "$0"
  StrCpy $4 0
path_procurar:
  IntCmp $4 $3 path_append path_comparar path_append
path_comparar:
  StrCpy $1 $0 $2 $4
  StrCmp $1 "$INSTDIR" path_done
  IntOp $4 $4 + 1
  Goto path_procurar
  StrCmp $0 "" 0 path_append
  WriteRegExpandStr HKCU "Environment" "Path" "$INSTDIR"
  Goto path_done
path_append:
  WriteRegExpandStr HKCU "Environment" "Path" "$0;$INSTDIR"
path_done:
  System::Call 'USER32::SendMessageTimeout(p 0xffff, i ${WM_SETTINGCHANGE}, p 0, t "STR:Environment", i 0x2, i 5000, *p .r0)'
SectionEnd

Section "Desinstalar"
  Delete "$INSTDIR\Chimpi3D.exe"
  Delete "$INSTDIR\of.exe"
  Delete "$INSTDIR\Desinstalar.exe"
  RMDir "$INSTDIR"
  Delete "$SMPROGRAMS\Chimpi3D\Chimpi3D.lnk"
  Delete "$SMPROGRAMS\Chimpi3D\Desinstalar.lnk"
  RMDir "$SMPROGRAMS\Chimpi3D"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Chimpi3D"
  ; Não altera outros aplicativos no PATH do usuário
SectionEnd
