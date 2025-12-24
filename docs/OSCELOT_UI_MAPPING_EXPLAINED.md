# OSCelot UI Mapping Explained

## Understanding the Dots/Slots

The **dots on the left side** are **mapping slots**. They start empty and become configured when you map a parameter AND send an OSC message.

## How the UI Mapping Actually Works

### Step-by-Step UI Workflow

1. **Click on a mapping slot** (one of the dots on the left)
   - The slot becomes active/selected
   - It shows "Mapping..." or similar indicator

2. **Click on a parameter** in VCV Rack (knob, slider, button)
   - This binds the parameter to that slot
   - The slot now shows the parameter name

3. **Send an OSC message from your controller**
   - The OSC message format determines the slot type:
     - `/fader` message → Slot becomes a **Fader**
     - `/button` message → Slot becomes a **Button**
     - `/encoder` message → Slot becomes an **Encoder**
   - The slot icon changes to match the type

### The Key Point

**The slot type (fader/button/encoder) is determined by the OSC address you send, NOT by right-clicking or UI configuration!**

## OSC Message Formats Required

### For Fader/Slider Slots
```
Address: /fader (or anything ending with /fader)
Arguments: [Id, Value]
Example: /fader [1, 0.5]
```
- Id = Controller ID (slot number)
- Value = 0.0 to 1.0

### For Button Slots
```
Address: /button (or anything ending with /button)
Arguments: [Id, Value]
Example: /button [0, 1.0]
```
- Id = Controller ID (slot number)
- Value = 0.0 or 1.0 (on/off)

### For Encoder Slots
```
Address: /encoder (or anything ending with /encoder)
Arguments: [Id, Delta]
Example: /encoder [2, 1.0]
```
- Id = Controller ID (slot number)
- Delta = -1.0 or +1.0 (incremental change)

## Complete UI Workflow Example

**Mapping VCO Frequency to a Fader:**

1. **Click first mapping slot** (leftmost dot)
   - Slot becomes active

2. **Click "Map" button** in OSCelot (optional, but helps)

3. **Click the Frequency knob** on VCO module
   - Parameter name appears in slot: "Frequency" or "Module 2, Param 0"

4. **Send OSC message from controller:**
   ```
   /fader [0, 0.5]
   ```
   - Address ends with `/fader` → Slot becomes Fader type
   - Controller ID = 0 (first slot)
   - Value = 0.5

5. **Slot icon changes** to fader/slider icon ✓

## Why This Is Confusing

The documentation doesn't clearly explain that:
- You need an **OSC controller** to send messages during mapping
- The **OSC address format** determines the slot type
- There's no right-click menu to configure slot types
- The slot type is **inferred from the OSC message** you send

## Alternative: Direct Parameter Mapping (No Slots)

If you don't have an OSC controller to send messages during mapping, you can use **direct parameter mapping**:

1. Click "Map" button
2. Click parameter (knob/slider)
3. Parameter appears in OSCelot's list with Module ID and Param ID
4. Use `/param [ModuleID, ParamID, Value]` format directly
5. No slots needed!

## The Confusion Explained

The dots don't "become tags" through UI configuration. They become fader/button/encoder icons **only after** you:
1. Map a parameter (click slot, click parameter)
2. Send an OSC message with the appropriate address format

**Without an OSC controller sending messages during mapping, the slots stay as dots!**

## Solution for OSC-MCP Users

Since you're using OSC-MCP programmatically, you don't need the slot system at all:

1. **Map parameters** (click Map, click knob) - this creates the mapping
2. **Use `/param` format** directly:
   ```python
   await send_osc("127.0.0.1", 10001, "/param", [ModuleID, ParamID, Value])
   ```
3. **Ignore the slots entirely** - they're for hardware OSC controllers

The slots are designed for **hardware OSC controllers** (like TouchOSC, Lemur, etc.) that send `/fader`, `/button`, `/encoder` messages. For programmatic control via OSC-MCP, use `/param` format instead.

