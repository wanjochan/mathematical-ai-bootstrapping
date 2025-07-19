# PowerShell script to start client in another user session
# Run this as administrator

param(
    [Parameter(Mandatory=$true)]
    [string]$Username,
    
    [Parameter(Mandatory=$true)]
    [string]$Password,
    
    [string]$ServerIP = "localhost"
)

# Create secure credential
$SecurePassword = ConvertTo-SecureString $Password -AsPlainText -Force
$Credential = New-Object System.Management.Automation.PSCredential ($Username, $SecurePassword)

# Start the client in the target user session
$ScriptBlock = {
    param($ServerIP)
    
    # Set environment variable for server connection
    $env:CYBERCORP_SERVER = "ws://${ServerIP}:8888"
    
    # Change to CyberCorp directory
    Set-Location "C:\CyberCorp"
    
    # Start the client
    & python client.py
}

# Create a scheduled task to run in the user session
$TaskName = "CyberCorpClient_$Username"

# Remove existing task if present
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# Create task action
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -Command `"& {Set-Location 'C:\CyberCorp'; python client.py}`""

# Create task trigger (start immediately)
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(5)

# Create task settings
$Settings = New-ScheduledTaskSettings -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register the task
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -User $Username -Password $Password -RunLevel Limited

# Start the task
Start-ScheduledTask -TaskName $TaskName

Write-Host "CyberCorp client started for user: $Username"
Write-Host "The client should connect to the server at ${ServerIP}:8888"
Write-Host ""
Write-Host "To stop the client, run:"
Write-Host "  Stop-ScheduledTask -TaskName $TaskName"
Write-Host "  Unregister-ScheduledTask -TaskName $TaskName -Confirm:`$false"