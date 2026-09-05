# Resolume Expert

You are an expert on controlling Resolume Avenue/Arena via `osc-mcp`'s
`resolume_manager` tool. Unlike Max/MSP, Resolume ships a real, fixed,
documented OSC namespace and turns OSC input on by default — but this
tool has now had **two** fabricated addresses caught and fixed
(`set_layer_opacity` earlier this session, `set_bpm` during this skill's
own research). Don't assume the rest is clean just because it looks
plausible.

## The chain: Resolume → OSC in (on by default) → osc-mcp

1. Resolume Avenue or Arena installed and running (demo mode: unlimited
   time, periodic black-frame overlay, no project save — enough to test
   OSC control; see `src/oscmcp/app_detect.py`, `key="resolume"`).
2. **OSC input is on by default on port 7000** — confirmed both in this
   repo's own `docs/ONBOARDING.md` ("Resolume: OSC input is on by default
   on port 7000; check Preferences → OSC if it doesn't respond") and
   `app_detect.py`'s `default_osc_port=7000` for `key="resolume"`. This is
   the one port default in this pair of apps that's actually verified —
   no guessing needed.
3. The addressable namespace is generated from the composition's actual
   layer/clip/effect layout — Resolume's own support docs
   (`resolume.com/support/en/osc`) say the address list "changes depending
   on how you have your composition set up," and recommend using
   Shortcuts → Edit OSC inside Resolume itself to read back the live
   address for anything not already nailed down below. The base hierarchy
   (`/composition/layers/{n}/...`, `/composition/tempocontroller/...`) is
   stable; the exact clip/layer count in a given composition is not.

## The real protocol: verified against Resolume's own OSC list

Verified against the official OSC address list Resolume itself ships
(`resolume.com/download/Manual/OSC/OSC list.txt`) and the support site's
OSC reference (`resolume.com/support/en/osc`) — not assumed from memory.

| Area | Address | Notes |
|---|---|---|
| Clip trigger | `/composition/layers/{n}/clips/{m}/connect` | int arg, `1` triggers, `0` = off (per official list) |
| Clip connected state | `/composition/layers/{n}/clips/{m}/connected` | readback |
| Layer opacity | `/composition/layers/{n}/video/opacity` | float `0.0`–`1.0`. **Confirmed the `/video/` segment is required** — this repo's own `CHANGELOG.md` documents that `/composition/layers/{n}/opacity` (no `/video/`) was verified live against Resolume Avenue 7.27.1 to be silently ignored. |
| Tempo/BPM | `/composition/tempocontroller/tempo` | **Fixed** — `resolume_manager` used to send `/transport/tempo`, which appears nowhere in this list. |
| Tempo nudge | `/composition/tempocontroller/tempoinc`, `tempodec`, `tempomultiplytwo`, `tempodividetwo`, `tempotap`, `tempopush`, `tempopull` | all present in the official list; none implemented by `resolume_manager` today (gap, not a bug) |

## `resolume_manager` — what osc-mcp actually implements

```python
resolume_manager(operation, host="127.0.0.1", port=7000, layer=None, column=None, opacity=None, bpm=None)
```

| Operation | Sends | Verified? |
|---|---|---|
| `play_clip` | `/composition/layers/{layer}/clips/{column}/connect`, `[1]` | **Matches the official list** — address structure and int arg both correct. |
| `set_layer_opacity` | `/composition/layers/{layer}/video/opacity`, `[opacity]` | **Correct, already fixed this session** — see CHANGELOG entry above. |
| `set_bpm` | `/composition/tempocontroller/tempo`, `[bpm]` | **Fixed** — used to send `/transport/tempo`, which appears nowhere in Resolume's official OSC list. |

## Known gaps

- ~~`set_bpm` sent `/transport/tempo`~~ — fixed to
  `/composition/tempocontroller/tempo`, the real address confirmed in
  Resolume's own shipped OSC list.
- **BPM value format is unresolved** (this part was *not* fixed - not
  primary-sourced enough to change confidently). Multiple independent (non-primary,
  forum-level) reports describe Resolume's tempo OSC input expecting a
  **normalized `0.0`–`1.0` float** mapped across a fixed BPM range
  (reportedly 20–500), not a raw BPM number — the same convention
  Resolume uses for opacity, clip triggers, etc. `resolume_manager`'s
  `set_bpm` currently sends the raw `bpm` argument straight through with
  no normalization. If confirmed, this would be a **second, independent**
  bug in the same operation on top of the wrong address. **Not verified
  against a primary source or a live instance** — flagging explicitly as
  "needs live testing," per this task's rule against inventing behavior.
- **Tempo nudge operations** (`tempoinc`/`tempodec`/`tempotap`/etc.) are
  real, documented addresses with no corresponding `resolume_manager`
  operation — gap, not a bug, mirroring the VCV skill's phrasing for
  `vcv_manager`'s missing `/encoder` support.
- **`play_clip` has no "clear"/disconnect counterpart** — only
  `connect=1` is ever sent; there's no way to send `0` or read back
  `connected` state through this tool today.
- **Composition-dependent addressing isn't surfaced anywhere in this
  tool.** Resolume's own docs stress that beyond the stable top-level
  hierarch, e.g. how many clips exist per layer, is composition-specific
  — a `layer`/`column` index that doesn't exist in the user's actual
  composition will silently no-op exactly like the OSCelot
  Send/Receive-off case in `vcv_manager`, with no error surfaced back to
  the caller.

## Best practices

1. **`set_bpm`'s address is now fixed, but the BPM value format is still
   unconfirmed** — if tempo doesn't change as expected, try a normalized
   0.0-1.0 value before assuming the address is wrong again.
2. **When in doubt about any address not in the table above, point the
   user at Shortcuts → Edit OSC inside Resolume itself** — that's
   Resolume's own documented way to get the exact live address for a
   given control, since composition-dependent addresses can't be
   hardcoded here.
3. **Port 7000 is the one genuinely verified default in this app pair** —
   no need to ask the user for it unless they've changed Resolume's own
   OSC preferences.
4. **If you find another address mismatch while working in this tool,
   flag it the same way this file does** — don't silently correct it in
   passing; the opacity fix and this file both treat that as a separate,
   deliberate, verified change, not a drive-by edit.

## Primary sources

- `resolume.com/download/Manual/OSC/OSC list.txt` — the actual OSC address
  list Resolume itself ships/distributes; primary source for every
  address in the table above except the BPM normalization claim
- `resolume.com/support/en/osc` — official support-site OSC reference;
  confirms composition-dependent addressing and points users at
  Shortcuts → Edit OSC for live lookup
- `CHANGELOG.md` (this repo) — exact wording of the already-fixed
  `set_layer_opacity` bug, verified live against Resolume Avenue 7.27.1
- `src/oscmcp/app_detect.py` (this repo, `key="resolume"`) — verified
  `default_osc_port=7000`, install paths, demo-mode notes
- `src/oscmcp/mcp_server.py` (this repo, `resolume_manager` at line 2565)
  — the actual operations and addresses this tool sends today
- `docs/ONBOARDING.md` (this repo) — confirms OSC-on-by-default on port
  7000
