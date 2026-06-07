#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ $# -gt 0 ]]; then
  CATEGORIES=("$@")
elif [[ -n "${CATEGORIES:-}" ]]; then
  # shellcheck disable=SC2206
  CATEGORIES=(${CATEGORIES})
else
  CATEGORIES=(Cell_Phones_and_Accessories)
fi

for category in "${CATEGORIES[@]}"; do
  python prepare_edit_data.py \
    --category="${category}" \
    --number_per_item=10 \
    --topk=10 \
    --cache_dir="data/cache/" \
    --output_dir="data/Edit/${category}"
done
