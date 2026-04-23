Option Explicit

Dim shell
Dim fso
Dim appDir
Dim pythonExe
Dim command

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

appDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = appDir

pythonExe = appDir & "\venv\Scripts\pythonw.exe"
If Not fso.FileExists(pythonExe) Then
    pythonExe = appDir & "\venv\Scripts\python.exe"
End If

If Not fso.FileExists(pythonExe) Then
    MsgBox "Python virtual environment was not found. Please install dependencies first.", vbCritical, "Video Transcriber"
    WScript.Quit 1
End If

command = """" & pythonExe & """ """ & appDir & "\run.py" & """"
shell.Run command, 0, False
