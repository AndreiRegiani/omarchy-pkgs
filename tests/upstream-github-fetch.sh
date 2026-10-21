#!/bin/bash
# The github provider's fetches: the release feed sends the job's token to
# api.github.com through curl's stdin config (never on a command line), the
# checksum download from github.com never gets it, and both stay on HTTP/1.1.
set -euo pipefail
ROOT=$(realpath "${BASH_SOURCE[0]%/*}/..")
source "$ROOT/helpers/upstream-github.sh"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1"; exit 1; }

curl() {
  printf '%s\n' "$@" > "$T/args"
  cat > "$T/stdin"
}

UPSTREAM_GITHUB_TOKEN=job-token github_fetch_releases owner/repo </dev/null
grep -qx 'https://api.github.com/repos/owner/repo/releases?per_page=100' "$T/args" \
  && pass "the release feed comes from the API" || fail "release feed URL: $(<"$T/args")"
grep -qx -- '--http1.1' "$T/args" && pass "the release feed uses HTTP/1.1" || fail "release feed args: $(<"$T/args")"
grep -q job-token "$T/args" && fail "the token is on the command line"
pass "the token stays off the command line"
grep -A1 -x -- '--config' "$T/args" | grep -qx -- '-' \
  && [[ $(<"$T/stdin") == 'header = "Authorization: Bearer job-token"' ]] \
  && pass "the token goes to the API through stdin config" || fail "args: $(<"$T/args") stdin: $(<"$T/stdin")"

UPSTREAM_GITHUB_TOKEN= github_fetch_releases owner/repo </dev/null
grep -qx -- '--config' "$T/args" && fail "an empty token still reads a config"
[[ ! -s "$T/stdin" ]] && pass "no token, no Authorization header" || fail "stdin: $(<"$T/stdin")"

UPSTREAM_GITHUB_TOKEN=job-token github_fetch_checksums owner/repo v1.0 SHA256SUMS </dev/null
grep -qx 'https://github.com/owner/repo/releases/download/v1.0/SHA256SUMS' "$T/args" \
  && pass "checksums come from the release download" || fail "checksums URL: $(<"$T/args")"
grep -qx -- '--http1.1' "$T/args" && pass "the checksum download uses HTTP/1.1" || fail "checksum args: $(<"$T/args")"
grep -q job-token "$T/args" "$T/stdin" && fail "the token went to a release download"
pass "the token never goes to a release download"
