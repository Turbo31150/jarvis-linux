###############################################################################
# JARVIS Docker — Arret propre
###############################################################################

Write-Host "=== Arret JARVIS Docker Stack ===" -ForegroundColor Cyan
Set-Location "/home/turbo/jarvis-linux\docker"
docker compose down
Write-Host "[OK] Stack arretee" -ForegroundColor Green
