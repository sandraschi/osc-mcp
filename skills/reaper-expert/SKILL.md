# REAPER Expert

## What is REAPER

A professional, low-cost DAW (Digital Audio Workstation) by Cockos, known
for its deep customizability - nearly every part of its behavior can be
scripted (ReaScript in Lua/EEL2/Python), and its routing is unusually
flexible compared to most DAWs. Widely used for recording, editing,
mixing, and mastering; popular specifically because it's inexpensive,
fully portable (no installer required), and endlessly extensible.

**Core features:** unlimited tracks/routing/sends, a native scripting API
(ReaScript) for automating almost anything, a large third-party
extension/plugin ecosystem, flexible project-file-based configuration,
and — the reason it's relevant here — real, native, built-in OSC control
that doesn't need a bridge or remote script the way Ableton or OBS do.

## Orthogonal to `reaper-mcp` - read this before doing anything else

This fleet already has a **separate, dedicated `reaper-mcp` server**
(6 portmanteau tools: transport, tracks, project, system, ReaScript,
orchestrator - plus its own OSC client and `reapy-boost`/ReaScript access
for things OSC can't reach at all, like track enumeration or rendering).
That's the right tool for anyone doing real REAPER automation.

`osc-mcp` itself only touches REAPER in three narrow spots, all inside
cross-app orchestration tools (`music_loader_manager`, `audio_workflow_manager`)
whose actual job is keeping REAPER's transport/tempo in sync *alongside
other OSC gear* (VCV Rack, in this repo's case) - e.g. "start REAPER and
VCV Rack's transport at the same moment." It was never meant to be a
REAPER control surface, and this skill's scope matches that: verifying
and fixing what `osc-mcp` already sends, not building out REAPER
coverage that belongs in `reaper-mcp` instead. If a user wants real
REAPER control (track management, rendering, ReaScript), point them at
`reaper-mcp`, not this tool.

## The real protocol: a *configurable* pattern, not a fixed one

Unlike most apps in this fleet, REAPER's OSC address space isn't fixed by
the app itself - Preferences → Control/OSC/web lets a user load any
`.ReaperOSC` pattern-config text file, and the file's contents literally
define what address triggers what. What follows describes REAPER's own
**shipped default** pattern config (`Default.ReaperOSC`), verified
against a real copy of that file, not assumed. If a user has swapped in a
custom pattern config, none of this necessarily still applies - always
ask before assuming.

Argument-type flags matter and are easy to get wrong:

| Flag | Meaning | Example |
|---|---|---|
| `n` | Normalized float, 0.0 (min) to 1.0 (max) | `/track/volume 0.5` = fader at the midpoint, not "50% loudness" |
| `f` | Raw float, interpreted directly | `/tempo/raw 100.351` sets tempo to exactly 100.351 BPM |
| `b` | Binary 0/1, explicit on/off | `/track/3/mute 1` mutes, `/track/3/mute 0` unmutes |
| `t` | Trigger/toggle - fires with no argument or `1` | `/play` (no args) starts playback |
| `i` | Integer argument | `/action 40042` triggers REAPER action 40042 by command ID |

Relevant real actions from `Default.ReaperOSC` (not guessed):

| Action | Pattern(s) | Notes |
|---|---|---|
| PLAY | `t/play` | Trigger, no args needed |
| STOP | `t/stop` | Trigger |
| PAUSE | `t/pause` | Trigger |
| RECORD | `t/record` | Trigger |
| REWIND | `b/rewind` | **Binary hold gesture** - `1` begins continuous rewind, `0` stops it. Not a jump-to-position action. |
| TEMPO | `n/tempo`, `f/tempo/raw`, `r/tempo/rotary`, `s/tempo/str` | `/tempo` alone is **normalized 0.0-1.0**; `/tempo/raw` takes an actual BPM number |
| TRACK_VOLUME | `n/track/volume`, `n/track/@/volume` (fader position), `f/track/volume/db`, `f/track/@/volume/db` (dB) | Bare/`n` variant is normalized fader position, not loudness in any linear sense - depends on REAPER's fader taper preference |
| TRACK_MUTE | `b/track/@/mute`, `t/track/@/mute/toggle` | Explicit set (`b`) or toggle (`t`) - `osc-mcp` doesn't use this today |
| TRACK_SOLO | `b/track/@/solo`, `t/track/@/solo/toggle` | Same shape as mute |
| ACTION | `i/action`, `t/action/@` | Generic escape hatch - triggers **any** REAPER action by its numeric command ID. There is no dedicated "go to start of project" address; the real way to do that is `/action 40042` (confirmed against REAPER's own action list) |

**There is no marker-creation action anywhere in the default config** -
only navigating to an existing marker (`GOTO_MARKER`) and reading/renaming
one by index or ID (`MARKER_NAME`/`MARKER_TIME`/`MARKERID_*`). Worth
knowing: `reaper-mcp`'s own `osc_client.py` sends `/marker/add` for its
`add_marker()` method, which doesn't correspond to any action in
REAPER's real default pattern config either - flagging for awareness,
not fixing (separate repo, out of scope here).

## What `osc-mcp` actually sends (three call-sites, all in `mcp_server.py`)

| Tool / operation | Sends to REAPER | Verdict |
|---|---|---|
| `music_loader_manager("start_performance")` | `/play`, `[]` | Correct |
| `music_loader_manager("stop_performance")` | `/stop`, `[]` | Correct |
| `audio_workflow_manager("sync_tempo_all")` | `/tempo/raw`, `[bpm]` | **Fixed** - used to send bare `/tempo`, which is normalized 0.0-1.0, not a raw BPM value |
| `audio_workflow_manager("start_all")` | `/play`, `[]` | Correct |
| `audio_workflow_manager("stop_all")` | `/stop`, `[]` | Correct |
| `audio_workflow_manager("reset_all")` | `/action`, `[40042]` | **Fixed** - used to send `/rewind` with no argument, which (a) is a continuous hold-to-rewind gesture, not a jump-to-start action, and (b) sent no argument at all where the real protocol needs an explicit 1/0. Now triggers REAPER's real "Transport: Go to start of project" action by ID instead. |
| `music_loader_manager`'s Bach-organ setup step | `/track/1/volume`, `[0.8]` | Correct - matches the real normalized fader-position convention |

## Known gaps

- **Port (8000) and host default are consistent** across all three
  call-sites and match `reaper-mcp`'s own default - unlike several other
  apps in this fleet, this one wasn't internally inconsistent.
- **`reset_all`'s REAPER fix depends on the default pattern config being
  loaded.** If a user has swapped in a custom `.ReaperOSC` file, action ID
  40042 still works (action IDs are global, not pattern-config-specific),
  but any address-based operation in this table could differ.
- **No feedback/read path.** None of these tools listen for REAPER's own
  OSC feedback (e.g. `/play 1` echoed back on transport state change) -
  fire-and-forget only, same as every other manager in this fleet.
- **The other REAPER-adjacent addresses in `music_loader_manager`'s
  `load_bach_organ`/`load_midi_file`/`setup_organ_rig` operations are
  actually VCV Rack addresses** (`/param`, `/module/add`, `/connect`,
  `/transport/play`) - unrelated to REAPER, and themselves unverified/
  likely fabricated against OSCelot's real slot-addressed protocol (see
  `skills/vcvrack-expert/`). Out of scope for this skill, flagging for
  awareness since it's in the same functions.

## Best practices

1. **Point real REAPER automation requests at `reaper-mcp`**, not this
   tool - `osc-mcp`'s REAPER support exists only to keep REAPER in sync
   with other OSC gear inside a couple of orchestration tools.
2. **Never assume `/tempo` sets a BPM value** - it's normalized 0.0-1.0.
   Use `/tempo/raw` for an actual BPM number.
3. **`/rewind` is a hold gesture, not a seek** - don't reach for it to
   jump to a specific position; use `/action <command_id>` with a real,
   verified action ID instead (REAPER's own Action List, or the
   Ultraschall-maintained action-list reference, has the numbers).
4. **If a user has a custom `.ReaperOSC` pattern config loaded, none of
   the addresses above are guaranteed to still apply** - ask what pattern
   config they're using before assuming the defaults hold.

## Primary sources

- `reaper.fm/sdk/osc/osc.php` - REAPER's own official OSC SDK
  documentation (pattern-config format, argument-type flags)
- `github.com/Ultraschall/ultraschall-portable/blob/master/Plugins/Default.ReaperOSC` -
  a real copy of REAPER's shipped default pattern config, fetched and
  read directly (not summarized from memory) for every address in the
  tables above
- Ultraschall's compiled REAPER action list
  (`ultraschall-lua-api-for-reaper` repo, `Reaper-ActionList.txt`) -
  confirms command ID `40042` = "Transport: Go to start of project"
- `src/oscmcp/mcp_server.py` (this repo) - `music_loader_manager` and
  `audio_workflow_manager`, the actual REAPER call-sites this skill
  documents
- `reaper-mcp/reaper_mcp/osc_client.py`, `reaper-mcp/README.md`,
  `reaper-mcp/CLAUDE.md` (sibling repo) - confirms the orthogonal,
  dedicated REAPER automation server this skill defers to
