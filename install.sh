#!/usr/bin/env bash

set -euo pipefail

AGENT="both"
REPO="Lengcangr/Buffett"
REF="main"
SKILL_NAME="buffett-investing-coach"
CODEX_SKILLS_DIR=""
CLAUDE_SKILLS_DIR=""
FORCE="0"

usage() {
  cat <<'EOF'
Usage: install.sh [--agent codex|claude|both] [--force]
                  [--repo owner/repo] [--ref branch]
                  [--codex-skills-dir path] [--claude-skills-dir path]

Installs the Buffett skill into Codex, Claude Code, or both.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)
      AGENT="${2:-}"
      shift 2
      ;;
    --repo)
      REPO="${2:-}"
      shift 2
      ;;
    --ref)
      REF="${2:-}"
      shift 2
      ;;
    --skill-name)
      SKILL_NAME="${2:-}"
      shift 2
      ;;
    --codex-skills-dir)
      CODEX_SKILLS_DIR="${2:-}"
      shift 2
      ;;
    --claude-skills-dir)
      CLAUDE_SKILLS_DIR="${2:-}"
      shift 2
      ;;
    --force)
      FORCE="1"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ "$AGENT" != "codex" && "$AGENT" != "claude" && "$AGENT" != "both" ]]; then
  echo "Invalid --agent value: $AGENT" >&2
  exit 1
fi

default_skills_dir() {
  local target="$1"

  if [[ "$target" == "codex" ]]; then
    if [[ -n "${CODEX_HOME:-}" ]]; then
      printf '%s\n' "${CODEX_HOME}/skills"
    else
      printf '%s\n' "${HOME}/.codex/skills"
    fi
    return
  fi

  printf '%s\n' "${HOME}/.claude/skills"
}

download_cmd() {
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$1" -o "$2"
    return
  fi

  if command -v wget >/dev/null 2>&1; then
    wget -qO "$2" "$1"
    return
  fi

  echo "Need curl or wget to download the repository archive." >&2
  exit 1
}

local_source=""
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
candidate="${script_dir}/skills/${SKILL_NAME}"

if [[ -f "${candidate}/SKILL.md" ]]; then
  local_source="$candidate"
fi

cleanup_root=""
if [[ -z "$local_source" ]]; then
  cleanup_root="$(mktemp -d)"
  archive_path="${cleanup_root}/repo.tar.gz"
  extract_root="${cleanup_root}/extract"
  mkdir -p "$extract_root"
  download_cmd "https://github.com/${REPO}/archive/refs/heads/${REF}.tar.gz" "$archive_path"
  tar -xzf "$archive_path" -C "$extract_root"
  repo_root="$(find "$extract_root" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
  local_source="${repo_root}/skills/${SKILL_NAME}"

  if [[ ! -f "${local_source}/SKILL.md" ]]; then
    echo "Could not locate skills/${SKILL_NAME}/SKILL.md in downloaded repository." >&2
    rm -rf "$cleanup_root"
    exit 1
  fi
fi

install_target() {
  local target="$1"
  local custom_dir="$2"
  local skills_dir="$custom_dir"

  if [[ -z "$skills_dir" ]]; then
    skills_dir="$(default_skills_dir "$target")"
  fi

  local destination="${skills_dir}/${SKILL_NAME}"

  mkdir -p "$skills_dir"

  if [[ -e "$destination" ]]; then
    if [[ "$FORCE" != "1" ]]; then
      echo "Destination already exists: $destination . Re-run with --force to overwrite." >&2
      exit 1
    fi

    rm -rf "$destination"
  fi

  cp -R "$local_source" "$destination"
  printf 'Installed %s to %s\n' "$SKILL_NAME" "$destination"
}

case "$AGENT" in
  codex)
    install_target "codex" "$CODEX_SKILLS_DIR"
    ;;
  claude)
    install_target "claude" "$CLAUDE_SKILLS_DIR"
    ;;
  both)
    install_target "codex" "$CODEX_SKILLS_DIR"
    install_target "claude" "$CLAUDE_SKILLS_DIR"
    ;;
esac

if [[ -n "$cleanup_root" ]]; then
  rm -rf "$cleanup_root"
fi

printf '\nNext step: restart Codex or Claude Code so the new skill is loaded.\n'
