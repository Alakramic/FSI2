# play.ps1 - Windows PowerShell Launcher para SGAF
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsList
)

$argString = if ($ArgsList) { $ArgsList -join " " } else { "" }
wsl.exe -d Ubuntu-24.04 bash -c "cd /home/alakramic/2026/FSI2 && ./play.sh $argString"
