# SuperCollider Expert

## What is SuperCollider

A free, open-source platform for **real-time audio synthesis and
algorithmic composition** — it's a synthesizer, not a DAW or a sequencer
in the usual GUI sense. You write code (`sclang`, its own language) that
defines synths, effects, and generative/algorithmic music systems, which
an audio engine (`scsynth`) then renders live.

**Core features:** sample-accurate real-time synthesis, live coding
(editing the running sound in real time), a large built-in library of
signal-processing unit generators (UGens) for building custom
instruments/effects, and OSC as its *native* control protocol (`scsynth`
is driven entirely by OSC messages, unlike most apps in this fleet which
need a bridge). Widely used in experimental/electronic music, live
coding performance, and academic sound research.

You are an expert on controlling SuperCollider via `osc-mcp`'s
`supercollider_manager` tool. SuperCollider is **two separate processes**,
and confusing them is the single most common source of "it's not working"
here — this repo's own port table used to say `57120` for SuperCollider's
default OSC port; that number is real but belongs to the *wrong* process.
Everything below is checked against SuperCollider's own official
`Server-Command-Reference` doc (`doc.sccode.org`, mirrored at
`docs.supercollider.online`) and its OSC communication guide, not recalled
from memory.

## Two processes, two ports — read this before anything else

SuperCollider ships as a **language** and a **server**, and only one of
them plays audio or answers synthesis OSC commands:

| Process | Role | Default OSC port |
|---|---|---|
| **`scsynth`** (or `supernova`) | The audio server — allocates synths, buses, buffers, groups; the only thing that answers `/s_new`, `/n_set`, `/n_free`, etc. | **57110** |
| **`sclang`** | The language/client — interprets SuperCollider-language code, compiles `SynthDef`s, and *sends* OSC to `scsynth`. Also runs its own tiny OSC receiver (via `OSCFunc`/`OSCdef`) for language-side scripting, unrelated to audio synthesis. | **57120** (`NetAddr.langPort`, and only if that port wasn't already taken at startup — falls back to another port silently otherwise) |

Quoting the real architecture doc: "sclang is a client for the scsynth
server. It connects to scsynth... and sends OSC message[s] to scsynth,"
while "the server scsynth... can instantiate, connect and control new audio
processing blocks in response to specific OSC messages it receives."

**`supercollider_manager`'s default `port=57110` is correct** — it targets
`scsynth`, which is what you want for `/s_new`/`/n_set`/`/n_free`. If you
ever see `57120` proposed as the target for audio-synthesis OSC commands,
that's `sclang`'s language port, not the server — sending synthesis
commands there does nothing (57120 is not listening for `/s_new` at all).

**The IDE (`scide`) is neither of these.** `scide.exe` is just a text
editor/front-end for `sclang`; running it alone starts nothing that
answers OSC. This repo's own `app_detect.py` already documents this
correctly: `"scsynth.exe (the audio server) is what actually answers OSC -
running scide.exe alone isn't enough."`

## Setup dependency chain

1. `scsynth` must actually be **booted**, not just installed. In practice
   this means either:
   - Running `sclang`, then evaluating `s.boot` (`s` = the default
     `Server` object) — this launches `scsynth` as a subprocess already
     wired to listen on `s.addr`'s port (57110 by default), or
   - Launching `scsynth.exe`/`scsynth` directly from a command line.
2. A `SynthDef` with the name you want to trigger must already be **loaded
   into the running `scsynth`** before `/s_new` will do anything audible.
   `supercollider_manager` has no operation that loads one (no `/d_recv` or
   `/d_load`) — the only name guaranteed to exist without any extra setup
   is the server's own built-in `"default"` SynthDef (auto-loaded at boot
   unless disabled). Any other `def_name` needs to have been compiled and
   sent to the server by `sclang` (or already present in the server's
   synthdefs directory) through some other channel first.
3. No firewall exception is generally needed for `127.0.0.1`, but LAN/
   Tailscale control needs port 57110 open on the machine running
   `scsynth`.

## The real protocol — verified argument order

Source: `doc.sccode.org/Reference/Server-Command-Reference.html`
(mirrored at `docs.supercollider.online`), the official Server Command
Reference.

| Address | Arguments (in order) | Notes |
|---|---|---|
| `/s_new` | `synthDefName (string), nodeID (int), addAction (int), addTargetID (int), [controlName/index, value]...` | `addAction`: 0=addToHead, 1=addToTail, 2=addBefore, 3=addAfter, 4=addReplace (target node freed). NodeID `-1` asks the server to auto-assign an ID you won't know. |
| `/n_set` | `nodeID (int), [controlName/index, value]...` | Sets one or more named/indexed controls on an existing node |
| `/n_free` | `nodeID (int) [, nodeID...]` | Frees one or more nodes |
| `/n_run` | `[nodeID, runFlag]...` | Not implemented by `supercollider_manager` |
| `/g_new` | `[groupID, addAction, addTargetID]...` | Not implemented by `supercollider_manager` — group 0 is the always-present root group |
| `/notify` | `receiveFlag (0/1), clientID (optional)` | Registers the sender's return address for server notifications/replies. Not implemented by `supercollider_manager` — see Known gaps. |
| `/status` | none | Requests server status; not implemented |
| `/d_recv` | `buffer (bytes), completionMsg (optional bytes)` | Loads a compiled SynthDef into the server; not implemented — see setup chain above |

## `supercollider_manager` — what osc-mcp actually implements

```python
supercollider_manager(operation, host="127.0.0.1", port=57110,
                       def_name=None, node_id=None, add_action=None,
                       target=None, control_name=None, value=None)
```

| Operation | Sends | Verdict |
|---|---|---|
| `create_synth` | `/s_new, (def_name, node_id, add_action or 0, target or 0)` | **Correct** — matches the real argument order and defaults exactly (`add_action=0` is `addToHead`, `target=0` is the root group) |
| `free_node` | `/n_free, (node_id)` | **Correct** |
| `set_control` | `/n_set, (node_id, control_name, value)` | **Correct** — real `/n_set` accepts a control name (string) or index (int) interchangeably, matches |

Unlike the VRChat and VCV Rack integrations, everything this tool actually
implements matches the real protocol exactly — the gaps here are entirely
about missing operations, not wrong ones.

## Known gaps

1. **No `/notify` call anywhere.** `supercollider_manager` never registers
   a return address with the server. Practically: you can fire `/s_new`,
   `/n_set`, `/n_free` all day with zero feedback channel back to
   `osc-mcp` — no confirmation a synth actually started, and (not verified
   from docs fetched this session — needs live testing) it's unclear
   whether `/notify` registration also gates delivery of `/fail` error
   replies for malformed commands, versus only gating node-lifecycle
   notifications (`/n_go`/`/n_end`/`/n_off`/`/n_on`). Either way, this tool
   currently has no way to detect a silently-failed `/s_new` (e.g. an
   unloaded SynthDef name) beyond checking for audible/visible effect.
2. **No SynthDef loading path** (`/d_recv`/`/d_load`) — `create_synth`
   only works for `def_name="default"` (the server's built-in SynthDef) or
   a name already loaded into the running server through `sclang` or the
   server's synthdefs directory. There is no way, through this tool alone,
   to get a custom SynthDef onto the server.
3. **No `/status` or `/g_new`/`/g_free`** — no way to query server health
   or manage groups (beyond the always-present root group `0`, which
   `create_synth`'s `target=0` default already targets correctly).
4. **Port confusion risk**: don't let a user's SuperCollider language code
   (which talks about `NetAddr.langPort`, 57120) bleed into the port you
   configure here — that's `sclang`'s own port, unrelated to `scsynth`'s
   57110.

## Best Practices

1. **Confirm `scsynth` is actually running**, not just that SuperCollider
   (the IDE) is open. `app_detect.py`'s `process_names` list
   (`scsynth.exe`, `scide.exe`, `sclang.exe`) can tell you which processes
   exist, but only `scsynth.exe` running means anything will answer OSC.
2. **Use `"default"` as `def_name`** for a first connectivity test — it's
   the one SynthDef guaranteed to exist without any extra setup.
3. **Never target 57120** for `supercollider_manager` calls — that's the
   language port, not the server.
4. **No feedback means no feedback** — without `/notify`, a "successful"
   `create_synth` call only means the UDP packet was sent, not that
   `scsynth` did anything with it. Cross-check with audible output or the
   SuperCollider IDE's own node tree view when troubleshooting.

## Primary sources

- `https://doc.sccode.org/Reference/Server-Command-Reference.html` (mirror:
  `https://docs.supercollider.online/Reference/Server-Command-Reference.html`) —
  exact argument order for `/s_new`, `/n_set`, `/n_free`, `/n_run`,
  `/g_new`, `/notify`, `/status`, `/d_recv`; add-action integer meanings
- `https://doc.sccode.org/Guides/ClientVsServer.html` — sclang vs scsynth
  role split
- SuperCollider `NetAddr.langPort` documentation (via
  `doc.sccode.org`/`docs.supercollider.online` OSC guide search results) —
  confirms 57120 as the language port, distinct from the server
- `src/oscmcp/app_detect.py` (this repo) — corrected `default_osc_port=57110`
  and the "scsynth.exe... running scide.exe alone isn't enough" note
