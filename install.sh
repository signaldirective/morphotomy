#!/usr/bin/env bash
# Install MORPHOTOMY for the current user.
#
#   ./install.sh              copy the theme into ~/.config/omarchy/themes
#   ./install.sh --link       symlink it instead, so edits here apply live
#   ./install.sh --apply      ...and switch to it now
#   ./install.sh --plymouth   also install the custom boot splash (sudo)
#   ./install.sh --hook       re-assert the splash after every theme change
#   ./install.sh --force      replace a theme installed by `omarchy theme install`
#
# Users install with: omarchy theme install https://github.com/signaldirective/morphotomy
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
theme_home="${XDG_CONFIG_HOME:-$HOME/.config}/omarchy/themes"
name=morphotomy
target="$theme_home/$name"

link=false
apply=false
plymouth=false
hook=false
force=false

for arg in "$@"; do
  case $arg in
    --link) link=true ;;
    --apply) apply=true ;;
    --plymouth) plymouth=true ;;
    --hook) hook=true ;;
    --force) force=true ;;
    -h|--help) sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown flag: $arg" >&2; exit 1 ;;
  esac
done

# A theme installed with `omarchy theme install` is a git clone. Replacing it
# with a copy would silently end its ability to update, so only do that on
# request -- the normal user install is the omarchy command, not this script.
if [[ -d $target/.git ]] && ! $force; then
  echo "$target is a git clone (installed with 'omarchy theme install')." >&2
  echo "Remove it with 'omarchy theme remove $name' first, or pass --force to replace it." >&2
  exit 1
fi

missing=()
[[ -f $here/colors.toml ]] || missing+=("colors.toml")
[[ -f $here/backgrounds/1-implantation.webp ]] || missing+=("backgrounds/1-implantation.webp")
[[ -f $here/unlock.png ]] || missing+=("unlock.png")
if (( ${#missing[@]} )); then
  echo "missing theme files: ${missing[*]}" >&2
  exit 1
fi

mkdir -p "$theme_home"
if $link; then
  rm -rf "$target"
  ln -s "$here" "$target"
  echo "linked $target -> $here"
else
  rm -rf "$target"
  mkdir -p "$target"
  # everything except the tools and the git metadata
  tar -C "$here" -cf - \
      --exclude=./tools --exclude=./source --exclude=./.git \
      --exclude='./backgrounds/.render-*' . |
    tar -C "$target" -xf -
  echo "installed $target"
fi

if $plymouth; then
  echo "installing the Plymouth splash (sudo)"
  sudo install -d -m 0755 /usr/share/plymouth/themes/morphotomy
  sudo install -m 0644 "$here"/plymouth/morphotomy/* /usr/share/plymouth/themes/morphotomy/
  sudo plymouth-set-default-theme morphotomy
  if command -v limine-mkinitcpio >/dev/null; then
    sudo limine-mkinitcpio
  else
    sudo mkinitcpio -P
  fi
  echo "Plymouth theme installed — visible on the next boot"
  if $hook; then
    if command -v omarchy >/dev/null && omarchy hook install theme-set "$here/hooks/theme-set-morphotomy.sh" 2>/dev/null; then
      echo "hook installed: the splash will survive future theme changes"
    else
      echo "could not install the hook automatically; see hooks/ in the README" >&2
    fi
  fi
fi

if $apply; then
  omarchy theme set "$name"
fi

cat <<EOF

MORPHOTOMY is in $target
  switch to it:   omarchy theme set $name
  next wallpaper: omarchy theme bg next
  boot splash:    $0 --plymouth --hook
EOF
