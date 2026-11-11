<#
  Inicia e SUPERVISIONA o ambiente de PRODUÇÃO do Harley Store (o que os
  funcionários usam).

  Executado automaticamente pela tarefa agendada "HarleyStore-Producao"
  quando o notebook liga. Fica em execução enquanto o sistema estiver no ar.

  Por que é um supervisor: a tarefa agendada roda numa sessão separada do
  Windows (sessão 0), e os processos criados lá não podem ser encerrados
  pelo usuário comum ("Acesso negado"). Por isso quem encerra a produção é
  este próprio script: o parar_producao.ps1 só cria o arquivo de pedido
  logs\PARAR, e este script, ao vê-lo, encerra toda a sua árvore de processos.

  Lê o endereço de rede do arquivo producao.local.ps1, que fica na raiz da
  pasta de produção e NÃO vai para o git. Conteúdo esperado:

      $EnderecoProducao = '192.168.0.54'

  A saída do Reflex vai para logs\producao-AAAAMMDD.log.
#>
$ErrorActionPreference = 'Stop'
$raiz = Split-Path $PSScriptRoot -Parent
Set-Location $raiz

$arquivoLocal = Join-Path $raiz 'producao.local.ps1'
if (-not (Test-Path $arquivoLocal)) {
    Write-Error ("Arquivo producao.local.ps1 nao encontrado em $raiz. " +
                 "Crie-o com a linha:  `$EnderecoProducao = '<IP reservado do notebook>'")
    exit 1
}
$EnderecoProducao = $null
. $arquivoLocal
if (-not $EnderecoProducao) {
    Write-Error "producao.local.ps1 nao define `$EnderecoProducao."
    exit 1
}

# Em produção o Reflex inicia o backend chamando o executável "granian" pelo
# nome; na tarefa agendada o .venv não está no PATH, então é incluído aqui.
$env:PATH = (Join-Path $raiz '.venv\Scripts') + ';' + $env:PATH

$env:REFLEX_API_URL       = "http://${EnderecoProducao}:8000"
$env:REFLEX_DEPLOY_URL    = "http://${EnderecoProducao}:3000"
$env:REFLEX_FRONTEND_PORT = '3000'
$env:REFLEX_BACKEND_PORT  = '8000'
Remove-Item Env:\REFLEX_BACKEND_HOST -ErrorAction SilentlyContinue  # padrao 0.0.0.0

# UTF-8 em toda a saída do Python. Sem isto, quando o Next.js escreve uma
# mensagem com símbolo especial (ex.: "⨯"), o Reflex falha ao repassá-la para
# o log (codificação cp1252 do Windows) e a TELA cai, com o backend vivo.
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

$pastaLogs = Join-Path $raiz 'logs'
New-Item -ItemType Directory -Force $pastaLogs | Out-Null
$log = Join-Path $pastaLogs ("producao-{0:yyyyMMdd}.log" -f (Get-Date))
$pedidoParada = Join-Path $pastaLogs 'PARAR'
Remove-Item $pedidoParada -ErrorAction SilentlyContinue   # pedido antigo não vale
# O supervisor escreve num log PRÓPRIO: o arquivo do Reflex fica aberto para
# escrita pelo cmd, e gravar nele daqui falharia com "arquivo em uso".
# Uma falha de log nunca pode interromper a supervisão.
$logSupervisor = Join-Path $pastaLogs ("supervisor-{0:yyyyMMdd}.log" -f (Get-Date))
function Registrar($texto) {
    try { Add-Content -Path $logSupervisor -Encoding utf8 -Value ("{0:yyyy-MM-dd HH:mm:ss} {1}" -f (Get-Date), $texto) } catch {}
}

function Encerrar-Arvore([int]$raizPid) {
    $todos = @(Get-CimInstance Win32_Process)
    $alvo = @{ $raizPid = $true }
    do {
        $novos = 0
        foreach ($p in $todos) {
            if (-not $alvo.ContainsKey([int]$p.ProcessId) -and $alvo.ContainsKey([int]$p.ParentProcessId)) {
                $alvo[[int]$p.ProcessId] = $true; $novos++
            }
        }
    } while ($novos -gt 0)
    foreach ($id in $alvo.Keys) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
    # workers que perderam o pai e ainda seguram as portas da produção
    Start-Sleep -Seconds 2
    foreach ($c in @(Get-NetTCPConnection -LocalPort 3000, 8000 -State Listen -ErrorAction SilentlyContinue)) {
        $proc = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
        if ($proc -and $proc.ProcessName -match '^(python|pythonw|node|bun)$') {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

function Iniciar-Reflex {
    Registrar "iniciando producao em http://${EnderecoProducao}:3000"
    # cmd /c faz o redirecionamento sem o PowerShell 5.1 transformar a saída
    # de erro do Reflex em exceção.
    $reflex = Join-Path $raiz '.venv\Scripts\reflex.exe'
    return Start-Process cmd.exe -PassThru -WindowStyle Hidden -WorkingDirectory $raiz -ArgumentList @(
        '/c', "`"`"$reflex`" run --env prod --loglevel info >> `"$log`" 2>&1`"")
}
function Portas-No-Ar {
    $escutando = @(Get-NetTCPConnection -LocalPort 3000, 8000 -State Listen -ErrorAction SilentlyContinue |
                   Select-Object -ExpandProperty LocalPort -Unique)
    return ($escutando.Count -eq 2)
}

# Daqui em diante nenhum erro pode derrubar o supervisor sem encerrar os filhos.
$ErrorActionPreference = 'Continue'

# Supervisão com auto-recuperação:
#  - pedido de parada (logs\PARAR)       -> encerra tudo e sai;
#  - Reflex terminou sozinho             -> reinicia;
#  - não subiu em 15 min (compilação)    -> reinicia;
#  - tela ou backend sumiram por 90 s    -> reinicia (caso real: a tela
#    caiu com o backend vivo, e o processo principal continuava "rodando").
# No máximo 5 reinícios por hora, para não ficar em laço se houver um erro fixo.
$LIMITE_SUBIDA_S = 15 * 60
$LIMITE_FORA_S = 90
$reinicios = New-Object System.Collections.Generic.List[datetime]
$processo = Iniciar-Reflex
$inicio = Get-Date
$noAr = $false
$foraDesde = $null

while ($true) {
    Start-Sleep -Seconds 5
    if (Test-Path $pedidoParada) {
        Registrar 'pedido de parada recebido; encerrando'
        Encerrar-Arvore $processo.Id
        Remove-Item $pedidoParada -ErrorAction SilentlyContinue
        Registrar 'producao encerrada a pedido'
        exit 0
    }

    $motivo = $null
    if ($processo.HasExited) {
        $motivo = "Reflex terminou sozinho (codigo $($processo.ExitCode))"
    } elseif (Portas-No-Ar) {
        if (-not $noAr) { Registrar ("producao no ar (subiu em {0:N0} s)" -f ((Get-Date) - $inicio).TotalSeconds) }
        $noAr = $true
        $foraDesde = $null
    } elseif (-not $noAr) {
        if (((Get-Date) - $inicio).TotalSeconds -gt $LIMITE_SUBIDA_S) { $motivo = 'nao subiu em 15 min' }
    } else {
        if (-not $foraDesde) { $foraDesde = Get-Date }
        elseif (((Get-Date) - $foraDesde).TotalSeconds -gt $LIMITE_FORA_S) { $motivo = 'tela ou backend fora do ar ha 90 s' }
    }

    if ($motivo) {
        $umaHoraAtras = (Get-Date).AddHours(-1)
        $recentes = @($reinicios | Where-Object { $_ -ge $umaHoraAtras })
        if ($recentes.Count -ge 5) {
            Registrar "$motivo; 5 reinicios na ultima hora - desistindo (veja $log)"
            Encerrar-Arvore $processo.Id
            exit 1
        }
        Registrar "$motivo; reiniciando"
        Encerrar-Arvore $processo.Id
        $reinicios.Add((Get-Date))
        $processo = Iniciar-Reflex
        $inicio = Get-Date
        $noAr = $false
        $foraDesde = $null
    }
}
