# Aurora kernel 7.1.12.aurora8-2 edge update

This update uses kernel commit `60ef6b4cd62a0249c0376e5f199f642f50b645f6`,
which adds the shared Aurora defaults fragment to the reviewed `339ea0487`
code base, including the merged macaudio speaker-codec dependency fix.
The package merges and validates the kernel-owned fragment; driver choices
are maintained with the kernel source.

- Neo speaker support includes the MAX98360A amplifier driver. The explicit
  config requirement also guards against the driver being omitted in future.
- Compatible built-in Force Touch trackpads get the MTP haptics module.
  External Magic Trackpads continue to use the existing magicmouse driver.
  The Neo has a mechanical trackpad.
- J613/J615 PMP temperature telemetry is available as a module.
- Intel IGB and IGC PCIe Ethernet controllers are supported, including
  compatible Thunderbolt adapters and docks. Other Intel NIC drivers remain
  disabled.
- Existing ISP camera support is retained as a validated config requirement.

These defaults apply to the shared Mac kernel; each driver binds to matching
hardware. Reboot after installing the kernel update. Speaker protection still
requires the normal audio services and configuration.

This update targets edge. M1/M2 cold-boot qualification and its recorded
evidence remain required before promotion to rc or stable. Config checks do
not constitute hardware qualification.
