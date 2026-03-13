#!/bin/bash
# JARVIS M1 Panel — Layout tmux avec monitoring
SESSION="jarvis-panel"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session $SESSION existe deja — attache..."
    tmux attach -t "$SESSION"
    exit 0
fi

tmux new-session -d -s "$SESSION" -n "monitor"

# Pane 0: htop
tmux send-keys -t "$SESSION" "htop" C-m

# Split horizontal
tmux split-window -h -t "$SESSION"
# Pane 1: nvidia-smi en boucle
tmux send-keys -t "$SESSION" "watch -n 2 nvidia-smi" C-m

# Split pane 1 vertical
tmux split-window -v -t "$SESSION"
# Pane 2: journalctl services jarvis
tmux send-keys -t "$SESSION" "journalctl --user -u 'jarvis-*' -u 'lmstudio-*' -f --no-pager" C-m

# Split pane 0 vertical
tmux select-pane -t 0
tmux split-window -v -t "$SESSION"
# Pane 3: dashboard jarvis
tmux send-keys -t "$SESSION" "python3 ~/jarvis-linux/monitoring/m1-jarvis-dashboard.py" C-m

# Egaliser les panes
tmux select-layout -t "$SESSION" tiled

tmux attach -t "$SESSION"
