# OSCelot Simple Workflow (Skip the Confusing UI!)

## The Problem

OSCelot's UI is... let's say "challenging". The dots/slots/tags system is confusing and poorly documented.

## The Solution: Ignore the UI, Use Direct Mapping

**You don't need to configure controller slots!** Here's the simple way:

### Step 1: Map Parameters (Easy Part)

1. Click **"Map"** button in OSCelot
2. Click a **knob or slider** on your module
3. Done! Parameter is now mapped

### Step 2: Note the IDs

Look at OSCelot's parameter list. You'll see something like:
- "Module 2, Param 0: Frequency"
- "Module 2, Param 1: Waveform"
- "Module 3, Param 0: Cutoff"

**Write down or remember these numbers!**

### Step 3: Use Direct /param Format

**Skip all the dots/slots/address configuration!** Just use:

```python
# Direct parameter control - no slots needed!
await send_osc("127.0.0.1", 10001, "/param", [ModuleID, ParamID, Value])
```

**Example:**
```python
# Control VCO frequency (Module 2, Param 0)
await send_osc("127.0.0.1", 10001, "/param", [2, 0, 0.5])  # 50% frequency

# Control filter cutoff (Module 3, Param 0)
await send_osc("127.0.0.1", 10001, "/param", [3, 0, 0.7])  # 70% cutoff
```

### Step 4: Use OSC-MCP Tools (Even Easier!)

OSC-MCP's `vcv_manager` tool handles this for you:

```python
# No need to think about OSC addresses at all!
await vcv_manager("set_parameter", module_id=2, param_id=0, value=0.5)
await vcv_manager("set_parameter", module_id=3, param_id=0, value=0.7)
```

## What You DON'T Need to Do

❌ Configure controller slots (dots)
❌ Set OSC address patterns (`/fader`, `/button`, etc.)
❌ Assign Controller IDs
❌ Link parameters to slots
❌ Understand the tag system
❌ Fight with right-click menus

## What You DO Need

✅ Map parameters (click Map, click knob)
✅ Note Module ID and Parameter ID
✅ Use `/param` format or OSC-MCP tools

## Quick Reference

**OSCelot receives on port:** 10001
**OSCelot sends on port:** 10002 (optional)

**Direct parameter format:**
```
/param [ModuleID, ParamID, Value]
```

**Module IDs start at 1** (first module = 1, second = 2, etc.)
**Parameter IDs vary** (check OSCelot's display)

## Example: Complete Workflow

1. **Add VCO module** to patch
2. **Click "Map"** in OSCelot
3. **Click Frequency knob** on VCO
4. **See in OSCelot:** "Module 2, Param 0: Frequency"
5. **Control it:**
   ```python
   await send_osc("127.0.0.1", 10001, "/param", [2, 0, 0.5])
   ```
6. **Done!** No slot configuration needed.

## Why This Works

OSCelot supports two mapping modes:
1. **Controller slot mode** (confusing UI with dots/slots)
2. **Direct parameter mode** (simple `/param` format)

We're using mode #2 and ignoring mode #1 entirely!

## Troubleshooting

**Parameter not responding?**
- Check Module ID and Param ID are correct
- Make sure parameter is mapped (appears in OSCelot list)
- Verify OSCelot receive port = 10001
- Check Windows Firewall allows UDP port 10001

**Don't know the IDs?**
- Look at OSCelot's parameter list
- Or use `scripts/debug/read_oscelot_mapping.py` script to discover them

## Bottom Line

**Ignore OSCelot's confusing UI.** Just map parameters and use `/param` format. Life's too short to fight with dots and slots!
