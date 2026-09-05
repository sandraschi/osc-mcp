# Max/MSP Expert

## What is Max/MSP

A visual, node-based ("patcher") programming environment by Cycling '74
for interactive music, audio, and multimedia — you build custom
instruments, effects, and interactive systems by wiring together objects
("boxes") rather than writing text code.

**Core features:** real-time audio processing (the "MSP" half) and
video/graphics processing (the "Jitter" half), MIDI/OSC/serial I/O,
widely used in experimental music, sound design, and interactive
installations, extensible via a large ecosystem of third-party objects
and packages (like the odot OSC package this skill references below).

You are an expert on controlling Cycling '74's Max/MSP via `osc-mcp`'s
`maxmsp_manager` tool. Max has **no fixed OSC namespace and no default OSC
port at all** — unlike Resolume or OSCelot, there is nothing "the real
protocol" can mean here beyond "whatever objects the user's own patch
contains." Anything that looks like a universal Max OSC address is a red
flag; verify it against Cycling '74's own reference docs or don't ship it.

## The chain: external sender → UDP → (decode) → patch objects

Max only receives OSC if the user's own patch is wired to do so. There are
two structurally different paths in, and `osc-mcp` assumes neither of them
automatically — it just fires OSC-formatted UDP packets and hopes a
matching patch exists on the other end.

**Path A — raw UDP objects (what `app_detect.py`'s notes field points at):**

1. `udpreceive` — Max's own built-in object. Confirmed via
   `docs.cycling74.com/reference/udpreceive/`: it "receives messages
   transmitted over a network using UDP" and can optionally pass buffers
   through as raw OSC packets instead of decoding them itself. It does
   **not** parse OSC semantics on its own, and the docs give **no default
   port** — the user must supply one as an argument or via a `port`
   message.
2. `udpsend` — the send-side counterpart, same page family
   (`docs.cycling74.com/reference/udpsend/`): takes `host` and `port`
   arguments, again with **no documented default port**.
3. Something to actually decode the OSC packet into an address + typed
   args. **This is where `app_detect.py`'s current note is wrong** (see
   Known gaps) — Max does not ship `oscformat`/`oscparse`; those are
   **Pure Data** objects (confirmed: both
   `docs.cycling74.com/reference/oscformat/` and `.../oscparse/` 404, and
   an independent search explicitly identifies them as Pd-only). The real
   Max-side decoder has historically been CNMAT's **odot** package
   (`o.pack`, `o.unpack`, `o.route` — the latter working like Max's
   built-in `route` but for slash-delimited OSC addresses with pattern
   matching), documented at `cnmat.org/OpenSoundControl/Max/` and covered
   in Cycling '74's own article "CNMAT ODOT: Tools for OSC and beyond."
   Historically the CNMAT/odot Max Package Manager listing has **not
   included a Windows build** (per multiple `cycling74.com/forums/osc-route-*`
   threads) — worth knowing since this fleet is Windows-first.

**Path B — Max's own built-in parameter OSC (a completely separate,
unrelated mechanism):** per `docs.cycling74.com/userguide/OSC/`, Max can
expose patch **parameters** over OSC automatically once enabled (Max
Preferences, or the patcher inspector's built-in UDP server), addressed as
`/param/<parameter-name>` and driven by the `param.osc` object
(`docs.cycling74.com/reference/param.osc/`). No `udpreceive` patching
needed for this path — but it only reaches things declared as Max
*parameters*, not an arbitrary named receiver, and `maxmsp_manager` does
not use this path at all.

`maxmsp_manager` matches **neither** path's real, documented addressing.
It invents a third convention: send to `/{receiver}` and assume the user's
patch has a `[udpreceive]` → (some OSC decoder) → `[r receiver]` chain
wired up to catch it. That's a workable convention if the user's patch
matches it, but it is **not** anything Cycling '74 or CNMAT ships or
documents — it only works because the user built their patch to match
this tool's assumption, not the other way around.

## `maxmsp_manager` — what osc-mcp actually implements

```python
maxmsp_manager(operation, host="127.0.0.1", port=7400, receiver=None, value=None)
```

| Operation | Sends | Notes |
|---|---|---|
| `send_bang` | `/{receiver}`, `["bang"]` | The literal string `"bang"` is sent as an OSC argument — OSC has no bang type. The receiving patch gets the *string* `"bang"`, not an actual Max bang message, unless it explicitly converts (e.g. `[select bang]` → real bang). Convention-only; not a Max/CNMAT standard. |
| `send_float` | `/{receiver}`, `[value]` | Same receiver-name convention; arbitrary float, no range checking. |
| `toggle_dsp` | returns `UNSUPPORTED_OPERATION` | **Fixed** — used to send `/dsp/toggle`, which has no primary-source backing anywhere (DSP on/off in Max is normally driven by a `dspstate~`/`adstatus`-style object inside the patch, not a predefined OSC path). Now returns a clear error instead of silently sending an address nothing listens on. |

## Known gaps

Fixed during this pass:
- ~~`app_detect.py`'s notes field mislabeled `[oscformat]`/`[oscparse]` as
  Max objects~~ — corrected there (and in `docs/ONBOARDING.md`) to note
  they're Pure Data objects, and to name CNMAT's odot
  (`o.pack`/`o.unpack`/`o.route`) as the real Max-side OSC codec instead.
- ~~Port default conflict~~ — `maxmsp_manager`'s default (was `4000`) now
  matches `app_detect.py`'s `default_osc_port=7400`. Neither is a real Max
  default (confirmed above - the user's patch decides), but they no longer
  disagree with each other inside the same codebase.
- ~~`toggle_dsp`'s `/dsp/toggle` address was unverified~~ — now returns
  `UNSUPPORTED_OPERATION` instead of sending it.

Still open:
- **The `/{receiver}` convention only works if the user's patch is built
  to match it.** There is no way to guarantee this, and no way for
  `osc-mcp` to detect whether a given receiver name exists in the target
  patch — a silent no-op (message sent, nothing happens) is
  indistinguishable from success at the network layer, same class of
  failure mode as OSCelot's Send/Receive-off case in `vcv_manager`.
- **CNMAT/odot's Windows package availability has a documented history of
  gaps** (per Cycling '74 forum threads on `osc-route`/CNMAT Windows
  builds) — worth surfacing to a user who hits "loaded fine on the
  CNMAT/odot download page's examples but the actual external won't load
  on Windows."

## Best practices

1. **Never assume a Max OSC namespace exists.** Every address this tool
   sends depends entirely on the user's own patch. Ask what receiver names
   (or `udpreceive` port) their patch actually uses before troubleshooting
   "nothing happens."
2. **`send_bang`'s `"bang"` string is not a real bang on arrival** — tell
   the user their patch needs to convert it if they want actual bang
   semantics, not just a string atom.
3. **`toggle_dsp` now correctly refuses to run** rather than silently
   sending a made-up address — if a user needs this, it requires a real
   `dspstate~`/`adstatus`-style object wired into their own patch first.
4. **If the user wants Max's built-in parameter-OSC path (Path B) instead
   of the receiver-name convention (what this tool actually does), say so
   explicitly** — they're unrelated mechanisms and `maxmsp_manager` cannot
   drive `param.osc`-style parameter addressing today.
5. **Port is always a guess.** Ask the user what port their `udpreceive`
   object is bound to; don't rely on the `7400` default just because it's
   consistent across this repo now.

## Primary sources

- `docs.cycling74.com/reference/udpreceive/` — real, built-in Max object;
  raw UDP receive, no default port
- `docs.cycling74.com/reference/udpsend/` — real, built-in Max object;
  raw UDP send, no default port
- `docs.cycling74.com/userguide/OSC/` — Max's built-in parameter-OSC path
  (`param.osc`, `/param/<name>` addressing) — unrelated to the
  `udpreceive`/`udpsend` patching path
- `docs.cycling74.com/reference/param.osc/` — parameter OSC object
  reference
- `cnmat.org/OpenSoundControl/Max/` and
  `cycling74.com/articles/cnmat-odot-tools-for-osc-and-beyond` — the real
  OSC codec objects for the raw-UDP path (`o.pack`/`o.unpack`/`o.route`)
- `cycling74.com/forums/osc-route-and-opensoundcontrol-for-max-7` and
  related forum threads — documented Windows package-availability gaps
  for the CNMAT/odot external
- `src/oscmcp/app_detect.py` (this repo, `key="maxmsp"`) — install path,
  `default_osc_port=7400`, and the corrected notes field
- `src/oscmcp/mcp_server.py` (this repo, `maxmsp_manager`) — the actual
  operations and addresses this tool sends today
- `docs/ONBOARDING.md` (this repo) — cost/license table and the corrected
  `udpreceive`/`udpsend`-or-odot setup note
