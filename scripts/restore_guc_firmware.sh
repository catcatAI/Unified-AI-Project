#!/usr/bin/env bash
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
# A/B the Arc B570 GuC firmware (needs root; reboot to take effect).
#
# Facts (2026-10-25):
#   - /lib/firmware/xe/bmg_guc_70.bin is GuC 70.72.1, installed 2026-10-02,
#     byte-identical to linux-firmware upstream (de81c75f...).
#   - bmg_guc_70.bin.zst (present since 2026-07-14) decompresses to the older
#     2025-03-27 build (777e9406...). This script makes .bin equal the older
#     build — a downgrade A/B against the version implicated by upstream
#     intel/compute-runtime#999 (BMG + GuC 70.72.1 + "not started" timeouts).
#   - The current 70.72.1 file is kept as .guc70.72.1-20261002.bak so
#     re-applying is a one-command revert.
#
# Usage: sudo bash scripts/restore_guc_firmware.sh   (or via elevation)
set -euo pipefail

DIR=/lib/firmware/xe
BIN="$DIR/bmg_guc_70.bin"
ZST="$DIR/bmg_guc_70.bin.zst"
BAK="$DIR/bmg_guc_70.bin.guc70.72.1-20261002.bak"
SHA_CURRENT_UPSTREAM="de81c75f46a127c33cd59f604d800e9ffc7ed3495967ba0d8767cd6985ab398b"
SHA_OLD_ZST="777e9406832666bb9db918edfc43cf4bdc992a8dd081eabdc6ebcd4b583fd3db"

cur=$(sha256sum "$BIN" | awk '{print $1}')
if [ "$cur" = "$SHA_OLD_ZST" ]; then
    echo "already at the older (.zst) content: $cur"
    exit 0
fi
if [ "$cur" != "$SHA_CURRENT_UPSTREAM" ]; then
    echo "REFUSING: unexpected .bin content $cur (neither 70.72.1 nor .zst)" >&2
    exit 1
fi

# Keep the 70.72.1 file for a one-command revert (cp bak back over .bin).
if [ ! -f "$BAK" ]; then
    cp -p "$BIN" "$BAK"
    echo "backed up 70.72.1 -> $BAK"
fi

tmp=$(mktemp "$DIR/.guc.XXXXXX")
zstd -dc "$ZST" > "$tmp"
new=$(sha256sum "$tmp" | awk '{print $1}')
if [ "$new" != "$SHA_OLD_ZST" ]; then
    rm -f "$tmp"
    echo "REFUSING: decompressed .zst hash $new != expected $SHA_OLD_ZST" >&2
    exit 1
fi
chmod 644 "$tmp"
chown root:root "$tmp"
mv "$tmp" "$BIN"
echo "installed older GuC content:"
sha256sum "$BIN"
echo "reboot required: the xe driver loads the GuC only at probe."
echo "revert anytime: cp -p $BAK $BIN && reboot"
