"""Generates the raw synthetic cohort via Synthea (Apache-2.0, MITRE Corporation).

Deliberately shells out to the upstream jar rather than reimplementing
patient generation — Synthea's clinical modules are the actual research
asset here; nothing about them is worth re-deriving.

Reproducibility: every parameter that controls the generated population
(seed, size, state, which CSV tables are exported) lives in the committed
`data/synthea.config.json`, never as a flag typed once and forgotten.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "data" / "synthea.config.json"
TOOLS_DIR = REPO_ROOT / ".tools"
JAR_PATH = TOOLS_DIR / "synthea-with-dependencies.jar"
OUTPUT_DIR = REPO_ROOT / "data" / "synthea"

SYNTHEA_JAR_URL = (
    "https://github.com/synthetichealth/synthea/releases/download/"
    "master-branch-latest/synthea-with-dependencies.jar"
)


def _find_java() -> str:
    """Looks on PATH first, then a common user-local install location (no
    root required — see docs/PLAN.md §Phases, Phase 1). Raises with an exact
    fix rather than silently installing anything on the caller's behalf.
    """
    on_path = shutil.which("java")
    if on_path:
        return on_path

    local_opt = Path.home() / ".local" / "opt"
    for candidate in sorted(local_opt.glob("jdk-*")):
        java_bin = candidate / "bin" / "java"
        if java_bin.exists():
            return str(java_bin)

    raise SystemExit(
        "No Java runtime found. Synthea needs a JDK 17+. To install one "
        "without root, run:\n\n"
        "  mkdir -p ~/.local/opt && cd ~/.local/opt\n"
        "  curl -sL -o jdk.tar.gz "
        "'https://api.adoptium.net/v3/binary/latest/17/ga/linux/x64/jdk/hotspot/normal/eclipse'\n"
        "  tar xzf jdk.tar.gz && rm jdk.tar.gz\n"
    )


def _ensure_jar() -> Path:
    if JAR_PATH.exists():
        return JAR_PATH
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading Synthea jar from {SYNTHEA_JAR_URL} ...")
    urllib.request.urlretrieve(SYNTHEA_JAR_URL, JAR_PATH)  # noqa: S310 - fixed, pinned upstream URL
    print(f"Saved to {JAR_PATH} ({JAR_PATH.stat().st_size / 1e6:.0f} MB)")
    return JAR_PATH


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text())
    java = _find_java()
    jar = _ensure_jar()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        java,
        "-jar",
        str(jar),
        "-s",
        str(config["seed"]),
        "-p",
        str(config["population_size"]),
        f"--exporter.baseDirectory={OUTPUT_DIR}/",
        "--exporter.fhir.export=false",
        "--exporter.csv.export=true",
        "--exporter.hospital.fhir.export=false",
        "--exporter.practitioner.fhir.export=false",
        "--exporter.csv.included_files=" + ",".join(config["included_csv_files"]),
        config["state"],
    ]
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=REPO_ROOT)  # noqa: S603 - fixed argv, no shell
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
