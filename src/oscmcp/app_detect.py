"""Install/process detection for the external host apps this server wraps via OSC.

Mirrors the obs-mcp `obs_detect.py` pattern (detect installations, detect a
running process) but generalized across the 9+ apps this server wraps -
those apps live at very different paths, some with version numbers baked
into the install directory, so each entry uses a glob pattern rather than a
fixed path.

Never launches anything - that's a separate, explicit-user-action concern
(see the fleet.py launch pattern), not part of detection.
"""

from __future__ import annotations

import glob
import logging
from dataclasses import dataclass

import psutil

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AppSpec:
    """Static, per-app detection metadata."""

    key: str
    display_name: str
    path_globs: list[str]
    process_names: list[str]
    default_osc_port: int | None
    license: str  # "free" | "commercial" | "commercial-trial" | "hardware"
    platform: str  # "windows" | "macos" | "cross-platform"
    download_url: str
    notes: str = ""


@dataclass
class AppStatus:
    key: str
    display_name: str
    installed: bool
    installed_path: str | None
    running: bool
    process_pid: int | None
    default_osc_port: int | None
    license: str
    platform: str
    download_url: str
    testable_here: bool
    notes: str


# Path globs use Windows Program Files conventions since that's this server's
# primary deployment target; installs elsewhere (custom drive, portable) won't
# be detected and that's a known, accepted limitation of glob-based detection.
APP_SPECS: list[AppSpec] = [
    AppSpec(
        key="ableton",
        display_name="Ableton Live",
        path_globs=[
            r"C:\ProgramData\Ableton\Live*\Program\Ableton Live*.exe",
            r"C:\Program Files\Ableton\Live*\Program\Ableton Live*.exe",
        ],
        process_names=["Ableton Live 10 Suite.exe", "Ableton Live 11 Suite.exe", "Ableton Live 12 Suite.exe"],
        default_osc_port=11000,
        license="commercial-trial",
        platform="windows",
        download_url="https://www.ableton.com/en/trial/",
        notes=(
            "Ableton Live has NO native OSC support. This server's ableton_manager assumes the "
            "third-party AbletonOSC remote script (github.com/ideoforms/AbletonOSC) is installed "
            "into Live's Remote Scripts folder and enabled in Preferences > Link/Tempo/MIDI. "
            "Without it, every send is a silent no-op - Live never receives anything."
        ),
    ),
    AppSpec(
        key="touchdesigner",
        display_name="TouchDesigner",
        path_globs=[r"C:\Program Files\Derivative\TouchDesigner\bin\TouchDesigner.exe"],
        process_names=["TouchDesigner.exe"],
        default_osc_port=9000,
        license="commercial",
        platform="windows",
        download_url="https://derivative.ca/download",
        notes="Free non-commercial license available. Needs an OSC In CHOP/DAT configured inside the .toe project to receive.",
    ),
    AppSpec(
        key="vrchat",
        display_name="VRChat",
        path_globs=[
            r"C:\Program Files (x86)\Steam\steamapps\common\VRChat\VRChat.exe",
            r"C:\Program Files\Steam\steamapps\common\VRChat\VRChat.exe",
        ],
        process_names=["VRChat.exe"],
        default_osc_port=9000,
        license="free",
        platform="windows",
        download_url="https://store.steampowered.com/app/438100/VRChat/",
        notes="Free client + free Steam/VRChat account. OSC must be enabled in-game: Settings > OSC > Enabled.",
    ),
    AppSpec(
        key="vcvrack",
        display_name="VCV Rack",
        path_globs=[r"C:\Program Files\VCV\Rack2*\Rack.exe", r"C:\Program Files\VCV\Rack\Rack.exe"],
        process_names=["Rack.exe"],
        default_osc_port=None,  # OSCelot's receive port is fully user-configured, no fixed default
        license="free",
        platform="cross-platform",
        download_url="https://vcvrack.com/",
        notes=(
            "Free (Rack 2 Free edition). Needs OSCelot (via the VCV Library, needs a "
            "free VCV account) patched in and each parameter manually mapped to a slot - "
            "see docs/OSCELOT_MAPPING_GUIDE.md. No direct module/param OSC addressing exists."
        ),
    ),
    AppSpec(
        key="supercollider",
        display_name="SuperCollider",
        path_globs=[r"C:\Program Files\SuperCollider-*\scide.exe"],
        process_names=["scsynth.exe", "scide.exe", "sclang.exe"],
        default_osc_port=57110,
        license="free",
        platform="cross-platform",
        download_url="https://supercollider.github.io/",
        notes="Free/open-source. scsynth.exe (the audio server) is what actually answers OSC - running scide.exe alone isn't enough.",
    ),
    AppSpec(
        key="maxmsp",
        display_name="Max/MSP",
        path_globs=[r"C:\Program Files\Cycling '74\Max*\Max.exe"],
        process_names=["Max.exe"],
        default_osc_port=7400,
        license="commercial-trial",
        platform="windows",
        download_url="https://cycling74.com/downloads",
        notes="30-day full-featured trial. Needs udpreceive/udpsend or [oscformat]/[oscparse] objects patched in.",
    ),
    AppSpec(
        key="resolume",
        display_name="Resolume Avenue/Arena",
        path_globs=[r"C:\Program Files\Resolume Avenue\Avenue.exe", r"C:\Program Files\Resolume Arena\Arena.exe"],
        process_names=["Avenue.exe", "Arena.exe"],
        default_osc_port=7000,
        license="commercial-trial",
        platform="windows",
        download_url="https://resolume.com/download",
        notes="Unlimited-time demo mode (periodic black-frame overlay, no project save) - good enough to test OSC control.",
    ),
    AppSpec(
        key="qlab",
        display_name="QLab",
        path_globs=[],
        process_names=[],
        default_osc_port=53000,
        license="commercial-trial",
        platform="macos",
        download_url="https://qlab.app/",
        notes="macOS-only - cannot be installed or detected on a Windows host at all. Free to run with a watermark; full save needs a license.",
    ),
    AppSpec(
        key="puredata",
        display_name="Pure Data",
        path_globs=[r"C:\Program Files\PD\bin\pd.exe", r"C:\Program Files\Pd*\bin\pd.exe"],
        process_names=["pd.exe"],
        default_osc_port=9000,
        license="free",
        platform="cross-platform",
        download_url="https://puredata.info/downloads",
        notes="Free/open-source. Needs [netreceive]/[netsend] or the OSC library patched in to bridge to/from this server.",
    ),
    AppSpec(
        key="obs",
        display_name="OBS Studio (WebSocket bridge)",
        path_globs=[r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"],
        process_names=["obs64.exe", "obs32.exe"],
        default_osc_port=None,
        license="free",
        platform="cross-platform",
        download_url="https://obsproject.com/download",
        notes="Connects via obs-websocket (built into OBS 28+), not OSC. See docs/OBS_PLUGINS_GUIDE.md.",
    ),
]

_SPECS_BY_KEY = {s.key: s for s in APP_SPECS}


def _resolve_glob(patterns: list[str]) -> str | None:
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    return None


def _find_process(names: list[str]) -> int | None:
    if not names:
        return None
    wanted = {n.lower() for n in names}
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if (proc.info.get("name") or "").lower() in wanted:
                return proc.info["pid"]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def detect_app(key: str) -> AppStatus:
    """Detect install + running status for one app. Never launches anything."""
    spec = _SPECS_BY_KEY[key]
    installed_path = _resolve_glob(spec.path_globs)
    pid = _find_process(spec.process_names)
    return AppStatus(
        key=spec.key,
        display_name=spec.display_name,
        installed=installed_path is not None,
        installed_path=installed_path,
        running=pid is not None,
        process_pid=pid,
        default_osc_port=spec.default_osc_port,
        license=spec.license,
        platform=spec.platform,
        download_url=spec.download_url,
        testable_here=spec.platform != "macos",
        notes=spec.notes,
    )


def detect_all() -> list[AppStatus]:
    """Detect every wrapped app. O(n * process count) - fine for a manual onboarding check, not for polling."""
    return [detect_app(spec.key) for spec in APP_SPECS]
