#!/usr/bin/env bash
# Build the KspBot mod, (re)start KSP and install mod + kRPC settings.
# Usage: tools/install.sh [save-name]   save-name: autoload (or create as Normal career) at the main menu.
# KSP locks the DLL, so a running KSP is killed first (save your game!).
set -euo pipefail
K="${KSP_DIR:-/mnt/c/Program Files (x86)/Steam/steamapps/common/Kerbal Space Program}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$HOME/.dotnet:$PATH" DOTNET_ROOT="$HOME/.dotnet"
dotnet build -c Release "$ROOT/mod/KspBot" -v q -nologo | grep -E "error|Build succeeded"
if tasklist.exe 2>/dev/null | grep -i KSP_x64.exe >/dev/null; then
  taskkill.exe /IM KSP_x64.exe /F >/dev/null; sleep 5
fi
mkdir -p "$K/GameData/KspBot/Plugins" "$K/GameData/KspBot/PluginData"
rm -f "$K/GameData/KspBot/Plugins/KspBot.dll"
cp "$ROOT/mod/KspBot/bin/Release/net472/KspBot.dll" "$K/GameData/KspBot/Plugins/"
cp "$ROOT/tools/krpc-settings.cfg" "$K/GameData/kRPC/PluginData/settings.cfg"
if [ $# -ge 1 ]; then printf '%s' "$1" > "$K/GameData/KspBot/PluginData/autoload.txt"; fi
echo "installed; autoload=$(cat "$K/GameData/KspBot/PluginData/autoload.txt" 2>/dev/null || echo none)"
(cd /mnt/c && cmd.exe /c start steam://rungameid/220200)
echo "KSP starting; wait for: uv run ksp status"
