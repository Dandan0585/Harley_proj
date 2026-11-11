<#
  Atualiza a PRODUÇÃO para uma versão (tag) registrada no git e a reinicia.

  Roteiro: confere a produção -> para -> busca as versões -> checkout da
  tag -> instala dependências -> inicia -> espera ficar no ar.

  Também serve para VOLTAR à versão anterior:
      .\scripts\atualizar_producao.ps1 -Tag prod-20260923-1500

  Sem -Tag, usa a tag prod-* mais recente. Normalmente é chamado pelo
  publicar.ps1; rode direto só para voltar versão.
#>
param(
    [string]$Tag,
    [string]$Producao = 'C:\HARLEY_PROD',
    [int]$EsperaMaxMinutos = 10
)
# 'Continue' (e nao 'Stop'): no PowerShell 5.1, com 'Stop', qualquer aviso que o
# git escreva na saida de erro vira excecao, mesmo com 2>$null. Cada passo
# confere $LASTEXITCODE explicitamente.
$ErrorActionPreference = 'Continue'
$nomeTarefa = 'HarleyStore-Producao'

function Falhar($mensagem) { Write-Host "ERRO: $mensagem" -ForegroundColor Red; exit 1 }

if (-not (Test-Path (Join-Path $Producao '.git'))) { Falhar "$Producao nao e um clone git da aplicacao." }

# 1) Recusa se alguém alterou arquivos direto na produção.
$sujos = git -C $Producao status --porcelain --untracked-files=no
if ($sujos) {
    Falhar ("A producao tem alteracoes locais e nao sera atualizada:`n$($sujos -join "`n")`n" +
            "Leve essas alteracoes para o desenvolvimento ou descarte-as antes.")
}

# 2) Busca versões e escolhe a tag.
git -C $Producao fetch --quiet --tags --force origin
if ($LASTEXITCODE -ne 0) { Falhar 'git fetch falhou.' }
if (-not $Tag) {
    $Tag = git -C $Producao tag --list 'prod-*' --sort=-creatordate | Select-Object -First 1
    if (-not $Tag) { Falhar 'Nenhuma tag prod-* encontrada. Publique primeiro com publicar.ps1.' }
}
git -C $Producao rev-parse --verify --quiet "refs/tags/$Tag" | Out-Null
if ($LASTEXITCODE -ne 0) { Falhar "Tag '$Tag' nao existe." }
$anterior = git -C $Producao describe --tags --exact-match 2>$null
Write-Host "Atualizando producao: $(if ($anterior) { $anterior } else { '(sem tag)' }) -> $Tag" -ForegroundColor Cyan

# 3) Para, troca de versão e instala dependências.
& (Join-Path $PSScriptRoot 'parar_producao.ps1') -Producao $Producao
if ($LASTEXITCODE -ne 0) { Falhar 'Nao foi possivel parar a producao.' }

git -C $Producao -c advice.detachedHead=false checkout --quiet $Tag
if ($LASTEXITCODE -ne 0) { Falhar "checkout de $Tag falhou." }

& (Join-Path $Producao '.venv\Scripts\python.exe') -m pip install --quiet --disable-pip-version-check -r (Join-Path $Producao 'requirements.txt')
if ($LASTEXITCODE -ne 0) { Falhar 'pip install falhou.' }

# 4) Inicia pela tarefa agendada (ou direto, se ela ainda não existir).
if (Get-ScheduledTask -TaskName $nomeTarefa -ErrorAction SilentlyContinue) {
    Start-ScheduledTask -TaskName $nomeTarefa
} else {
    Write-Warning "Tarefa $nomeTarefa nao existe; iniciando a producao diretamente."
    Start-Process powershell.exe -WindowStyle Hidden -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $Producao 'scripts\iniciar_producao.ps1'))
}

# 5) Espera a produção responder (a compilação leva alguns minutos).
$inicio = Get-Date
$limite = $inicio.AddMinutes($EsperaMaxMinutos)
$ok = $false
while ((Get-Date) -lt $limite) {
    Start-Sleep -Seconds 5
    $escutando = @(Get-NetTCPConnection -LocalPort 3000, 8000 -State Listen -ErrorAction SilentlyContinue |
                   Select-Object -ExpandProperty LocalPort -Unique)
    if ($escutando.Count -eq 2) {
        try {
            $r = Invoke-WebRequest 'http://localhost:8000/ping' -UseBasicParsing -TimeoutSec 5
            $f = Invoke-WebRequest 'http://localhost:3000/' -UseBasicParsing -TimeoutSec 15
            if ($r.StatusCode -eq 200 -and $f.StatusCode -eq 200) { $ok = $true; break }
        } catch {}
    }
}
$segundos = [int]((Get-Date) - $inicio).TotalSeconds
if (-not $ok) { Falhar "A producao nao respondeu em $EsperaMaxMinutos min. Veja $Producao\logs." }
Write-Host "Producao no ar na versao $Tag (subiu em $segundos s)." -ForegroundColor Green
exit 0
