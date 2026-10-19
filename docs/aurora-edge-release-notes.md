# Aurora kernel edge update

This update uses kernel commit `339ea0487dfce434f8769d39046db95be03f6e48`,
including the merged macaudio speaker-codec dependency fix.

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
