# VCV Rack Expert

## What is VCV Rack

A free, open-source **virtual modular synthesizer** — a software
recreation of Eurorack-style hardware modular synths. Instead of one
fixed instrument, you patch virtual cables between small, single-purpose
modules (oscillators, filters, envelopes, sequencers, effects) to build a
custom sound-generating and processing chain from scratch.

**Core features:** hundreds of free and paid third-party modules from many
independent "brands," real-time patch-cable routing, MIDI/CV interfacing,
polyphonic signal paths, runs standalone or as a VST/AU plugin inside a
DAW.

You are an expert on controlling VCV Rack via `osc-mcp`'s `vcv_manager`
tool. This is the single most error-prone integration in the fleet — VCV
Rack has **no native OSC support
at all**, and the bridge module's own community documentation is thin
enough that most of what follows was verified against its real C++ source
and a live running instance, not just its docs.

## The chain: VCV Rack → OSCelot → osc-mcp

Every `vcv_manager` operation assumes the community **OSCelot** module
(by TheModularMind, installed from the VCV Library — needs a free VCV
account) is patched into the user's rack and configured. There is no
other path in. Before anything else works:

1. OSCelot must be installed (VCV Library → search "OSCelot" → Add, then
   Rack's own Library menu → "Update all").
2. It must be patched into the rack (drag it in from the module browser).
3. **Its Send and Receive toggles default OFF.** A freshly-placed OSCelot
   module shows both status dots orange — in this state `oscReceiver`
   never binds a UDP socket, so every OSC message sent to it is silently
   dropped with no error anywhere, including Rack's own log. Click the
   tiny button under each dot until both turn green. This step appears
   nowhere in OSCelot's own manual and is the single most common reason
   "nothing happens."
4. Each parameter you want to control must be **manually mapped to a slot**
   inside OSCelot's own UI first (see "Mapping parameters" below) — there
   is no way to address an arbitrary VCV module/parameter pair over OSC
   without this step, ever.

## The real protocol: three fixed addresses, slot-addressed

Verified against OSCelot's real source
(`github.com/The-Modular-Mind/oscelot`, `Oscelot.cpp`'s `processOscMessage`)
and its docs (`docs/Oscelot.md`) — an earlier version of this project's own
docs described a fabricated `/param [ModuleID, ParamID, Value]` addressing
mode that **does not exist**. Don't reintroduce it.

| Type | Address | Arguments | Example |
|---|---|---|---|
| Fader | `/fader` | `(Id: int, Value: float 0.0–1.0)` | `/fader, (1, 0.5573)` |
| Encoder | `/encoder` | `(Id: int, Delta: ±1.0 multiples)` | `/encoder, (1, -1.0)` |
| Button | `/button` | `(Id: int, Value: 0.0 or 1.0)` | `/button, (1, 1.0)` |

`Id` is the mapping slot number OSCelot assigned when the parameter was
mapped through its own UI — it has **no relationship to VCV's internal
module ID or parameter ID**. There is no default port; OSCelot's receive
port is entirely user-configured inside its own UI (see `app_detect.py`:
`default_osc_port=None` for VCV Rack, deliberately — a previous version of
this codebase guessed `7000`, then `14000`; both were fabricated).

**The first message to a freshly-mapped slot only creates/types it** —
it locks the slot to fader/encoder/button and records the Id, but does
**not** move the parameter yet. Send the identical message a second time
to actually apply the value. This is a real quirk of OSCelot's own learn
logic (the create branch never sets the `oscReceived` flag the value-apply
step checks for), not a bug in `osc-mcp`.

## OSC feedback (if you also need to read state back)

If OSCelot's Sender is enabled, every parameter change (from OSC or from
turning the knob by hand in Rack) emits two messages:

```
/fader, (1, 0.3499999940395355)
/fader/info, (1, 'MixMaster', '-01-: level', '-21.335', ' dB')
```

The first repeats slot Id + normalized 0.0–1.0 value. The `/info` variant
carries the module name, parameter label, current display value, and unit
— useful for confirming what a slot is actually bound to.

## `vcv_manager` — what osc-mcp actually implements

```python
vcv_manager(operation, host="127.0.0.1", port=10001, module_id=None, value=None, reaper_tempo=None)
```

`module_id` is a confusingly-named parameter kept for backward
compatibility — **it means the OSCelot mapping slot Id, never a VCV Rack
module ID.**

| Operation | Sends | Notes |
|---|---|---|
| `set_parameter` | `/fader, (module_id, value)` | `value` is 0.0–1.0 |
| `trigger` | `/button, (module_id, 1.0)` | Presses a mapped button slot |
| `sync_reaper_tempo` | `/fader, (module_id, tempo/120.0 clamped 0-1)` | Crude 120-BPM-as-1.0 normalization; no better convention is documented anywhere |

**Gap, not a bug**: OSCelot's real `/encoder` address has no corresponding
`vcv_manager` operation today — only fader and button slots are reachable.
If a user has an encoder-mode slot mapped, there is currently no way to
drive it through this tool.

Nine other operations you may be tempted to reach for —
`send_cv`, `set_light`, `play_midi`, `stop_midi`, `send_midi_cc`,
`start_transport`, `stop_transport`, `reset_transport`,
`set_transport_position` — have **no verified real OSC address** anywhere
in OSCelot's protocol and correctly return `UNSUPPORTED_OPERATION` rather
than guessing one. Don't invent addresses for these; if a user needs one,
it needs primary-source verification first (or direct empirical testing
against a running Rack instance, as everything above was).

## Mapping parameters (must happen once, in OSCelot's own UI)

1. **Map an entire module** (fast path) — click OSCelot's module-map
   button, then click the target module in the rack. Every exposed
   parameter on it gets a slot.
2. **Map a single parameter** — right-click the specific knob/button in
   VCV Rack itself, choose "OSCelot: Map", which creates one slot.

Either way, note the slot number(s) assigned — that's the `module_id`
value every `vcv_manager` call needs.

## Generating patches without any of this

If the goal is building a VCV Rack patch programmatically rather than
*controlling* a running one, that's a separate, unrelated feature —
`src/oscmcp/vcv_patch_builder.py` / `vcv_presets.py` generate real,
loadable `.vcv` files (modules + cables) directly as JSON, with port
indices extracted from each module's own C++ source rather than guessed.
See `patches/README.md` and the "VCV Rack & Community Patches" section of
the repo's own `README.md`. This path needs no OSCelot, no mapping, and no
live Rack connection at all — it produces a file you open with Rack's own
File > Open.

## Discovery pages (browsing, not control)

Two dashboard pages help a user find modules/patches, but neither talks
OSC and neither is part of `vcv_manager`:

- **VCV Module Library** (`/vcv-library`) — browses the official module
  marketplace (`library.vcvrack.com`), 4,468 modules, 345 brands.
- **Community Patches** (`/community-patches`) — browses Patchstorage.com's
  real Beta API across all 92 platforms it hosts, filterable to VCV Rack.

## Best Practices

1. **Always confirm Send/Receive are both green** before assuming a
   silent failure is `osc-mcp`'s fault — it's almost always this.
2. **Send twice on a fresh mapping** — the first message only types the
   slot; the second actually moves it.
3. **Never guess a port** — there is no default. Ask the user for the
   port OSCelot is configured to receive on, or check its own UI.
4. **Don't invent `/param` or module/param-ID addressing** — it does not
   exist in the real plugin, no matter how convenient it would be.
5. If a user wants a *new* patch built rather than an *existing* one
   controlled, that's the patch-builder path, not `vcv_manager` at all.

## Primary sources

- `github.com/The-Modular-Mind/oscelot` — OSCelot's real source and docs
  (`docs/Oscelot.md`, `src/Oscelot.cpp`)
- `docs/OSCELOT_MAPPING_GUIDE.md` (this repo) — the full setup walkthrough,
  corrected 2026-09-05 against the above and live-tested against a real
  running Rack instance
- `src/oscmcp/app_detect.py` — verified install paths, process names, and
  the deliberate `default_osc_port=None`
