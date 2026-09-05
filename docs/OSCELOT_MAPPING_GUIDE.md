# OSCelot Detailed Mapping Guide

**Corrected 2026-09-05 against the real, primary-source manual**
(`github.com/The-Modular-Mind/oscelot/blob/main/docs/Oscelot.md`) — the
previous version of this file had a "Direct `/param [ModuleID, ParamID,
Value]`" mode and a "right-click a dot to choose Slider/Button/Encoder"
workflow that **do not exist in the real plugin**. Both were fabricated;
neither matches OSCelot's actual, documented OSC protocol. See git history
if you need the old (wrong) version for reference.

## Enable the Send/Receive toggles first (they default OFF)

**Live-verified 2026-09-05**: a freshly-placed OSCelot module has both its
Send and Receive toggle buttons OFF (the panel's status dots render orange).
In this state `oscReceiver.start(port)` is never called, so OSCelot has no
UDP socket bound at all — every message sent to it is silently dropped, no
error, nothing in Rack's log. Click the small button under each of the
"Send"/"Receive" dots once (they're tiny — the round dot itself is the
button's light, not a separate control) until the dot turns green before
sending anything. This one step isn't mentioned anywhere in OSCelot's own
manual and is easy to miss entirely.

**Also live-verified**: the very first OSC message to a freshly-clicked
mapping slot only *creates and types* the slot (locks it to `/fader`,
`/encoder`, or `/button` and records the `Id`) — it does **not** move the
parameter yet. Send the identical message (`same address, same Id`) a
**second time** to actually apply the value. This matches OSCelot's own
source (`processOscMessage` in `Oscelot.cpp`): the create/learn branch never
sets the internal `oscReceived` flag that the value-apply step in `process()`
checks for, so the learn message and the first real value-apply message are
never the same message.

## The real protocol: three fixed message types, slot-addressed

OSCelot has **numbered mapping slots** (not one per module/param — one per
control you've manually mapped). Each slot is bound to exactly one VCV Rack
parameter, done once through OSCelot's own UI (see "Mapping parameters"
below) — **there is no way to address an arbitrary module/param pair
directly by ID over OSC**. You can only drive a slot that a human already
mapped.

Every message **must** end with one of these three addresses and carry
exactly two arguments:

| Type | Address suffix | Arguments | Example |
|---|---|---|---|
| Fader | `/fader` | `(Id: int, Value: float 0.0-1.0)` | `/fader, (1, 0.5573)` |
| Encoder | `/encoder` | `(Id: int, Delta: ±1.0 multiples)` | `/encoder, (1, -1.0)` |
| Button | `/button` | `(Id: int, Value: 0.0 or 1.0)` | `/button, (1, 1.0)` |

`Id` is the mapping slot's number, assigned when you mapped it in OSCelot's
UI — it has no fixed relationship to VCV's own internal module ID or
parameter ID. There is no `/param` address, no direct ModuleID/ParamID
addressing, and no way to skip the manual-mapping step.

Encoders are always in `DIRECT` mode. Faders/buttons default to `DIRECT`
too, but can be switched to `Pickup (snap)`, `Pickup (jump)`, `Toggle`, or
`Toggle + Value` in OSCelot's own controller-mode setting per slot.

## OSC feedback

If OSCelot's Sender is running, every parameter change (from OSC or from
turning the knob by hand in Rack) generates two messages back out:

```
/fader, (1, 0.3499999940395355)
/fader/info, (1, 'MixMaster', '-01-: level', '-21.335', ' dB')
```

The first repeats the slot Id + normalized value (0.0-1.0). The second,
suffixed `/info`, carries the module name, the parameter's label, its
current display value, and its unit — useful for confirming what a slot
is actually bound to without opening Rack.

## Mapping parameters (the only way to bind a slot)

You must do this once per parameter, in OSCelot's own UI, before any OSC
message can reach it:

1. **Map an entire module** (fast path): click OSCelot's module-map button
   (cursor becomes a crosshair), then click any module's panel in your
   patch. Every mappable parameter on that module gets bound to slots at
   once. `Ctrl/Cmd+Shift+D` clears existing mappings first;
   `Shift+D` keeps them and re-maps onto the new module.
2. **Map one parameter at a time**: click an empty mapping slot in
   OSCelot, then click the target knob/slider/button in your patch, then
   send a real `/fader`, `/encoder`, or `/button` message from your
   controller (or from `send_osc` while testing) — **the address you send
   is what determines the slot's type**, not a right-click menu.
3. **MeowMory**: once you've mapped a module type, you can save that
   mapping ("Store mapping") and re-apply it to any other instance of the
   same module type later (`Apply`, or hotkey `Shift+V`), without
   re-mapping by hand every time.

## Testing a mapping with osc-mcp

```python
# Slot 1, fader value 0.5573 (Id must be a slot you've already mapped in OSCelot's UI)
await send_osc("127.0.0.1", 7000, "/fader", [1, 0.5573])

# Slot 0, button press
await send_osc("127.0.0.1", 7000, "/button", [0, 1.0])

# Slot 2, encoder nudge
await send_osc("127.0.0.1", 7000, "/encoder", [2, 1.0])
```

Port `7000` above matches this repo's `app_detect.py` default note — set
OSCelot's own "Receive port" in its UI to whatever you actually use, there
is no fixed default.

## Common issues

- **Nothing happens when you send a message**: the slot must already be
  mapped to a parameter through OSCelot's UI first (see above) — OSC alone
  cannot create a new mapping to an arbitrary module/param.
- **Wrong Id**: `Id` is the mapping-slot number OSCelot assigned, not a
  VCV module ID. Check OSCelot's own list to see which Id belongs to which
  parameter.
- **Encoder does nothing on `/fader`/`/button` addresses**: each slot only
  responds to the one address type it was mapped with.
