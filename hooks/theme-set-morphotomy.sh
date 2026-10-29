#!/usr/bin/env bash
# Re-assert the MORPHOTOMY Plymouth theme after Omarchy restyles its own.
#
# Omarchy's theme-set runs `omarchy plymouth set`, which publishes the theme's
# unlock.png into its own Plymouth theme and then calls
# `plymouth-set-default-theme omarchy`. That switches the boot splash away from
# ours on every theme change, so this hook puts it back. It is best-effort: a
# hook cannot prompt for a password, so it only acts when sudo is passwordless.
set -euo pipefail

theme_dir=/usr/share/plymouth/themes/morphotomy
[[ -d $theme_dir ]] || exit 0

current=$(plymouth-set-default-theme 2>/dev/null || true)
[[ $current == "morphotomy" ]] && exit 0

if sudo -n plymouth-set-default-theme morphotomy >/dev/null 2>&1; then
  echo "morphotomy: Plymouth theme re-asserted" >&2
else
  echo "morphotomy: Plymouth theme is '$current' — run 'omarchy plymouth' setup again (needs sudo)" >&2
fi
