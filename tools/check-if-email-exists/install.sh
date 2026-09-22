#!/usr/bin/env bash
# Install reacherhq/check-if-email-exists (CLI + optional HTTP backend) from source.
#
# Usage:
#   ./install.sh              # build and install the CLI to ~/.local/bin
#   ./install.sh --backend    # also build the HTTP backend binary
#   PREFIX=/usr/local ./install.sh
#
# Requires: rust toolchain (rustup), perl, cc, make, pkg-config.

set -euo pipefail

REPO_URL="https://github.com/reacherhq/check-if-email-exists.git"
REF="${REF:-master}"
SRC_DIR="${SRC_DIR:-${HOME}/.local/src/check-if-email-exists}"
PREFIX="${PREFIX:-${HOME}/.local}"
BIN_DIR="${PREFIX}/bin"
BUILD_BACKEND=0

for arg in "$@"; do
  case "$arg" in
    --backend) BUILD_BACKEND=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

command -v cargo >/dev/null || {
  echo "cargo not found. Install Rust: https://rustup.rs" >&2
  exit 1
}

if [ -d "${SRC_DIR}/.git" ]; then
  echo ">> updating ${SRC_DIR}"
  git -C "${SRC_DIR}" fetch --depth 1 origin "${REF}"
  git -C "${SRC_DIR}" checkout FETCH_HEAD
else
  echo ">> cloning into ${SRC_DIR}"
  mkdir -p "$(dirname "${SRC_DIR}")"
  git clone --depth 1 --branch "${REF}" "${REPO_URL}" "${SRC_DIR}"
fi

echo ">> building CLI (release, LTO: this takes several minutes)"
cargo build --release --manifest-path "${SRC_DIR}/Cargo.toml" -p check-if-email-exists-cli

mkdir -p "${BIN_DIR}"
install -m 0755 "${SRC_DIR}/target/release/check_if_email_exists" "${BIN_DIR}/check_if_email_exists"
echo ">> installed ${BIN_DIR}/check_if_email_exists"

if [ "${BUILD_BACKEND}" = "1" ]; then
  echo ">> building HTTP backend"
  cargo build --release --manifest-path "${SRC_DIR}/Cargo.toml" -p reacher_backend
  install -m 0755 "${SRC_DIR}/target/release/reacher_backend" "${BIN_DIR}/reacher_backend"
  echo ">> installed ${BIN_DIR}/reacher_backend"
fi

case ":${PATH}:" in
  *":${BIN_DIR}:"*) ;;
  *) echo ">> NOTE: add ${BIN_DIR} to your PATH" ;;
esac

"${BIN_DIR}/check_if_email_exists" --version || true
