Set WshShell = WScript.CreateObject("WScript.Shell")
If WScript.Arguments.Count > 0 Then
    CmdToRun = ""
    For i = 0 To WScript.Arguments.Count - 1
        If InStr(WScript.Arguments(i), " ") > 0 Then
            CmdToRun = CmdToRun & """" & WScript.Arguments(i) & """ "
        Else
            CmdToRun = CmdToRun & WScript.Arguments(i) & " "
        End If
    Next
    ' 0 means hide the window, False means do not wait for command to complete
    WshShell.Run Trim(CmdToRun), 0, False
End If