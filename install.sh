#!/usr/bin/env bash
# colab-ml-preflight installer
# Auto-detects CLI tool and installs Colab-specific skills, scripts, and references.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "============================================"
echo "  colab-ml-preflight installer"
echo "  \"Stop losing training runs to Colab"
echo "   disconnects and silent failures.\""
echo "============================================"
echo ""

# Detect CLI tool
detect_cli() {
    if [ -d ".claude" ] || command -v claude &>/dev/null; then
        echo "claude-code"
    elif [ -f "AGENTS.md" ] || [ -f ".codex" ]; then
        echo "codex"
    elif [ -d ".cursor" ]; then
        echo "cursor"
    elif [ -f ".aider.conf.yml" ]; then
        echo "aider"
    else
        echo "generic"
    fi
}

CLI_TOOL=$(detect_cli)
echo -e "${GREEN}Detected CLI tool: ${CLI_TOOL}${NC}"

TARGET_DIR="$(pwd)"
echo "Installing to: ${TARGET_DIR}"
echo ""

# Install core files
echo "Installing core files (Colab-native)..."
mkdir -p "${TARGET_DIR}/scripts"
mkdir -p "${TARGET_DIR}/references"
mkdir -p "${TARGET_DIR}/case_studies"
mkdir -p "${TARGET_DIR}/platforms"
mkdir -p "${TARGET_DIR}/templates"

cp "${SCRIPT_DIR}/scripts/"*.py "${TARGET_DIR}/scripts/" 2>/dev/null && echo "  Scripts copied (pre-configured for Colab)" || true
cp "${SCRIPT_DIR}/references/"*.md "${TARGET_DIR}/references/" 2>/dev/null && echo "  References copied (Colab-focused)" || true
cp "${SCRIPT_DIR}/case_studies/"*.md "${TARGET_DIR}/case_studies/" 2>/dev/null && echo "  Case studies copied (Colab-adapted)" || true
cp "${SCRIPT_DIR}/platforms/"*.json "${TARGET_DIR}/platforms/" 2>/dev/null && echo "  Platform snapshot copied (colab.json only)" || true
cp "${SCRIPT_DIR}/templates/"* "${TARGET_DIR}/templates/" 2>/dev/null && echo "  Config templates copied" || true

chmod +x "${TARGET_DIR}/scripts/"*.py 2>/dev/null || true

# Install CLI-specific adapter
case "${CLI_TOOL}" in
    claude-code)
        echo ""
        echo "Installing Claude Code adapter..."
        mkdir -p "${TARGET_DIR}/.claude/skills/build"
        mkdir -p "${TARGET_DIR}/.claude/skills/check"
        mkdir -p "${TARGET_DIR}/.claude/skills/launch"
        mkdir -p "${TARGET_DIR}/.claude/skills/monitor"
        mkdir -p "${TARGET_DIR}/.claude/skills/blackbox"
        mkdir -p "${TARGET_DIR}/.claude/skills/handbook"
        mkdir -p "${TARGET_DIR}/.claude/commands"
        mkdir -p "${TARGET_DIR}/.claude-plugin"

        for skill in build check launch monitor blackbox handbook; do
            cp "${SCRIPT_DIR}/.claude/skills/${skill}/SKILL.md" \
               "${TARGET_DIR}/.claude/skills/${skill}/SKILL.md" 2>/dev/null || true
        done
        echo "  Skills installed (Colab-native)"

        cp "${SCRIPT_DIR}/.claude/commands/"*.md "${TARGET_DIR}/.claude/commands/" 2>/dev/null || true
        echo "  Commands installed"

        cp "${SCRIPT_DIR}/.claude-plugin/plugin.json" "${TARGET_DIR}/.claude-plugin/" 2>/dev/null || true
        cp "${SCRIPT_DIR}/.claude-plugin/hooks.json" "${TARGET_DIR}/.claude-plugin/" 2>/dev/null || true
        echo "  Plugin config installed"

        mkdir -p "${TARGET_DIR}/prompts"
        cp "${SCRIPT_DIR}/prompts/"*.md "${TARGET_DIR}/prompts/" 2>/dev/null || true
        echo "  Prompts installed"
        ;;

    codex)
        echo ""
        echo "Installing Codex adapter..."
        cp "${SCRIPT_DIR}/adapters/codex/AGENTS.md" "${TARGET_DIR}/AGENTS.md"
        echo "  AGENTS.md installed (Colab-native)"
        ;;

    cursor)
        echo ""
        echo "Installing Cursor adapter..."
        mkdir -p "${TARGET_DIR}/.cursor/rules"
        cp "${SCRIPT_DIR}/adapters/cursor/.cursor/rules/ml-preflight.md" \
           "${TARGET_DIR}/.cursor/rules/ml-preflight.md"
        echo "  Cursor rules installed (Colab-native)"
        ;;

    aider)
        echo ""
        echo "Installing Aider adapter..."
        if [ ! -f "${TARGET_DIR}/.aider.conf.yml" ]; then
            cp "${SCRIPT_DIR}/adapters/aider/.aider.conf.yml" "${TARGET_DIR}/.aider.conf.yml"
            echo "  .aider.conf.yml installed"
        else
            echo -e "  ${YELLOW}.aider.conf.yml exists — merge manually${NC}"
        fi
        ;;

    generic)
        echo ""
        echo "Installing generic adapter..."
        mkdir -p "${TARGET_DIR}/prompts"
        cp "${SCRIPT_DIR}/prompts/"*.md "${TARGET_DIR}/prompts/" 2>/dev/null || true
        echo "  Prompts installed"
        echo -e "  ${YELLOW}See adapters/generic/README.md for integration instructions${NC}"
        ;;
esac

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "Quick start (no --platform flag needed — always Colab):"
echo "  python scripts/preflight_check.py your_notebook.ipynb"
echo "  python scripts/env_parity.py your_notebook.ipynb"
echo "  python scripts/poll_monitor.py --check-health"
echo ""
echo "Commands available (Claude Code):"
echo "  /build    — Construct Colab notebook with governance rules"
echo "  /check    — Preflight validation before running on Colab"
echo "  /launch   — Deploy to Colab via Drive or GitHub"
echo "  /monitor  — Monitor with in-notebook heartbeats"
echo "  /blackbox — Triage disconnects, crashes, and errors"
echo "  /handbook — Colab reference lookup"
echo ""
