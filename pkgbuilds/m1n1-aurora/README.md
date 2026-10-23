# m1n1-aurora

Build the canonical Aurora bootloader package from an immutable omacom/m1n1
commit. The current candidate is 76194672cd873db0c32f98037d3b160874ea3863
(merged source PRs #6, #7, #8, #10, #12 and #13), with Clang/lld, Rust 1.89.0 and
`-Os`. The package's existing 48/128/256 artwork is unchanged. The former USB4
alias patch is already in the source; the APFS preboot UUID handoff proposed in
omarchy-pkgs #1485 is also present upstream, so neither needs a local patch.

## Existing installations

The package replaces the downstream `aura` and `m1n1-neo` packages and conflicts
with the stock `m1n1`; it never automatically replaces the stock package.
It provides `m1n1=1.6.1.aurora20` for the kernel dependency. An installed
`m1n1-aurora` upgrades normally; an `aura` installation accepts pacman's named
replacement transaction. `aura` is removed in the same transaction, leaving
exactly one provider for the boot checker merged in omarchy-mac-pkgs #52.

Stage 2 remains `/usr/lib/asahi-boot/m1n1.bin`. The existing asahi-scripts hook
rebuilds `m1n1/boot.bin` on the selected system ESP from the loader, kernel DTBs
and U-Boot. This package adds no install script, Recovery command or ESP rename.
`/etc/default/update-m1n1` overrides are left alone.

Stage 1 raw/Mach-O artifacts are available under
`/usr/share/m1n1-aurora/stage1/`. The old `/usr/share/aura/stage1/aura-raw.bin`
and `aura.macho` paths remain regular-file copies for installer compatibility.
Normal package updates never enroll Stage 1; that requires a separate explicit
installer or Recovery operation. Large Neo images need matched Stage 1 and
Stage 2 support, so a Stage 2 package upgrade alone is not a Stage 1 migration.

## Coordinated image rollout

Before publishing an image, switch the image builder's package selection and
signed candidate-set ownership from `aura` to `m1n1-aurora`. Its existing
`m1n1-aurora -> aura` rewrite must be removed, and its artifact/ownership checks
must expect `m1n1-aurora`. The compatibility files preserve artifact lookups;
they do not change that exact package-name selection. Keep accepting already
installed `aura` in the boot checker. Leave the legacy `aura` recipe unchanged
until that coordinated rollout; do not select both providers in an image.

## Qualification

This is an unsigned candidate, not a new hardware-qualified release.
`build-qualification.json` remains `hardware_tested: false`; the qualification
validator must pass without `--build-only` before publication. Matched Neo
Stage 1/Stage 2 boot, repair and upgrade evidence remains required.
The source pin includes the GNU ld orphan-layout fix and linker regression
tests merged in omacom/m1n1 #13; this recipe explicitly uses lld. No Stage 1
enrollment, target installation or hardware boot is performed by updating
this package PR.
