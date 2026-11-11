<#
  Fixa (ou volta ao automático) o IP do Wi-Fi deste notebook, que é o
  servidor do Harley Store. PRECISA SER EXECUTADO COMO ADMINISTRADOR.

  Por quê: sem IP fixo o modem pode dar outro endereço ao notebook depois de
  reiniciar, e os aparelhos da loja deixam de achar o sistema. O ideal é a
  reserva no modem (DHCP); este script é a alternativa sem mexer no modem.

  ATENÇÃO: com IP fixo, este notebook NÃO conecta direito em outras redes
  Wi-Fi (casa, celular). Para usar fora da loja, rode com -Automatico, e
  com -Fixo de novo ao voltar.

  Uso (PowerShell como administrador):
      .\scripts\ip_do_servidor.ps1 -Fixo          # 192.168.0.12 (padrão)
      .\scripts\ip_do_servidor.ps1 -Automatico    # volta ao DHCP

  Se trocar o IP, ajuste também C:\HARLEY_PROD\producao.local.ps1 e rode
  .\scripts\atualizar_producao.ps1.
#>
param(
    [switch]$Fixo,
    [switch]$Automatico,
    [string]$IP = '192.168.0.12',
    [string]$Mascara = '255.255.255.0',
    [string]$Gateway = '192.168.0.1',
    [string[]]$DNS = @('181.213.132.2', '181.213.132.3', '8.8.8.8'),
    [string]$Adaptador = 'Wi-Fi',
    [string]$Log
)
$ErrorActionPreference = 'Continue'
if (-not $Log) { $Log = Join-Path (Split-Path $PSScriptRoot -Parent) 'logs\ip_do_servidor.log' }
New-Item -ItemType Directory -Force (Split-Path $Log) | Out-Null
function Registrar($texto) { Add-Content -Path $Log -Encoding utf8 -Value ("{0:yyyy-MM-dd HH:mm:ss} {1}" -f (Get-Date), $texto); Write-Host $texto }

$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { Registrar 'FALHA este script precisa ser executado como administrador.'; exit 1 }
if ($Fixo -eq $Automatico) { Registrar 'FALHA use -Fixo ou -Automatico.'; exit 1 }

function Voltar-Automatico {
    netsh interface ipv4 set address name="$Adaptador" source=dhcp | Out-Null
    netsh interface ipv4 set dnsservers name="$Adaptador" source=dhcp | Out-Null
}

if ($Automatico) {
    Voltar-Automatico
    Start-Sleep -Seconds 8
    Registrar "OK    $Adaptador em modo automatico (DHCP): $((Get-NetIPAddress -InterfaceAlias $Adaptador -AddressFamily IPv4 -ErrorAction SilentlyContinue).IPAddress)"
    exit 0
}

Registrar "fixando $Adaptador em $IP (gateway $Gateway)"
netsh interface ipv4 set address name="$Adaptador" static $IP $Mascara $Gateway 1 | Out-Null
netsh interface ipv4 set dnsservers name="$Adaptador" static $DNS[0] primary validate=no | Out-Null
for ($i = 1; $i -lt $DNS.Count; $i++) {
    netsh interface ipv4 add dnsservers name="$Adaptador" $DNS[$i] index=($i + 1) validate=no | Out-Null
}

# Confere: alcança o modem e a internet? Se não, volta ao automático.
$ok = $false
for ($t = 0; $t -lt 10 -and -not $ok; $t++) {
    Start-Sleep -Seconds 3
    $ok = (Test-Connection -ComputerName $Gateway -Count 1 -Quiet) -and
          (Test-Connection -ComputerName 8.8.8.8 -Count 1 -Quiet)
}
if (-not $ok) {
    Voltar-Automatico
    Registrar "FALHA sem conexao com IP fixo $IP; voltei ao automatico (DHCP)."
    exit 1
}
Registrar "OK    $Adaptador com IP fixo $IP, modem e internet respondendo."
exit 0
