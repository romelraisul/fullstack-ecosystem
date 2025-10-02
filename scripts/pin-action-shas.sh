#!/usr/bin/env bash
set -euo pipefail
# Script: pin-action-shas.sh
# Scans workflow YAML files and replaces action references of the form
#   uses: owner/action@vX or @main / @master / @vX.Y.Z
# with a commit SHA, opening a summary of changes.
# Excludes already-SHA pinned references (40 hex chars) and local ./ paths.

WORKFLOWS_DIR=".github/workflows"
TMP_FILE="/tmp/pin-actions.$$"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) required for resolving SHAs" >&2
  exit 1
fi

changed=0

while IFS= read -r -d '' file; do
  while IFS= read -r line; do
    if [[ "$line" =~ uses:\ ([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([A-Za-z0-9_.-]+) ]]; then
      full=${BASH_REMATCH[0]}
      repo=${BASH_REMATCH[1]}
      ref=${BASH_REMATCH[2]}
      # Skip if ref already looks like a SHA
      if [[ $ref =~ ^[0-9a-fA-F]{40}$ ]]; then
        continue
      fi
      # Skip local or composite refs
      if [[ $repo == .* ]]; then
        continue
      fi
      echo "Resolving $repo@$ref" >&2
      sha=$(gh api repos/$repo/commits/$ref -q '.sha' 2>/dev/null || true)
      if [[ -z "$sha" ]]; then
        echo "Warning: could not resolve $repo@$ref" >&2
        continue
      fi
      # Escape slashes for sed
      esc_full=$(printf '%s\n' "$full" | sed -e 's/[\/[\*\&]/\\&/g')
      esc_repl="uses: $repo@$sha"
      sed -i.bak -e "s|$esc_full|$esc_repl|" "$file"
      changed=1
    fi
  done < "$file"
  rm -f "$file.bak"
  done < <(find "$WORKFLOWS_DIR" -type f -name '*.yml' -print0)

if [[ $changed -eq 0 ]]; then
  echo "No action references required pinning." >&2
else
  echo "Pinned mutable action refs to SHAs." >&2
fi
