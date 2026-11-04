#!/usr/bin/env bash
# Status line: Zayana keeps you company at the bottom of Claude Code
input=$(cat)
dir=$(echo "$input" | sed -n 's/.*"current_dir":"\([^"]*\)".*/\1/p')
printf '\e[31m🧕 زيانه\e[0m · \e[32m%s\e[0m · \e[33mمرحبا بك!\e[0m' "${dir##*/}"
