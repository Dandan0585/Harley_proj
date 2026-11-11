<#
  Aplica no Xano (workspace HARLEY) o que está na pasta xano\ do projeto.

  Mostra a prévia das mudanças e pede confirmação antes de gravar (a CLI
  do Xano pergunta "sim/não"). Só envia arquivos alterados e NUNCA apaga
  nada do Xano. Das funções, só as de quick_start\ são enviadas.

  Uso (PowerShell, na pasta do projeto):
      .\scripts\aplicar_xano.ps1              # prévia + confirmação
      .\scripts\aplicar_xano.ps1 -SoPrevia    # só mostra o que mudaria

  Emergência (volta os endpoints ao estado de antes da auditoria de
  24/09/2026, com a API ABERTA sem login; os campos novos continuam):
      .\scripts\aplicar_xano.ps1 -Reverter
#>
param([switch]$SoPrevia, [switch]$Reverter)
$ErrorActionPreference = 'Stop'
$raiz = Split-Path $PSScriptRoot -Parent
$pasta = if ($Reverter) { Join-Path $raiz 'xano_backup\antes_da_auditoria_2026-09-24' } else { Join-Path $raiz 'xano' }
if (-not (Test-Path $pasta)) { Write-Error "Pasta $pasta não encontrada."; exit 1 }
if (-not (Get-Command xano -ErrorAction SilentlyContinue)) {
    Write-Error 'CLI do Xano não encontrada. Instale com: npm install -g @xano/cli'; exit 1
}

Write-Host "Prévia das mudanças no Xano (nada é gravado nesta etapa):" -ForegroundColor Cyan
xano workspace push -d $pasta -e 'function/relatorio/**' -e 'function/utils/**' --no-guids --dry-run
if ($LASTEXITCODE -ne 0) { Write-Error 'A prévia falhou; nada foi alterado.'; exit 1 }
if ($SoPrevia) { exit 0 }

Write-Host "`nAplicando (a CLI vai pedir confirmação):" -ForegroundColor Yellow
xano workspace push -d $pasta -e 'function/relatorio/**' -e 'function/utils/**' --no-guids
exit $LASTEXITCODE
