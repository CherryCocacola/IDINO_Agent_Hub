 = @(
    "C:\inetpub\wwwroot\AIUIUX\index.html",
    "C:\inetpub\wwwroot\AIUIUX\models.html",
    "C:\inetpub\wwwroot\AIUIUX\monitoring.html",
    "C:\inetpub\wwwroot\AIUIUX\apikeys.html",
    "C:\inetpub\wwwroot\AIUIUX\users.html",
    "C:\inetpub\wwwroot\AIUIUX\settings.html"
)

 = "    <a href=""models.html"" class=""nav-item"">"
 = "    <a href=""chat.html"" class=""nav-item""><i class=""fas fa-comments""></i><span>AI 채팅</span><span class=""nav-badge nav-badge-new"">NEW</span></a>"
 =  + [System.Environment]::NewLine + 

foreach ( in ) {
     = [System.IO.File]::ReadAllText(, [System.Text.Encoding]::UTF8)
    if (.Contains()) {
         = .Replace(, )
        [System.IO.File]::WriteAllText(, , (New-Object System.Text.UTF8Encoding ))
        Write-Output "SUCCESS: "
    } else {
        Write-Output "NOT FOUND (pattern missing): "
    }
}
