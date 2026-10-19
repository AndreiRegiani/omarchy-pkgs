# Shared by prepare() and the configuration-only CI check.
# The caller supplies _make with its toolchain flags.
configure_kernel() {
  local config_dir=$1 output_dir=$2 snapshot=${3:-}
  mkdir -p "$output_dir" || return
  cp "$config_dir/config" "$output_dir/.config" || return
  scripts/kconfig/merge_config.sh -m -O "$output_dir" "$output_dir/.config" \
    "$config_dir/common.config" "$config_dir/neo.config" || return
  scripts/config --file "$output_dir/.config" --disable LOCALVERSION_AUTO || return
  if [[ -n $snapshot ]]; then
    cp "$output_dir/.config" "$snapshot" || return
  fi
  _make O="$output_dir" olddefconfig || return
  python3 "$config_dir/validate-config.py" "$config_dir/common.config" "$output_dir/.config" || return
  python3 "$config_dir/validate-config.py" "$config_dir/neo.config" "$output_dir/.config" || return
  grep -qx 'CONFIG_RUST=y' "$output_dir/.config" || {
    echo 'linux-aurora requires Rust drivers; toolchain/configuration disabled CONFIG_RUST' >&2
    return 1
  }
}
