<#
  Publica na PRODUÇÃO a versão atual do desenvolvimento.

  1. Recusa se houver alterações não commitadas (só vai para a produção o
     que está registrado no git).
  2. Cria a tag prod-AAAAMMDD-HHMM no commit atual.
  3. Envia commit e tag ao GitHub (cópia de segurança; se falhar, só avisa).
  4. Atualiza e reinicia a produção nessa tag (atualizar_producao.ps1).

  Uso:  .\scripts\publicar.ps1
  Voltar versão:  .\scripts\atualizar_producao.ps1 -Tag <tag anterior>
#>
param([string]$Producao = 'C:\HARLEY_PROD')
# 'Continue' (e nao 'Stop'): no PowerShell 5.1, com 'Stop', qualquer aviso que o
# git escreva na saida de erro vira excecao, mesmo com 2>$null. Cada passo
# confere $LASTEXITCODE explicitamente.
$ErrorActionPreference = 'Continue'
$raiz = Split-Path $PSScriptRoot -Parent

$pendentes = git -C $raiz status --porcelain
if ($pendentes) {
    Write-Host "ERRO: ha alteracoes nao commitadas; faca o commit antes de publicar:" -ForegroundColor Red
    $pendentes | ForEach-Object { Write-Host "  $_" }
    exit 1
}

$tag = 'prod-{0:yyyyMMdd-HHmm}' -f (Get-Date)
if (git -C $raiz tag --list $tag) { $tag = 'prod-{0:yyyyMMdd-HHmmss}' -f (Get-Date) }
git -C $raiz tag -a $tag -m "Publicacao em producao $tag"
if ($LASTEXITCODE -ne 0) { Write-Host "ERRO: nao foi possivel criar a tag $tag." -ForegroundColor Red; exit 1 }
Write-Host "Versao marcada: $tag ($(git -C $raiz log -1 --format='%h %s'))" -ForegroundColor Cyan

git -C $raiz push --quiet origin HEAD $tag 2>$null
if ($LASTEXITCODE -ne 0) { Write-Warning 'Nao foi possivel enviar ao GitHub agora; a publicacao local continua.' }

& (Join-Path $PSScriptRoot 'atualizar_producao.ps1') -Tag $tag -Producao $Producao
exit $LASTEXITCODE
