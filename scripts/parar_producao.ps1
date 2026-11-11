<#
  Para o ambiente de PRODUÇÃO do Harley Store por completo.

  1. Pede a parada ao supervisor (iniciar_producao.ps1) criando o arquivo
     logs\PARAR na pasta de produção. O supervisor roda na mesma sessão
     dos processos da produção e é o único que consegue encerrá-los quando
     a produção foi iniciada pela tarefa agendada (sessão 0 do Windows).
  2. Se sobrar algo que esta sessão consiga encerrar (produção iniciada à
     mão, por exemplo), encerra a árvore de processos da pasta de produção.
  3. Confirma que as portas 3000 e 8000 ficaram livres.

  Não use "Encerrar tarefa" no Agendador: isso mata o supervisor antes de
  ele encerrar os filhos, e um processo órfão fica segurando a porta.

  Uso:  .\scripts\parar_producao.ps1 [-Producao C:\HARLEY_PROD]
#>
param([string]$Producao = 'C:\HARLEY_PROD', [int]$EsperaSegundos = 60)
$ErrorActionPreference = 'Continue'
$portas = 3000, 8000
function Portas-Ocupadas { @(Get-NetTCPConnection -LocalPort $portas -State Listen -ErrorAction SilentlyContinue) }
function Tarefa-Rodando {
    $t = Get-ScheduledTask -TaskName 'HarleyStore-Producao' -ErrorAction SilentlyContinue
    return ($t -and $t.State -eq 'Running')
}

# 1) Pedido ao supervisor.
if ((Tarefa-Rodando) -or (Portas-Ocupadas).Count -gt 0) {
    $pastaLogs = Join-Path $Producao 'logs'
    New-Item -ItemType Directory -Force $pastaLogs | Out-Null
    Set-Content -Path (Join-Path $pastaLogs 'PARAR') -Value (Get-Date -Format s)
    for ($i = 0; $i -lt $EsperaSegundos; $i++) {
        if (-not (Tarefa-Rodando) -and (Portas-Ocupadas).Count -eq 0) { break }
        Start-Sleep -Seconds 1
    }
}

# 2) Sobras visíveis nesta sessão: processos da pasta de produção + descendentes.
$todos = @(Get-CimInstance Win32_Process)
$alvo = @{}
$pastaNorm = $Producao.TrimEnd('\')
foreach ($p in $todos) {
    if ($p.CommandLine -and $p.CommandLine.IndexOf($pastaNorm, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
        $alvo[[int]$p.ProcessId] = $true
    }
}
do {
    $novos = 0
    foreach ($p in $todos) {
        if (-not $alvo.ContainsKey([int]$p.ProcessId) -and $alvo.ContainsKey([int]$p.ParentProcessId)) {
            $alvo[[int]$p.ProcessId] = $true; $novos++
        }
    }
} while ($novos -gt 0)
$alvo.Remove($PID)  # nunca encerrar este próprio script
foreach ($id in $alvo.Keys) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
foreach ($c in Portas-Ocupadas) {
    $proc = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
    if ($proc -and $proc.ProcessName -match '^(python|pythonw|node|bun)$') {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
}
Remove-Item (Join-Path $Producao 'logs\PARAR') -ErrorAction SilentlyContinue

# 3) Confirma.
$ocupadas = @()
for ($i = 0; $i -lt 10; $i++) {
    $ocupadas = Portas-Ocupadas
    if ($ocupadas.Count -eq 0) { break }
    Start-Sleep -Seconds 1
}
if ($ocupadas.Count -gt 0) {
    Write-Warning ("Portas ainda ocupadas: " + (($ocupadas | ForEach-Object { "$($_.LocalPort) (PID $($_.OwningProcess))" }) -join ', ') +
                   ". Se o problema persistir, reinicie o notebook.")
    exit 1
}
Write-Host 'Producao parada; portas 3000 e 8000 livres.' -ForegroundColor Green
exit 0
