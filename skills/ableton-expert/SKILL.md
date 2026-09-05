# Ableton Live Expert

## What is Ableton Live

A professional DAW (Digital Audio Workstation) for music production,
recording, arranging, mixing, and live performance. Its distinguishing
feature is **Session View** — a grid of audio/MIDI clips you can launch and
combine live, non-linearly, alongside the traditional linear **Arrangement
View** most DAWs only have.

**Core features:** multitrack audio/MIDI recording and editing, built-in
instruments/samplers/effects, audio warping and time-stretching,
clip-based live performance (Session View), Max for Live (visual-patching
extension for building custom devices), extensive VST/AU plugin support.

You are an expert on controlling Ableton Live via `osc-mcp`'s `ableton_manager`
tool. Live has **no native OSC support at all** — every address this tool
sends only means something if the third-party **AbletonOSC** remote script
is installed and enabled. Get that wrong and every call is a silent UDP
no-op: no error anywhere, nothing happens in Live.

## The chain: Ableton Live → AbletonOSC → osc-mcp

1. **AbletonOSC** (by ideoforms, `github.com/ideoforms/AbletonOSC`) must be
   downloaded and its folder copied into Live's Remote Scripts directory
   (platform-specific location under Live's user library — see the
   project's own README for the exact path per OS/Live version).
2. Restart Live, then select **"AbletonOSC"** as a Control Surface in
   Preferences → Link/Tempo/MIDI.
3. Only then does Live bind AbletonOSC's UDP listener. Before that, sending
   OSC to Live's machine does nothing and Live's log gives no indication
   OSC was ever attempted.

There is no in-Live settings toggle for this — unlike VRChat's
Settings → OSC → Enabled, Ableton itself has zero OSC awareness. AbletonOSC
*is* the entire OSC layer.

## The real protocol: fixed REST-like address tree, verified against AbletonOSC's own README

AbletonOSC listens on **port 11000** and sends replies on **port 11001**
(from its own README — these are fixed by the script, not user-configured,
which is why `ableton_manager`'s `port=11000` default is correct). Addresses
follow a `/live/<object>/<action>` or `/live/<object>/set|get/<property>`
pattern; `get` variants are queries, not used by `ableton_manager` today.

Relevant excerpt of AbletonOSC's real Song API (verified against its README
table, not guessed):

| Address | Args | Notes |
|---|---|---|
| `/live/song/start_playing` | none | Start session playback |
| `/live/song/stop_playing` | none | Stop session playback |
| `/live/song/stop_all_clips` | none | Stop all clips |
| `/live/song/set/tempo` | `tempo_bpm` (float) | Set song tempo |
| `/live/song/get/tempo` | none | Query tempo |
| `/live/song/tap_tempo` | none | Mimics the Tap Tempo button |
| `/live/track/set/volume` | `track_id, volume` (float 0.0–1.0) | |
| `/live/track/set/panning` | `track_id, pan` (float -1.0–1.0) | |
| `/live/track/set/mute` | `track_id, mute` (0/1) | |
| `/live/track/set/solo` | `track_id, solo` (0/1) | |
| `/live/clip/fire` | `track_id, clip_id` | Starts clip playback |
| `/live/clip/stop` | `track_id, clip_id` | Stops clip |
| `/live/clip_slot/fire` | `track_index, clip_index` | Toggles play/pause of that slot |
| `/live/scene/fire` | `scene_id` | Triggers an entire scene row |

There is no `/live/play`, `/live/stop`, or `/live/tempo` address anywhere in
AbletonOSC's real address space — confirmed by a literal search of its
README. Those three strings simply do not exist in the protocol.

## `ableton_manager` — what osc-mcp actually implements

```python
ableton_manager(operation, host="127.0.0.1", port=11000, track_index=None,
                 clip_slot=None, bpm=None, volume=None, pan=None)
```

| Operation | Sends | Matches real AbletonOSC? |
|---|---|---|
| `play` | `/live/song/start_playing`, `[]` | **Fixed** — used to send `/live/play`, which AbletonOSC has no handler for (silent no-op) |
| `stop` | `/live/song/stop_playing`, `[]` | **Fixed** — used to send `/live/stop` |
| `set_tempo` | `/live/song/set/tempo`, `[bpm]` | **Fixed** — used to send `/live/tempo` |
| `play_clip` | `/live/clip/fire`, `[track_index, clip_slot]` | Yes — matches the real address and argument order exactly. |
| `set_volume` | `/live/track/set/volume`, `[track_index, volume]` | Yes — matches exactly, including the documented 0.0–1.0 range. |
| `set_pan` | `/live/track/set/panning`, `[track_index, pan]` | Yes — matches exactly, including the documented -1.0–1.0 range. |

**Known gaps:**

1. ~~`play`, `stop`, and `set_tempo` sent addresses AbletonOSC does not
   recognize~~ — fixed to send `/live/song/start_playing`,
   `/live/song/stop_playing`, and `/live/song/set/tempo` respectively.
2. **`set_tempo`'s real valid range** is documented informally as roughly
   20–999 BPM by Live's own tempo field limits, not a hard range AbletonOSC
   itself enforces — don't assume AbletonOSC will clamp or validate; Live's
   own UI does.
3. **No mute, solo, or send-level operations** are exposed by
   `ableton_manager` even though AbletonOSC documents
   `/live/track/set/mute`, `/live/track/set/solo`, and
   `/live/track/set/send` — a real gap in coverage, not a bug, since no
   existing operation claims to do this and fails silently.
4. **No clip-slot toggle (`/live/clip_slot/fire`) or scene-fire
   (`/live/scene/fire`) operation** exists in `ableton_manager` — only the
   `/live/clip/fire` variant is reachable via `play_clip`.
5. **`track_id` vs `track_index` naming**: AbletonOSC's own docs call the
   first argument `track_id`/`track_index` inconsistently across its own
   README sections; empirically it is a 0-based track index in Live's
   track list, matching what `ableton_manager`'s `track_index` parameter
   assumes. Not verified against a live Ableton instance in this pass —
   flagging as consistent-with-docs, not independently re-tested.

## Best Practices

1. **Confirm AbletonOSC is actually selected as a Control Surface** in
   Preferences before assuming a silent failure is `osc-mcp`'s fault —
   this is the single most common reason nothing happens, exactly as with
   VCV Rack's OSCelot Send/Receive toggles.
2. **Port 11000 is a real fixed default**, not a guess — unlike VCV Rack's
   OSCelot (no default) or TouchDesigner's user-configured OSC In CHOP,
   AbletonOSC really does listen on 11000 out of the box.
3. If a user needs mute/solo/send control or scene firing, that needs new
   `ableton_manager` operations built against the addresses in the table
   above — don't invent a workaround address.

## Primary sources

- `github.com/ideoforms/AbletonOSC` — AbletonOSC's own README (Network
  Configuration, Song/Track/Clip API tables), fetched and cross-checked
  directly, including a literal text search confirming `/live/play`,
  `/live/stop`, and `/live/tempo` do not appear anywhere in it
- `src/oscmcp/app_detect.py` — this repo's own verified install/detection
  notes for Ableton Live (`key="ableton"`), confirming the "no native OSC,
  AbletonOSC-only" dependency and the correct `default_osc_port=11000`
- `docs/ONBOARDING.md` (this repo) — cost/setup/pitfalls table, confirms
  AbletonOSC's dependency is "undiscoverable from inside osc-mcp"
