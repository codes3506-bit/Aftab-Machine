#!/bin/bash
# Installs a Claude Code status line showing input tokens, output tokens and context window % used.
# Run on your own computer:  bash setup-statusline.sh
set -e
mkdir -p ~/.claude

cat > ~/.claude/statusline.sh <<'EOF'
#!/bin/bash
input=$(cat)
model=$(echo "$input" | jq -r '.model.display_name // "Claude"')
in_tok=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
out_tok=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')
size=$(echo "$input" | jq -r '.context_window.context_window_size // 0')
pct=$(echo "$input" | jq -r '.context_window.used_percentage // 0 | floor')
fmt() { awk -v n="$1" 'BEGIN{ if(n>=1000) printf "%.1fk", n/1000; else printf "%d", n }'; }
echo "$model | in: $(fmt "$in_tok")  out: $(fmt "$out_tok") | ctx: ${pct}% of $(fmt "$size")"
EOF
chmod +x ~/.claude/statusline.sh

settings=~/.claude/settings.json
[ -f "$settings" ] || echo '{}' > "$settings"
cp "$settings" "$settings.bak"
jq '.statusLine = {"type":"command","command":"~/.claude/statusline.sh"}' "$settings.bak" > "$settings"

echo "Done. Restart Claude Code to see the status line."
command -v jq >/dev/null || echo "Note: install jq (brew install jq / apt install jq)."
