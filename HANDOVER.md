# Handover — 2026-09-05/06 session (Claude → opencode/Antigravity)

Written because Claude ran out of weekly credits (usage-based billing
resets 2026-09-06 evening). Everything below is committed and pushed to
`master` unless noted otherwise. No uncommitted local changes at handoff.

## What happened this session, in order

1. **VCV Rack patch generation** (`src/oscmcp/vcv_patch_builder.py`,
   `vcv_presets.py`) — generates real, loadable `.vcv` files (modules +
   cables) as JSON, no GUI automation. Port indices extracted from real
   module C++ source via `scripts/vcv_port_schema_extract.py`, covering 18
   modules (Fundamental, Bogaudio, VCV Core). 7 presets, from a 3-module FM
   bell to a 19-module fully self-playing `grand_generative_patch`. All
   live-verified in a real running Rack.
2. **`patches/` depot** — all 7 presets committed as real `.vcv` files, so
   `git clone` alone gives a working preset set with no Python needed.
   `scripts/generate_vcv_patches.py` is the only thing that should write
   them; a test (`tests/test_vcv_patch_builder.py`) guards against drift.
3. **A real extractor bug found and fixed**: a `// added in X.Y.Z`
   full-line comment before an enum member silently ate the real member
   that followed. Re-audited all 18 already-shipped schemas against the
   fix per the fleet bug-discovery protocol — found it had already
   corrupted two committed entries (Fundamental LFO's inputs, Scope's
   outputs). Both fixed.
4. **Community Patches page** (`src/oscmcp/patchstorage_client.py`,
   `api/v1/endpoints/patchstorage.py`, `web_sota/src/pages/community-patches.tsx`)
   — browses the real, live Patchstorage.com Beta REST API across all 92
   platforms it hosts (VCV Rack, SuperCollider, Max for Live, TouchOSC,
   Bitwig, and 88 others). No auth needed, no local sync/cache (Patchstorage
   does server-side search/filter/sort/pagination itself).
5. **12 per-app skills** (`skills/{app}-expert/SKILL.md`) for every
   controlled application: Ableton, VCV Rack, TouchDesigner, VRChat,
   SuperCollider, Max/MSP, Resolume, QLab, Pure Data, OBS, REAPER, plus the
   existing generic `osc-mcp-expert`. Each researched against real primary
   sources (official docs, GitHub repos of any bridge/plugin), not written
   from memory, and each opens with a plain "what is this program" intro +
   compact feature list before any OSC specifics.
6. **The skill research found real bugs**, all fixed:
   - `ableton_manager`: `play`/`stop`/`set_tempo` sent addresses AbletonOSC
     doesn't recognize → fixed to `/live/song/start_playing` /
     `/live/song/stop_playing` / `/live/song/set/tempo`
   - `resolume_manager`: `set_bpm` sent `/transport/tempo` (not real) →
     `/composition/tempocontroller/tempo`
   - `vrchat_manager`: `chatbox_typing` sent text where a bool was expected
     (fixed); `tracking_control`/`trigger_haptic` sent addresses with no
     real basis (now return `UNSUPPORTED_OPERATION`)
   - `apps/vrchat.py`'s `VRChatOSC` class had send/receive ports swapped
     (affected the standalone `set_vrchat_expression`/
     `trigger_vrchat_haptic_lfo` tools)
   - `maxmsp_manager`/`puredata_manager`: port defaults disagreed with
     `app_detect.py`'s registry (now aligned); `toggle_dsp` in both had no
     real backing (now `UNSUPPORTED_OPERATION`); `app_detect.py`/
     `ONBOARDING.md` mislabeled `oscformat`/`oscparse` as Max objects
     (they're Pure Data's)
   - `obs_manager`: docstring never mentioned its hard dependency on
     `scripts/obs_websocket_bridge.py`; documented volume range was wrong
     (0.0-1.0 vs the bridge's real 0.0-2.0)
   - `audio_workflow_manager`/`music_loader_manager` REAPER calls:
     `/tempo` (normalized 0-1 per REAPER's own default OSC config, not raw
     BPM) → `/tempo/raw`; `/rewind` (hold-gesture, not a seek) used for
     "reset to start" → REAPER's real `/action 40042` ("Transport: Go to
     start of project")
   - Two **pre-existing, unrelated** bugs in `web_sota/src/pages/skills.tsx`
     found while verifying the new skills render: response-shape mismatch
     meant the Skills dashboard page always showed "No skills available,"
     and the detail fetch read `.text()` on a JSON response. Both fixed.
   - QLab and SuperCollider came back clean — nothing to fix there.

## Known gaps flagged but NOT fixed (deliberately out of scope)

- **`music_loader_manager`'s `load_bach_organ`/`load_midi_file`/
  `setup_organ_rig` operations send VCV Rack addresses** (`/param`,
  `/module/add`, `/connect`, `/transport/play`) that are unrelated to
  OSCelot's real slot-addressed protocol and are almost certainly
  fabricated the same way `vcv_manager` used to be, before an earlier
  session fixed it. Not touched this session — flagged in
  `skills/vcvrack-expert/` and `skills/reaper-expert/` for whoever picks
  this up next. This is probably the single highest-value remaining fix.
- **`reaper-mcp`'s own `/marker/add`** (separate sibling repo,
  `D:\Dev\repos\reaper-mcp`) doesn't correspond to any real action in
  REAPER's default OSC pattern config either — found while researching
  the REAPER skill, not fixed (different repo, wasn't asked).
- **Resolume's `set_bpm` value format is still unconfirmed** — fixed the
  address, but whether it wants raw BPM or a normalized 0.0-1.0 value
  over a 20-500 BPM range is only forum-sourced, not primary-sourced.
- **VRChat's `trigger_vrchat_haptic_lfo`/`VRChatOSC.trigger_haptic`
  remain functionally speculative** — no universal VRChat haptic address
  exists at all (confirmed), so this tool has no real fix available
  without per-avatar parameter discovery, which it has no way to do.

## Repo state at handoff

- Branch: `master`, all work pushed. Last commit: `7ed10ca`.
- All 75 backend tests pass (`uv run pytest tests/ -q`), lint clean
  (`ruff check`/`ruff format --check`), frontend typechecks clean
  (`npx tsc --noEmit` in `web_sota/`).
- A dev backend was running on `:10767` at end of session
  (`uv run uvicorn oscmcp.api.main:app --host 127.0.0.1 --port 10767`) —
  may or may not still be alive depending on what happened after handoff;
  check `netstat -ano | grep 10767` before assuming.
- `mcp-central-docs/projects/osc-mcp/{README,CHANGELOG,INSTALL}.md` were
  synced to match this repo's own docs earlier in the session (commit
  `fe11fa22` in that separate repo) — that repo has a lot of unrelated
  in-flight work from other sessions; don't blind `git add -A` there.

## Suggested next steps, roughly in priority order

1. Audit and fix `music_loader_manager`'s fabricated VCV Rack addresses
   (see gap above) — same treatment as everything else this session:
   read OSCelot's real protocol, fix or mark `UNSUPPORTED_OPERATION`.
2. If anyone has a real macOS box, live-verify the QLab skill's claims
   (never tested live this session — Windows can't run QLab at all).
3. Consider whether `reaper-mcp`'s `/marker/add` is worth fixing in that
   separate repo.
4. Nothing urgent is broken — this is a "keep going" list, not a
   "something's on fire" list.
