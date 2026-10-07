Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
scriptPath = currentDir & "\ets2_radio_proxy.py"
WshShell.CurrentDirectory = currentDir
WshShell.Run """D:\Anaconda\pythonw.exe"" """ & scriptPath & """", 0, False
