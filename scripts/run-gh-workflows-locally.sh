#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/run-gh-workflows-locally.sh [ci|release] [options] [-- <extra act args>]

Run this repository's GitHub Actions workflows locally with act.

Modes:
  ci                  Run .github/workflows/addon-ci.yml (default)
  release             Run .github/workflows/addon-release.yml

Options:
  -j, --job JOB       Run a single job from the selected workflow
      --tag TAG       Release tag to simulate, defaults to v<addon version>
      --list          List jobs in the selected workflow
      --dry-run       Show the execution plan without running containers
  -v, --verbose       Enable verbose act output
      --json-logs     Emit act logs in JSON format
      --reuse         Reuse existing act containers
      --secret-file   Load secrets from a specific act secrets file
      --allow-publish Allow release build/release jobs that publish artifacts
      --arch ARCH     Container architecture for act (default: linux/amd64)
  -h, --help          Show this help

Environment:
  ACT_IMAGE           Override the image used for ubuntu-latest
  ACT_CONTAINER_ARCH  Override the act container architecture
  GITHUB_TOKEN        Passed to act when set

Examples:
  scripts/run-gh-workflows-locally.sh ci
  scripts/run-gh-workflows-locally.sh ci --job test
  scripts/run-gh-workflows-locally.sh release
  scripts/run-gh-workflows-locally.sh release --job firmware --tag v0.4.6
  scripts/run-gh-workflows-locally.sh release --allow-publish --job build
EOF
}

die() {
  printf 'Error: %s\n' "$1" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

read_addon_version() {
  sed -n 's/^version:[[:space:]]*"\{0,1\}\([^\"]*\)"\{0,1\}$/\1/p' "$repo_root/wiimote-bridge/config.yaml" | head -n 1
}

workflow="ci"
job=""
tag=""
list_only=0
dry_run=0
verbose=0
json_logs=0
reuse=0
allow_publish=0
secret_file=""
container_arch="${ACT_CONTAINER_ARCH:-linux/amd64}"
act_image="${ACT_IMAGE:-catthehacker/ubuntu:full-latest}"
extra_args=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    ci|release)
      workflow="$1"
      shift
      ;;
    -j|--job)
      [[ $# -ge 2 ]] || die "Missing value for $1"
      job="$2"
      shift 2
      ;;
    --tag)
      [[ $# -ge 2 ]] || die "Missing value for $1"
      tag="$2"
      shift 2
      ;;
    --list)
      list_only=1
      shift
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -v|--verbose)
      verbose=1
      shift
      ;;
    --json-logs)
      json_logs=1
      shift
      ;;
    --reuse)
      reuse=1
      shift
      ;;
    --secret-file)
      [[ $# -ge 2 ]] || die "Missing value for $1"
      secret_file="$2"
      shift 2
      ;;
    --allow-publish)
      allow_publish=1
      shift
      ;;
    --arch)
      [[ $# -ge 2 ]] || die "Missing value for $1"
      container_arch="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      extra_args+=("$@")
      break
      ;;
    *)
      die "Unknown argument: $1"
      ;;
  esac
done

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/.." && pwd)"

require_command act
require_command docker
require_command git

docker info >/dev/null 2>&1 || die "Docker daemon is not available"

case "$workflow" in
  ci)
    workflow_file="$repo_root/.github/workflows/addon-ci.yml"
    event_name="push"
    event_ref="refs/heads/main"
    ;;
  release)
    workflow_file="$repo_root/.github/workflows/addon-release.yml"
    event_name="push"
    addon_version="$(read_addon_version)"
    [[ -n "$addon_version" ]] || die "Unable to read add-on version from wiimote-bridge/config.yaml"

    if [[ -z "$tag" ]]; then
      tag="v$addon_version"
    elif [[ "$tag" != v* ]]; then
      tag="v$tag"
    fi

    event_ref="refs/tags/$tag"

    if [[ -z "$job" && $allow_publish -eq 0 ]]; then
      job="firmware"
      printf 'Info: defaulting release runs to the safe local firmware path (prepare + firmware).\n' >&2
      printf 'Info: pass --allow-publish to run build/release jobs that publish to GHCR or GitHub Releases.\n' >&2
    fi

    if [[ $allow_publish -eq 0 && ( "$job" == "build" || "$job" == "release" ) ]]; then
      die "Release job '$job' publishes artifacts. Re-run with --allow-publish if that is intentional"
    fi

    if [[ $allow_publish -eq 1 && -z "${GITHUB_TOKEN:-}" && -z "$secret_file" && ! -f "$repo_root/.secrets.act" ]]; then
      die "Publishing release jobs require GITHUB_TOKEN or an act secrets file"
    fi
    ;;
esac

[[ -f "$workflow_file" ]] || die "Workflow file not found: $workflow_file"

if [[ $list_only -eq 1 ]]; then
  cd "$repo_root"
  exec act -W "$workflow_file" -l
fi

event_file="$(mktemp)"
artifact_dir="$repo_root/.act/artifacts"
mkdir -p "$artifact_dir"

cleanup() {
  rm -f "$event_file"
}

trap cleanup EXIT

cat >"$event_file" <<EOF
{
  "ref": "$event_ref",
  "repository": {
    "full_name": "andremmfaria/ha-wiimote-bridge",
    "default_branch": "main"
  },
  "head_commit": {
    "id": "local"
  }
}
EOF

act_command=(
  act
  "$event_name"
  -W "$workflow_file"
  -e "$event_file"
  -P "ubuntu-latest=$act_image"
  --container-architecture "$container_arch"
  --artifact-server-path "$artifact_dir"
)

if [[ -n "$job" ]]; then
  act_command+=( -j "$job" )
fi

if [[ $dry_run -eq 1 ]]; then
  act_command+=( -n )
fi

if [[ $verbose -eq 1 ]]; then
  act_command+=( -v )
fi

if [[ $json_logs -eq 1 ]]; then
  act_command+=( --json )
fi

if [[ $reuse -eq 1 ]]; then
  act_command+=( --reuse )
fi

if [[ -n "$secret_file" ]]; then
  act_command+=( --secret-file "$secret_file" )
elif [[ -f "$repo_root/.secrets.act" ]]; then
  act_command+=( --secret-file "$repo_root/.secrets.act" )
fi

if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  act_command+=( -s "GITHUB_TOKEN=$GITHUB_TOKEN" )
fi

if [[ ${#extra_args[@]} -gt 0 ]]; then
  act_command+=( "${extra_args[@]}" )
fi

printf 'Running %s workflow with act\n' "$workflow"
printf 'Workflow file: %s\n' "$workflow_file"
printf 'Event ref: %s\n' "$event_ref"
if [[ -n "$job" ]]; then
  printf 'Job: %s\n' "$job"
fi
if [[ $verbose -eq 1 ]]; then
  printf 'Act command:'
  printf ' %q' "${act_command[@]}"
  printf '\n'
fi

cd "$repo_root"
exec "${act_command[@]}"