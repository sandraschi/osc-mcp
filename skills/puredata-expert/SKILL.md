# Pure Data Expert

You are an expert on controlling Pure Data (Pd) via `osc-mcp`'s
`puredata_manager` tool. The single most important fact about Pd and OSC:
**vanilla Pure Data has no OSC support whatsoever.** Pd's core only ships
raw network primitives (`[netreceive]`/`[netsend]`, FUDI text protocol) —
turning bytes on a socket into an actual OSC message (address pattern +
typed arguments) requires a separate external library patched into the
user's `.pd` file. There is no way around this, and no version of "recent
Pd added OSC" — it is still true as of any current Pd release.

## The chain: Pd patch → transport objects → OSC (de)serializer objects

Two decisions have to be made correctly in the user's patch before any
`puredata_manager` call means anything:

1. **Transport (raw bytes)**: the mrpeach/mrpeach-successor library's own
   `[udpsend]`/`[udpreceive]` objects are the objects actually designed to
   carry OSC's binary payload — they hand you/take from you a list of
   raw byte values (0-255), not parsed FUDI messages.
   `[netreceive]`/`[netsend]` (Pd vanilla) can *also* be used if given the
   `-b` ("binary") creation flag (e.g. `[netreceive -b 3000]`) — without
   `-b` they default to **FUDI**, Pd's own semicolon-terminated text
   protocol, and will not carry OSC bytes correctly. `app_detect.py`'s note
   for `key="puredata"` — *"Needs `[netreceive]`/`[netsend]` or the OSC
   library patched in"* — is directionally right but underspecifies this:
   plain `[netreceive]` without `-b` does **not** give you OSC, only FUDI.
2. **OSC (de)serialization**: raw bytes from step 1 still aren't usable
   Pd messages — they need `[unpackOSC]` (binary bytes → OSC-address +
   typed args) and typically `[routeOSC]` (routes by address pattern) on
   the receive side, and `[oscformat]` / `[packOSC]` (Pd message → binary
   bytes) on the send side. These come from the **mrpeach** OSC library,
   now maintained at `github.com/pd-externals/osc` (older mirror:
   `github.com/pd-externals/mrpeach`) and installable through Pd's own
   Deken package manager (Help → "Find externals" → search "osc").
   `puredata-extended`/"Pd-extended" historically bundled mrpeach; vanilla
   Pd does not, so a fresh vanilla install needs the Deken install step.

So the real minimum patch to *receive* what `puredata_manager` sends is
something like: `[udpreceive 3000]` (or `[netreceive -b 3000]`) →
`[unpackOSC]` → `[routeOSC /whatever]`. There is no built-in equivalent.

## What `puredata_manager` actually sends

Verified by reading `puredata_manager` in `src/oscmcp/mcp_server.py`
directly (it has no separate wrapper class like the other apps —
the operation handlers call the shared `send_osc()` helper inline):

```python
puredata_manager(operation, host="127.0.0.1", port=9000,
                  receiver=None, value=None)
```

| Operation | Sends | Notes |
|---|---|---|
| `send_bang` | `/{receiver}` (no arguments) | **Fixed** — used to send a string argument whose value was the literal text `"bang"`; now sends a zero-argument message, matching mrpeach's idiomatic bang-over-OSC convention (`[routeOSC /foo]` emits a bang purely on receipt, regardless of arguments) |
| `send_float` | `/{receiver}, [value]` | Sends the address with a single float argument |
| `toggle_dsp` | `/pd/dsp/toggle` (no arguments) | Fixed address, not receiver-configurable — see Known gaps, still a project convention rather than a Pd standard |

These are real, well-formed OSC packets (via `pythonosc`) — the transport
and packet structure is correct. What's unverified is the *convention* on
the Pd-patch side.

## Known gaps

Fixed during this pass:
- ~~`send_bang`'s payload was a string `"bang"` argument~~ — now sends a
  zero-argument message instead, matching mrpeach's idiomatic convention.
- ~~Default port mismatch~~ — `puredata_manager`'s default (was `3000`)
  now matches `app_detect.py`'s `default_osc_port=9000`. Neither is a real
  Pd standard (Pd has no default OSC port), but they no longer disagree
  with each other inside the same codebase.

Still open:
- **No receiver-name validation or address-escaping.** `receiver` is
  interpolated directly into an OSC address path (`f"/{receiver}"`) with
  no check for embedded slashes, spaces, or OSC-invalid characters.
- **No feedback/read path.** `puredata_manager` never listens for
  anything Pd might send back (e.g. via `[udpsend]`/`[netsend]` from the
  patch to this server) — it is fire-and-forget only, consistent with
  every other manager in this fleet.
- **`toggle_dsp`'s address is a guess at convention, not a Pd or mrpeach
  standard.** `/pd/dsp/toggle` is not a real address Pd or mrpeach
  reserves or listens for out of the box — DSP on/off in Pd is normally
  driven by the `pd dsp 1`/`pd dsp 0` message to Pd's own internal `pd`
  object (via `[; pd dsp 1(` inside a patch, not over the network at all)
  or by whatever address the user's own patch happens to route to a
  `[; pd dsp $1(` message object. Treat `/pd/dsp/toggle` as this
  project's own convention that only works if the target patch has been
  built to listen for exactly that address — **not a Pd-wide standard**.

## Best practices

1. **Never assume a fresh/default Pd install can receive anything this
   tool sends.** The user must have mrpeach's OSC objects (via Deken) and
   a transport object (`[udpreceive]`, or `[netreceive -b]`) patched in
   first, plus `[unpackOSC]`/`[routeOSC]` wired to the receiver name being
   used.
2. **Confirm which port the user's own `[udpreceive N]`/
   `[netreceive -b N]` object is actually instantiated with** — don't
   trust the `9000` default without asking; it's this repo's own
   convention, not a Pd standard.
3. **`send_bang` now matches mrpeach's idiomatic zero-argument convention**,
   but if a user reports it "doesn't trigger anything," check their
   patch's `[routeOSC]` wiring by printing the raw `[unpackOSC]` output.
4. **Don't invent additional Pd OSC addresses.** There is no Pd-wide OSC
   dictionary the way QLab or obs-websocket have one — every address is
   whatever the specific patch happens to route, entirely user-defined.

## Primary sources

- `github.com/pd-externals/osc` — the current mrpeach/OSC library repo
  (`[packOSC]`, `[unpackOSC]`, `[routeOSC]`, `[pipelist]`,
  `[packOSCstream]`, `[unpackOSCstream]`), by Martin Peach, built with
  `pd-lib-builder`, installed via Deken
- `sourceforge.net/p/pure-data/svn/HEAD/tree/trunk/externals/mrpeach/osc/`
  — the older mrpeach SVN tree (`routeOSC-help.pd`, `unpackOSC-help.pd`,
  `oscformat`), for object-name history
- `pd.iem.sh/objects/netreceive/` — vanilla Pd's `[netreceive]`, its
  default FUDI behavior, and the `-b` binary-mode flag
- `lists.puredata.info` pd-list thread, "netreceive vs mrpeach/udpreceive
  in batch mode" — real-world confirmation transport objects (not
  OSC-parsing objects) are the layer that differs
- `src/oscmcp/mcp_server.py` (`puredata_manager`, around line 2718) — the
  actual implementation this skill documents
- `src/oscmcp/app_detect.py` (`key="puredata"`) — install path, process
  name, and `default_osc_port=9000`
- `docs/ONBOARDING.md` — Pure Data section, updated to name mrpeach and
  the `[netreceive -b]` binary-mode requirement explicitly
