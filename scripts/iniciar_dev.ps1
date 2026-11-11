<#
  Inicia o ambiente de DESENVOLVIMENTO do Harley Store.

  - Portas 3001 (tela) e 8001 (backend), para não conflitar com a
    produção (3000/8000), que roda ao mesmo tempo no mesmo notebook.
  - O backend escuta só em 127.0.0.1, e o firewall não libera 3001/8001:
    outros aparelhos da rede não alcançam o desenvolvimento.
  - Modo dev: recompila sozinho a cada arquivo salvo.

  Atenção: o desenvolvimento usa o MESMO banco Xano da produção. Teste só
  com registros marcados como teste e apague-os em seguida; não faça
  testes de estoque em produtos reais.

  Uso:  .\scripts\iniciar_dev.ps1      (abra http://localhost:3001)
#>
$ErrorActionPreference = 'Stop'
$raiz = Split-Path $PSScriptRoot -Parent
Set-Location $raiz

$env:REFLEX_API_URL       = 'http://localhost:8001'
$env:REFLEX_DEPLOY_URL    = 'http://localhost:3001'
$env:REFLEX_FRONTEND_PORT = '3001'
$env:REFLEX_BACKEND_PORT  = '8001'
$env:REFLEX_BACKEND_HOST  = '127.0.0.1'

Write-Host 'Harley Store - DESENVOLVIMENTO em http://localhost:3001 (Ctrl+C para parar)' -ForegroundColor Yellow
& (Join-Path $raiz '.venv\Scripts\reflex.exe') run --env dev
