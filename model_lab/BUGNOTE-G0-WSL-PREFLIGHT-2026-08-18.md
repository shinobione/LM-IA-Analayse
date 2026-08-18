# Candidate G0 preflight — WSL side-effect note

Date: 2026-08-18

The first real Windows G0 preflight on the RTX 3060 machine revealed an unintended side effect in the WSL probe.

The script advertised `ZERO PACKAGE INSTALL`, but when `wsl.exe` existed without WSL being fully provisioned, invoking `wsl.exe --version` / `wsl.exe --status` could trigger Windows' interactive WSL installation flow. The user-visible run enabled/installed WSL components and reported that a reboot was required.

This is a preflight bug. A read-only feasibility probe must not invoke commands that can enable Windows optional features, install WSL components, install a distribution, or require a reboot.

Fix policy:

- Do not invoke `wsl.exe` during G0.
- Detect WSL feature state read-only through `Get-WindowsOptionalFeature -Online` for `Microsoft-Windows-Subsystem-Linux` and `VirtualMachinePlatform`.
- Report `WSL_FEATURE`, `VMP_FEATURE`, and `REBOOT_MAY_BE_REQUIRED` conservatively.
- WSL availability is informational only for G0 and does not affect the RTX 3060 4-bit feasibility gate.
- No model download and no package installation are allowed in G0.

The first real machine result remains useful for GPU/disk gating:

- NVIDIA GeForce RTX 3060
- 12 GiB VRAM class
- ~94 GiB disk free at the time of the run
- `G0_STATUS=READY_FOR_QUANTIZED_PROOF_ONLY`

That status means only that an isolated 4-bit loading proof is worth designing. It does not mean MOSS-Music 8B is proven to fit or run on the card.
