# VRChat Expert

## What is VRChat

A free social VR platform where people interact as customizable 3D
avatars in user-created virtual worlds — usable with a VR headset or on a
flat monitor/keyboard.

**Core features:** fully custom, user-uploaded avatars (Unity-based, with
creator-defined animator parameters), user-built worlds, real-time
voice/text chat, face and full-body tracking support, and — the reason
it's in this fleet at all — a built-in OSC layer for driving avatar
parameters and inputs from outside the game.

You are an expert on controlling VRChat via `osc-mcp`'s `vrchat_manager` tool
and the two standalone tools `set_vrchat_expression` and
`trigger_vrchat_haptic_lfo`. VRChat has **real, official, first-party OSC
support** (unlike VCV Rack) — but this repo has two different code paths
talking to it, and they disagree with each other and with VRChat's own docs
on which port to use. Everything below was checked against VRChat's own
`docs.vrchat.com` pages and the `vrchat-community/osc` GitHub repo, not
recalled from memory.

## The chain: enabling OSC, and the two ports

1. VRChat must be running with an avatar loaded.
2. OSC is **off by default** and must be enabled in-game: Action Menu →
   **Options → OSC → Enabled** (confirmed: `docs.vrchat.com/docs/osc-overview`).
3. VRChat uses **two different ports for the two directions**, and this is
   the single most important fact in this file:
   - **Port 9000 — VRChat receives.** Anything that wants to *control*
     VRChat (set an avatar parameter, send a chatbox message, drive an
     input) must send to **9000**.
   - **Port 9001 — VRChat sends.** Anything that wants to *read* avatar
     parameter feedback, avatar-change events, etc. from VRChat must listen
     on **9001**.
   - Quoting the docs directly: "we default to receiving on port 9000 and
     sending on port 9001." Both are changeable at launch via
     `--osc=inPort:senderIP:outPort` (default equivalent:
     `--osc=9000:127.0.0.1:9001`).
4. Face tracking parameters (the `FT/v2/*` namespace used by
   `set_vrchat_expression`) additionally require the loaded avatar to
   actually expose Animator parameters literally named `FT/v2/<ShapeName>`
   — this is VRCFaceTracking's own naming convention, not something every
   avatar has. If the avatar wasn't built with VRCFT's template parameters
   (or a custom prefix was configured), the message lands on an address the
   avatar's Animator has no matching parameter for and does nothing.

## The real protocol

### Avatar parameters — one scalar value per address

`/avatar/parameters/<ParameterName>`, one Int/Bool/Float argument. Quoting
`vrchat-community/osc`'s own `Avatar-Parameters.md`: "incoming values at the
address `/avatar/parameters/name` will set the value of a matching
parameter's name" — the doc describes **exactly one value per message**,
never a compound argument list.

### Chatbox

| Address | Args | Meaning |
|---|---|---|
| `/chatbox/input` | `(string, bool, bool)` | text, send-immediately (bypasses keyboard if true), play-notification-sound |
| `/chatbox/typing` | `(bool)` | show/hide the "..." typing indicator — **no text argument at all** |

Source: `docs.vrchat.com/docs/osc-avatar-parameters` region covering chatbox,
cross-checked via search of the same official doc set.

### Input controller emulation

`/input/<Name>`, one argument. Confirmed real names from
`docs.vrchat.com/docs/osc-as-input-controller`:

- **Axes (float, -1..1):** `Vertical`, `Horizontal`, `LookHorizontal`,
  `UseAxisRight`, `GrabAxisRight`, `MoveHoldFB`, `SpinHoldCwCcw`,
  `SpinHoldUD`, `SpinHoldLR`
- **Buttons (int, 0/1):** `MoveForward`, `MoveBackward`, `MoveLeft`,
  `MoveRight`, `LookLeft`, `LookRight`, `Jump`, `Run`, `PanicButton`,
  `ComfortLeft`, `ComfortRight`, `DropLeft`/`DropRight`,
  `UseLeft`/`UseRight`, `GrabLeft`/`GrabRight`,
  `QuickMenuToggleLeft`/`QuickMenuToggleRight`, `Voice`

**There is no `LookUp` or `LookDown`.** VRChat's real input axis set has
`LookHorizontal` only — no vertical look input exists in the protocol.

### OSC Trackers — numbered slots, not named body parts

`docs.vrchat.com/docs/osc-trackers` describes a **numbered-slot** scheme,
not a named one:

```
/tracking/trackers/1/position   /tracking/trackers/1/rotation
...
/tracking/trackers/8/position   /tracking/trackers/8/rotation
/tracking/trackers/head/position   /tracking/trackers/head/rotation   (optional reference frame)
```

Each takes 3 floats (X,Y,Z world-space position, or euler-angle rotation;
1.0 = 1 meter). Up to 8 numbered trackers map informally to
hip/chest/2×feet/2×knees/2×elbows, but **that mapping is not part of the
address** — slot 3 isn't "LeftFoot," it's whatever the user's tracker-order
configuration says slot 3 is. **There is no OSC address to enable or
disable a tracker at all** — that's done in VRChat's own Tracking & IK menu
("Auto-center OSC Trackers") or the avatar's OSC config JSON, never via a
live OSC message.

### Haptics — no universal built-in address

Searched specifically for this: VRChat has **no standardized/built-in**
`/avatar/parameters/LeftHaptic` or `RightHaptic` parameter. Every real
haptics-over-OSC project found (Touch Feedback, VRCHaptics, OscGoesBrrr,
VuruVuruOSC) works by watching a **custom, avatar-specific** float
parameter the avatar creator chose to expose, then driving real controller
rumble from *outside* VRChat via SteamVR/OpenVR APIs — VRChat itself never
vibrates a controller from an incoming OSC message. Combined with the
one-value-per-address rule above, a message like
`/avatar/parameters/LeftHaptic, (duration, amplitude, frequency)` is
sending three floats to an address that (a) most avatars don't expose at
all, and (b) even where a similarly-named parameter exists, VRChat's
parameter contract only reads a single scalar per address — so any extra
arguments are almost certainly ignored or the whole message is malformed
depending on the receiving Animator's declared type.

### Unified Expressions naming (VRCFaceTracking)

`docs.vrcft.io`'s own parameter docs confirm the `FT/v2/<ShapeName>` naming
convention is real (VRCFaceTracking sends tracking data to VRChat avatars
using it), and confirmed real shape names include `JawOpen`,
`EyeLidLeft`/`EyeLidRight`. **`Smile` is not a real Unified Expressions or
Simple Expressions name** — the closest real names are
`MouthSmileLeft`/`MouthSmileRight` (Simple Expressions) or corner-pull
shapes in full Unified Expressions; there is no bare `Smile`.

## `vrchat_manager` — what osc-mcp actually implements

```python
vrchat_manager(operation, host="127.0.0.1", port=9000, param_name=None,
                value=None, message=None, device=None, duration=None,
                amplitude=None, frequency=None, input_name=None,
                tracking_type=None, enabled=True, notify=False)
```

Default port **9000 is correct** — this tool only ever sends *to* VRChat,
matching VRChat's real receive port.

| Operation | Sends | Verdict |
|---|---|---|
| `set_parameter` | `/avatar/parameters/{param_name}, (value)` | Correct — matches the real one-value-per-address contract |
| `send_chat` | `/chatbox/input, (message, True, notify)` | Correct arg order and types |
| `chatbox_typing` | `/chatbox/typing, (enabled)` | **Fixed** — used to send the message string where a bool belongs; now sends the `enabled` bool, no message text required |
| `input` | `/input/{input_name}, (float(value))` | Correct address shape; docstring's allowed `input_name` list had `LookUp`/`LookDown` (don't exist in VRChat's real input set) - **removed** |
| `tracking_control` | returns `UNSUPPORTED_OPERATION` | **Fixed** — used to fabricate `/tracking/{tracking_type}/enabled`; real trackers are numbered slots 1-8+head with only `/position` and `/rotation`, no named-body-part or enable/disable addressing exists at all, so this now returns a clear error instead |
| `afk_toggle` | `/avatar/parameters/AFK, (1 or 0)` | Correct — `AFK` is a real built-in VRChat animator parameter, confirmed reachable via the standard avatar-parameters address |
| `trigger_haptic` | returns `UNSUPPORTED_OPERATION` | **Fixed** — used to send `/avatar/parameters/{Left,Right}Haptic` with a 3-float payload (see Haptics section above for why neither the address nor the payload shape is real); now returns a clear error instead |

## `set_vrchat_expression` / `trigger_vrchat_haptic_lfo` — a different code path

These two tools (in `src/oscmcp/server.py`) don't call `send_osc` directly —
they construct a `VRChatOSC` instance from `src/oscmcp/apps/vrchat.py` and
use its `.set_parameter()` / `.trigger_haptic()` methods. That class's port
constants **were backwards relative to VRChat's real convention** (fixed):

```python
# Before the fix:
DEFAULT_INPUT_PORT = 9000   # wrongly fed the OSCServer (listener)
DEFAULT_OUTPUT_PORT = 9001  # wrongly fed the OSCClient (sender)
# After:
DEFAULT_INPUT_PORT = 9001   # we listen here for VRChat's outgoing messages
DEFAULT_OUTPUT_PORT = 9000  # we send here - VRChat's own real listen port
```

Before the fix, the `OSCClient` (what `.send()` actually uses to talk to
VRChat) was bound to port 9001 by default — but VRChat's real receive port
is 9000, confirmed above from `docs.vrchat.com/docs/osc-overview`. Every
call through `set_vrchat_expression` and `trigger_vrchat_haptic_lfo` was a
silent UDP no-op unless the user happened to be running VRChat with
non-default `--osc` arguments. `vrchat_manager` (the portmanteau tool,
above) hardcodes `port=9000` directly and never went through `VRChatOSC`,
so it was never affected by this one.

## Known gaps

Fixed during this pass (kept here for history/context, not because they're
still wrong):
1. ~~Port mismatch~~ — `VRChatOSC`'s port constants now match VRChat's real
   convention (see above).
2. ~~`chatbox_typing` sent the wrong argument type~~ — now sends the
   `enabled` bool; `message` is no longer required or used for this op.
3. ~~`tracking_control`'s address was fabricated~~ — now returns
   `UNSUPPORTED_OPERATION` with an explanation, rather than sending a
   made-up address.
4. ~~Haptics addresses had no real basis~~ — `trigger_haptic` (the
   `vrchat_manager` operation) now returns `UNSUPPORTED_OPERATION`.
   `VRChatOSC.trigger_haptic` (used only by the standalone
   `trigger_vrchat_haptic_lfo` tool) still sends the same fabricated
   addresses — deep-reworking that async LFO pattern runner's error
   propagation was out of scope for this pass, so its docstring now
   states plainly that it's speculative/likely non-functional instead.
5. ~~`LookUp`/`LookDown` listed as valid~~ — removed from `vrchat_manager`'s
   docstring.
6. ~~`Smile` used as an example expression~~ — `set_vrchat_expression`'s
   docstring/examples now use `JawOpen` (a confirmed real name) instead.

Still open:
7. **`FT/v2/<name>` isn't guaranteed to exist on an arbitrary avatar** —
   it's VRCFaceTracking's own convention, not a VRChat platform guarantee.
8. **Not verified — needs live testing**: whether VRChat's OSC layer
   silently ignores extra arguments beyond the first on an
   `/avatar/parameters/*` message, or rejects the whole message. No primary
   source found either way.
9. **`trigger_vrchat_haptic_lfo`/`VRChatOSC.trigger_haptic` remain
   functionally speculative** — see item 4. A real fix would need a way to
   discover the target avatar's actual haptic-capable parameter names,
   which isn't something this tool can know in advance.

## Best Practices

1. **Never conflate the two ports.** Sending to VRChat: 9000. Receiving
   from VRChat: 9001. If a tool "succeeds" but nothing happens in-game,
   check which port it actually used first.
2. **OSC must be manually enabled in-game every session** — Action Menu →
   Options → OSC → Enabled. It is not on by default and does not persist
   as an in-game setting the way you might expect (verify current-session
   state before assuming a prior enable still holds).
3. **Don't assume a parameter exists on the loaded avatar.** `/avatar/parameters/*`
   silently no-ops if the Animator has no matching parameter — this is true
   for `AFK`, `FT/v2/*` face tracking names, and any custom haptics
   parameter alike.
4. **Trackers are numbered, not named** — don't invent `/tracking/{BodyPart}/...`
   addresses; the real scheme is `/tracking/trackers/{1-8|head}/{position|rotation}`.
5. If a user wants real controller haptics from VRChat, point them at a
   community bridge app (VRCHaptics, OscGoesBrrr, Touch Feedback) that
   reads an avatar-specific parameter and drives the vibration itself —
   `osc-mcp` sending to `LeftHaptic`/`RightHaptic` directly has no
   documented effect on a stock avatar.

## Primary sources

- `https://docs.vrchat.com/docs/osc-overview` — ports (9000 receive / 9001
  send), enabling OSC, `--osc=` launch argument
- `https://docs.vrchat.com/docs/osc-avatar-parameters` — avatar parameter
  address format, chatbox address/argument details
- `https://docs.vrchat.com/docs/osc-as-input-controller` — full real
  `/input/*` address list
- `https://docs.vrchat.com/docs/osc-trackers` — numbered-slot tracker
  addressing, position/rotation-only, no enable/disable address
- `https://github.com/vrchat-community/osc/blob/main/docs/Avatar-Parameters.md` —
  one-value-per-address confirmation
- `https://docs.vrcft.io/docs/tutorial-avatars/tutorial-avatars-extras/parameters` /
  `.../unified-blendshapes` — `FT/v2/*` naming convention, real shape names
  (`JawOpen`, `EyeLidLeft`/`EyeLidRight`)
- `https://github.com/benaclejames/VRCFaceTracking/blob/master/VRCFaceTracking.Core/Params/Expressions/UnifiedSimpleExpressions.cs` —
  confirms `Smile` is not a real parameter name
- `src/oscmcp/apps/vrchat.py`, `src/oscmcp/server.py` (this repo) — the
  `VRChatOSC` class and the two standalone tools' actual port defaults and
  send calls
- `src/oscmcp/app_detect.py` (this repo) — install path, `default_osc_port=9000`,
  "OSC must be enabled in-game" note
