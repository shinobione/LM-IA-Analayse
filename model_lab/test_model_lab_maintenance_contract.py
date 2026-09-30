from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def main() -> int:
    cleanup = (REPO / "SONICTRACE_V4_MODEL_LAB_CLEANUP.cmd").read_text(encoding="utf-8")
    preflight = (REPO / "SONICTRACE_V4_MOSS_MUSIC_G_PREFLIGHT.cmd").read_text(encoding="utf-8")
    verdict_f = (ROOT / "BENCHMARK-VERDICT-2026-08-18-CANDIDATE-F.md").read_text(encoding="utf-8")
    feasibility_g = (ROOT / "CANDIDATE-G-FEASIBILITY-2026-08-18.md").read_text(encoding="utf-8")

    # Cleanup is local Model Lab maintenance only. Benchmark reports are never
    # removed by any default option, and product/backend paths are not deletion targets.
    assert 'set "RUNTIME=%LAB%\\.runtime"' in cleanup
    assert 'set "RESULTS=%LAB%\\results"' in cleanup
    assert 'rmdir /s /q "%RESULTS%"' not in cleanup
    assert 'rmdir /s /q "%ROOT%backend' not in cleanup
    assert 'rmdir /s /q "%ROOT%js' not in cleanup
    assert 'rmdir /s /q "%ROOT%studio' not in cleanup.lower()
    assert "Catalogue V2-E" in cleanup
    assert "SHINOBIWAN STUDIO" in cleanup

    safe = cleanup.split(":safe", 1)[1].split(":strong", 1)[0]
    assert '%RUNTIME%\\muq_venv' not in safe
    assert 'call :remove_dir "%RUNTIME%\\venv"' not in safe
    assert 'call :remove_dir "%RUNTIME%\\clamp3"' not in safe
    for rejected in (
        "msclap_venv",
        "larger_clap_venv",
        "native_laion_music_venv",
        "m2d_clap_2025_venv",
        "m2d_clap_2025_src",
    ):
        assert rejected in safe

    strong = cleanup.split(":strong", 1)[1].split(":all", 1)[0]
    assert '%RUNTIME%\\muq_venv' not in strong
    assert 'call :remove_dir "%RUNTIME%\\venv"' in strong
    assert 'call :remove_dir "%RUNTIME%\\clamp3"' in strong
    assert 'call :remove_dir "%RUNTIME%"' not in strong

    wipe = cleanup.split(":all", 1)[1].split(":sizes", 1)[0]
    assert 'call :remove_dir "%RUNTIME%"' in wipe
    assert "NE supprimera PAS model_lab\\results" in wipe

    # Candidate G0 is intentionally read-only. The first real Windows run showed
    # that merely invoking wsl.exe can trigger Windows' interactive WSL install
    # path even when the binary exists. G0 must therefore never execute WSL,
    # install packages, enable Windows features, or load/download MOSS weights.
    assert "MOSS-Music-8B-Instruct" in preflight
    assert "ZERO MODEL DOWNLOAD" in preflight
    assert "ZERO OS FEATURE INSTALL" in preflight
    assert "nvidia-smi" in preflight
    assert "DISK_FREE_GIB" in preflight
    assert "BINARY_PRESENT_UNPROBED" in preflight
    assert "REBOOT_STATUS" in preflight
    assert "READY_FOR_QUANTIZED_PROOF_ONLY" in preflight
    assert "moss-music-g0-preflight-" in preflight
    assert "wsl.exe --version" not in preflight.lower()
    assert "wsl.exe --status" not in preflight.lower()
    assert "wsl.exe --install" not in preflight.lower()
    assert "enable-windowsoptionalfeature" not in preflight.lower()
    assert "dism /online /enable-feature" not in preflight.lower()
    assert "hf download" not in preflight.lower()
    assert "huggingface-cli download" not in preflight.lower()
    assert "pip install" not in preflight.lower()
    assert "from_pretrained" not in preflight

    # Real Candidate F result is closed honestly; no benchmark/taxonomy tuning.
    assert "0 PASS / 1 NEAR / 3 FAIL" in verdict_f
    assert "REJECTED FOR QUALITY" in verdict_f
    assert "declared_metadata_used_for_inference = false" in verdict_f
    assert "MuQ-MuLan remains the raw quality reference" in verdict_f

    # Candidate G remains a feasibility gate only until 4-bit operation is proven.
    assert "ad107c7ddaa06de168a0dfbc18d3e1e6a40c0e5e" in feasibility_g
    assert "Apache-2.0" in feasibility_g
    assert "DO NOT DOWNLOAD YET" in feasibility_g
    assert "BF16 / FP16" in feasibility_g
    assert "Potentially feasible, but unproven" in feasibility_g
    assert "Proceed with G0 preflight only" in feasibility_g
    assert "No SonicTrace V3, Catalogue V2-E or SHINOBIWAN STUDIO integration" in feasibility_g

    print("SonicTrace V4 Model Lab maintenance / Candidate G0 contract PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
