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
| `/g_new` | `[groupID, addAction, addTargetID]...` | Implemented as `create_group` |
| `/g_freeAll` | `groupID (int) [, groupID...]` | Implemented as `free_group` — frees every node *inside* the group, the group itself remains (verified live: `num_groups` unchanged after calling this on a freshly-created empty group) |
| `/notify` | `receiveFlag (0/1), clientID (optional)` | Registers the sender's return address for server notifications/replies. Not implemented by `supercollider_manager` — see Known gaps. |
| `/status` | none | Requests server status - server replies to whatever address the request came from. Implemented as `status`, using a dedicated request/reply socket (`_query_scsynth_status`), not the shared fire-and-forget `send_osc` helper every other operation here uses. |
| `/status.reply` | `unused, num_ugens, num_synths, num_groups, num_synthdefs, avg_cpu_percent, peak_cpu_percent, nominal_sample_rate, actual_sample_rate` | The real reply to `/status` - live-verified against a running `scsynth.exe` 3.14.1 before shipping (see below) |
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
| `create_group` | `/g_new, (node_id, add_action or 0, target or 0)` | **Added** — `node_id` doubles as the new group's ID (nodes and groups share one ID space in scsynth) |
| `free_group` | `/g_freeAll, (node_id)` | **Added** — `node_id` is the group's ID here |
| `status` | `/status`, waits for `/status.reply` on the same socket | **Added** — the one genuinely bidirectional operation in this whole tool; every other operation here (and in every other app-manager in this fleet except QLab/obs-websocket) is fire-and-forget |

Unlike the VRChat and VCV Rack integrations, everything this tool actually
implements matches the real protocol exactly — the remaining gaps are
entirely about missing operations, not wrong ones.

**Live-verified** (real running `scsynth.exe` 3.14.1, `-u 57110`, before
shipping any of this): `status` returned real telemetry (`num_groups`
correctly at 1 with nothing running, CPU/sample-rate fields all genuine,
non-fabricated numbers, actual sample rate showing real clock drift from
nominal - 48020.65 Hz vs 48000 Hz nominal on the test machine);
`create_group`/`free_group` confirmed against a live `status` diff
(`num_groups` 1→2 on create, staying at 2 after `free_group` since that
only empties the group rather than deleting it, exactly as documented).

## Known gaps

1. **No `/notify` call anywhere.** `supercollider_manager` never registers
   a return address with the server for node-lifecycle notifications
   (`/n_go`/`/n_end`/`/n_off`/`/n_on`) or `/fail` error replies - `status`
   now provides real *server-level* telemetry, but there's still no way to
   confirm an individual `/s_new` actually started (e.g. because the named
   SynthDef isn't loaded) beyond checking `status`'s `num_synths` before
   and after, or audible/visible effect.
2. **No SynthDef loading path** (`/d_recv`/`/d_load`) — `create_synth`
   only works for `def_name="default"` (the server's built-in SynthDef) or
   a name already loaded into the running server through `sclang` or the
   server's synthdefs directory. There is no way, through this tool alone,
   to get a custom SynthDef onto the server.
3. **Port confusion risk**: don't let a user's SuperCollider language code
   (which talks about `NetAddr.langPort`, 57120) bleed into the port you
   configure here — that's `sclang`'s own port, unrelated to `scsynth`'s
   57110.
4. **`status` blocks the event loop's thread pool for up to 2s on
   timeout** (`asyncio.to_thread` wraps a blocking socket call) — fine for
   occasional polling from the webapp's Refresh button, not something to
   call in a tight loop.

## Best Practices

1. **Confirm `scsynth` is actually running**, not just that SuperCollider
   (the IDE) is open. `app_detect.py`'s `process_names` list
   (`scsynth.exe`, `scide.exe`, `sclang.exe`) can tell you which processes
   exist, but only `scsynth.exe` running means anything will answer OSC.
2. **Use `"default"` as `def_name`** for a first connectivity test — it's
   the one SynthDef guaranteed to exist without any extra setup.
3. **Never target 57120** for `supercollider_manager` calls — that's the
   language port, not the server.
4. **`create_synth`/`free_node`/`set_control`/`create_group`/`free_group`
   are still fire-and-forget** — a "successful" call only means the UDP
   packet was sent, not that `scsynth` did anything with it. Use the new
   `status` operation before/after to cross-check `num_synths`/
   `num_groups` changed as expected, or check the SuperCollider IDE's own
   node tree view.

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
