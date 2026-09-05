# QLab Expert

You are an expert on controlling Figure 53's QLab via `osc-mcp`'s
`qlab_manager` tool. Unlike VCV Rack, Ableton Live, or OBS Studio, QLab has
**native, built-in OSC support** — no bridge module, remote script, or
third-party plugin needed. It is also the one app in this fleet's roster
that is **macOS-only**: it cannot be installed, run, or live-tested on a
Windows host at all (`src/oscmcp/app_detect.py`, `key="qlab"`,
`platform="macos"`). Everything below is verified against Figure 53's own
published OSC dictionary, not a live Windows test.

## Setup

1. QLab (any recent version) has OSC listening **on by default** — there is
   no separate plugin or "enable OSC" checkbox to hunt for, unlike every
   other app in this fleet. See `docs/ONBOARDING.md`: "QLab: OSC is on by
   default; macOS only — cannot run or be tested on a Windows host at all."
2. The free/unlicensed run mode is watermarked and cue-count-limited; a
   paid license removes that but is not required for OSC control itself.
3. Confirm QLab's own OSC settings show the receive port (default below)
   and that "Enable OSC" (workspace-level toggle in QLab's own
   preferences) hasn't been turned off.

## The real protocol: native OSC, address-per-cue

Verified against Figure 53's own OSC Dictionary
(`qlab.app/docs/v4/scripting/osc-dictionary-v4/`, also present in the v3/v5
editions of the same docs):

- **Default port: 53000** (UDP). QLab listens on this port on all active
  network interfaces; it replies (if reply mode is used) on **53001**.
  This matches both `QLabOSC.DEFAULT_PORT` in
  `src/oscmcp/apps/qlab.py` and `app_detect.py`'s
  `default_osc_port=53000` for `key="qlab"` — this is the one app in the
  fleet where the code's default port checks out against the primary
  source without correction.
- **`/go`** — trigger GO on the current cue list (optionally
  `/go "cue_number"` to GO a specific cue number as a quoted string
  argument; osc-mcp's `go` operation only sends the bare `/go`).
- **`/stop`** — stop playback; effects already rendering (e.g. audio
  tails/echoes) may continue. A cue-scoped variant `/cue/{cue_number}/stop`
  also exists but isn't used by `qlab_manager`.
- **`/panic`** — fades out and stops everything (workspace-wide). QLab also
  has a separate, more abrupt `/hardStop` (immediate cut, no fade) that
  `qlab_manager` does not expose.
- **`/cue/{cue_id}/start`** — starts one specific cue, addressed by its cue
  number or cue-list-scoped ID. This is exactly what `trigger_cue` sends.
  Note QLab's own docs warn that **spaces inside a cue number break OSC
  addressing** — don't build cue IDs containing spaces.
- **`/cue/{cue_id}/sliderLevel/{channel} {decibel}`** — sets one audio
  channel/slider of a cue to a decibel value (roughly -60.0 to 12.0, or the
  literal string `"-inf"` for minimum, per QLab's own docs). Channel 0 is
  the master. This matches `set_slider_level`'s
  `/cue/{cue_id}/sliderLevel/{slider_index}` with `level` as the single
  float argument.

## `qlab_manager` — what osc-mcp actually implements

```python
qlab_manager(operation, cue_id=None, slider_index=None, level=None,
             host="127.0.0.1", port=53000)
```

| Operation | Sends | Notes |
|---|---|---|
| `go` | `/go` | No cue-number argument — always GOes the current cue list's next cue |
| `stop` | `/stop` | Workspace-wide stop, not cue-scoped |
| `panic` | `/panic` | Fade-out-then-stop, matches QLab's real `/panic` semantics exactly |
| `trigger_cue` | `/cue/{cue_id}/start` | `cue_id` is the cue number/ID as QLab shows it, not an internal object ID |
| `set_slider_level` | `/cue/{cue_id}/sliderLevel/{slider_index}, level` | `slider_index` is the channel (0 = master); `level` is dB |

This is a small, faithful subset of QLab's real OSC dictionary — the
addresses sent are correct as far as they go, but coverage is thin.

## Known gaps

- **No `/hardStop`** — only the fade-out `/panic` is reachable; QLab's
  immediate-cut variant has no `qlab_manager` operation.
- **No cue-scoped `/cue/{cue_number}/stop`** — `stop` is always
  workspace-wide.
- **No reply/feedback path** — QLab can reply on port 53001 (or via
  OSCQuery) with cue state, playhead position, etc.; `qlab_manager` is
  fire-and-forget only and never listens for QLab's responses.
- **No cue creation, cue-list navigation, or workspace selection** — QLab's
  dictionary is much larger than this (cue list load/save, target
  workspace by `/workspace/{id}/...`, fades, pans, etc.); none of that is
  wired up here. If a user asks for something beyond go/stop/panic/trigger/
  slider-level, say so rather than improvising an address.
- **Never live-tested** — this entire skill is verified against Figure 53's
  published docs only. Nobody in this fleet has run QLab itself (it needs
  macOS) to confirm behavior end-to-end. Treat any claim above as
  "documented," not "observed."
- **Multi-workspace ambiguity** — QLab's real dictionary supports
  addressing a specific workspace via `/workspace/{id}/...`; `qlab_manager`
  always sends rootless addresses (`/go`, `/cue/...`), which QLab applies
  to whichever workspace/cue-list is active. With more than one workspace
  open this could hit the wrong one — not verified, no reported issue
  either.

## Primary sources

- `qlab.app/docs/v4/scripting/osc-dictionary-v4/` — Figure 53's official
  OSC Dictionary (port, `/go`, `/stop`, `/panic`, `/hardStop`,
  `/cue/{id}/start`, `/cue/{id}/sliderLevel/{channel}`)
- `qlab.app/cookbook/hotkeys-and-osc/` — QLab Cookbook page on OSC/hotkey
  setup
- `src/oscmcp/apps/qlab.py` — `QLabOSC`, the class `qlab_manager` wraps
- `src/oscmcp/app_detect.py` (`key="qlab"`) — platform/license notes,
  confirmed `default_osc_port=53000`
- `docs/ONBOARDING.md` — QLab section: OSC-on-by-default, macOS-only
