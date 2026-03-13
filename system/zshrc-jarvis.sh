#!/bin/bash
# JARVIS aliases — source depuis .zshrc ou .bashrc
# Usage: echo 'source ~/jarvis-linux/system/zshrc-jarvis.sh' >> ~/.zshrc

# Monitoring
alias jhealth='python3 ~/jarvis-linux/monitoring/m1-health.py'
alias jgpu='python3 ~/jarvis-linux/monitoring/m1-gpu-health.py'
alias jmem='python3 ~/jarvis-linux/monitoring/jarvis-memory-report.py'
alias jdash='python3 ~/jarvis-linux/monitoring/m1-jarvis-dashboard.py'
alias jpanel='bash ~/jarvis-linux/monitoring/m1-jarvis-panel.sh'
alias jzram='bash ~/jarvis-linux/system/zram/zram-status.sh'

# Services
alias jstatus='systemctl --user list-units --type=service --state=running | grep -i jarvis'
alias jtimers='systemctl --user list-timers | grep jarvis'
alias jlogs='journalctl --user -u "jarvis-*" -u "lmstudio-*" -f --no-pager'

# MCP
alias jmcp='curl -s -X POST http://127.0.0.1:8080/mcp -H "Authorization: Bearer 1202" -H "Content-Type: application/json"'
alias jtools='curl -s -X POST http://127.0.0.1:8080/mcp -H "Authorization: Bearer 1202" -H "Content-Type: application/json" -d '"'"'{"jsonrpc":"2.0","id":1,"method":"tools/list"}'"'"''

# Cluster
alias jlm='curl -s http://127.0.0.1:1234/api/v1/models | python3 -m json.tool'
alias jws='curl -s http://127.0.0.1:9742/health'
alias jclaw='curl -s http://127.0.0.1:28789/health'

# Docker
alias jdocker='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'

# GPU
alias jnv='nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv'
alias jgpusetup='sudo bash ~/jarvis-linux/monitoring/m1-gpu-setup.sh'

export JARVIS_HOME="$HOME/jarvis-linux"
