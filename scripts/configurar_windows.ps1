<#
  Configura o Windows do notebook servidor para o Harley Store ficar no ar
  durante o expediente. PRECISA SER EXECUTADO COMO ADMINISTRADOR.
  Pode ser executado de novo sem duplicar nada.

  1. Rede Wi-Fi atual como Privada.
  2. Nunca suspender/hibernar na tomada (na bateria continua 10 min).
  3. Fechar a tampa na tomada: não fazer nada.
  4. Horário ativo do Windows Update: 7h às 19h (reinícios só à noite).
  5. Firewall: libera TCP 3000 e 8000 apenas no perfil Privado.
  6. Tarefa agendada "HarleyStore-Producao": inicia a produção quando o
     notebook liga, sem precisar entrar na conta.

  Uso (PowerShell como administrador):
      .\scripts\configurar_windows.ps1 -Usuario "$env:COMPUTERNAME\$env:USERNAME"
#>
param(
    [Parameter(Mandatory)] [string]$Usuario,
    [string]$Producao = 'C:\HARLEY_PROD',
    [string]$Log
)
$ErrorActionPreference = 'Stop'
if (-not $Log) { $Log = Join-Path (Split-Path $PSScriptRoot -Parent) 'logs\configurar_windows.log' }
New-Item -ItemType Directory -Force (Split-Path $Log) | Out-Null
Set-Content -Path $Log -Encoding utf8 -Value ("configurar_windows {0:yyyy-MM-dd HH:mm:ss} usuario={1}" -f (Get-Date), $Usuario)
function Registrar($texto) { Add-Content -Path $Log -Encoding utf8 -Value $texto; Write-Host $texto }
function Passo($nome, [scriptblock]$acao) {
    try { & $acao; Registrar "OK    $nome" }
    catch { Registrar "FALHA $nome :: $($_.Exception.Message)" }
}

$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { Registrar 'FALHA este script precisa ser executado como administrador.'; exit 1 }

Passo '1 rede Wi-Fi como Privada' {
    Get-NetConnectionProfile | Where-Object { $_.InterfaceAlias -eq 'Wi-Fi' } |
        Set-NetConnectionProfile -NetworkCategory Private
}

Passo '2 nunca suspender/hibernar na tomada' {
    powercfg /change standby-timeout-ac 0
    powercfg /change hibernate-timeout-ac 0
    if ($LASTEXITCODE -ne 0) { throw "powercfg retornou $LASTEXITCODE" }
}

Passo '3 tampa fechada na tomada: nao fazer nada' {
    powercfg /setacvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION 0
    powercfg /setactive SCHEME_CURRENT
    if ($LASTEXITCODE -ne 0) { throw "powercfg retornou $LASTEXITCODE" }
}

Passo '4 horario ativo do Windows Update 7h-19h' {
    $chave = 'HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings'
    New-Item -Path $chave -Force | Out-Null
    Set-ItemProperty -Path $chave -Name ActiveHoursStart -Type DWord -Value 7
    Set-ItemProperty -Path $chave -Name ActiveHoursEnd -Type DWord -Value 19
    # desliga o "ajustar automaticamente conforme o uso", que sobrescreveria 7h-19h
    Set-ItemProperty -Path $chave -Name SmartActiveHoursState -Type DWord -Value 0
}

Passo '5 firewall TCP 3000/8000 somente perfil Privado' {
    $nome = 'Harley Store - producao (TCP 3000, 8000)'
    Get-NetFirewallRule -DisplayName $nome -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    New-NetFirewallRule -DisplayName $nome -Direction Inbound -Protocol TCP -LocalPort 3000, 8000 `
        -Action Allow -Profile Private -Description 'Acesso dos funcionarios ao Harley Store na rede da loja' | Out-Null
}

Passo '6 tarefa agendada HarleyStore-Producao' {
    $script = Join-Path $Producao 'scripts\iniciar_producao.ps1'
    $acao = New-ScheduledTaskAction -Execute 'powershell.exe' -WorkingDirectory $Producao `
        -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$script`""
    $gatilho = New-ScheduledTaskTrigger -AtStartup
    $gatilho.Delay = 'PT30S'   # dá tempo do Wi-Fi conectar
    $principal = New-ScheduledTaskPrincipal -UserId $Usuario -LogonType S4U -RunLevel Limited
    $config = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -StartWhenAvailable -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName 'HarleyStore-Producao' -Action $acao -Trigger $gatilho `
        -Principal $principal -Settings $config -Force `
        -Description 'Inicia o Harley Store (producao) quando o notebook liga' | Out-Null
}

Registrar 'FIM'
