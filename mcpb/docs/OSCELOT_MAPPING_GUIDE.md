# OSCelot Detailed Mapping Guide

## Understanding OSCelot's UI

### The Dots/Tags System

OSCelot has **controller slots** on the left side of its interface. These appear as dots initially, but can be configured as different controller types:

- **Dot (unconfigured)** - Empty slot, not assigned
- **Slider/Fader** - For continuous parameters (knobs, sliders)
- **Button** - For on/off parameters (switches, buttons)
- **Encoder** - For rotary encoders (incremental values)

### How to Configure Controller Slots

1. **Click on a dot** on the left side of OSCelot
2. **Right-click** (or check context menu) to see controller type options
3. **Select controller type**: Slider, Button, or Encoder
4. **Configure OSC address**: Each slot needs an OSC address pattern
   - Slider: `/fader` or `/slider`
   - Button: `/button`
   - Encoder: `/encoder`

### Detailed Mapping Process

#### Step 1: Map a Parameter to OSCelot

1. **Click "Map" button** in OSCelot (enters mapping mode)
2. **Click on a knob/slider** on your module (e.g., VCO frequency)
3. OSCelot automatically creates a mapping entry
4. The parameter appears in OSCelot's list with:
   - Module ID
   - Parameter ID
   - Parameter name

#### Step 2: Assign to Controller Slot

1. **Find the mapped parameter** in OSCelot's list
2. **Click on an empty dot** (controller slot) on the left
3. **Right-click** to set controller type:
   - For knobs/sliders → Choose **"Slider"** or **"Fader"**
   - For buttons/switches → Choose **"Button"**
   - For incremental controls → Choose **"Encoder"**
4. **Set OSC address pattern**:
   - Slider: `/fader` (or `/slider`)
   - Button: `/button`
   - Encoder: `/encoder`
5. **Set Controller ID**: This is the slot number (0, 1, 2, etc.)
   - First slot = ID 0
   - Second slot = ID 1
   - etc.

#### Step 3: Link Parameter to Controller Slot

1. **Drag** the parameter from the list to the controller slot
2. OR **Click** the parameter, then **click** the controller slot
3. The dot should change to show the controller type (slider/button/encoder icon)
4. The parameter is now linked to that controller slot

### OSC Message Formats

Once configured, OSCelot expects these message formats:

#### Slider/Fader Format
```
Address: /fader
Arguments: [ControllerID, Value]
Example: /fader [1, 0.75]  (Controller slot 1, value 0.75)
```

#### Button Format
```
Address: /button
Arguments: [ControllerID, Value]
Example: /button [0, 1]  (Controller slot 0, button pressed)
```

#### Encoder Format
```
Address: /encoder
Arguments: [ControllerID, Value]
Example: /encoder [2, 0.5]  (Controller slot 2, encoder value)
```

### Alternative: Direct Parameter Mapping

OSCelot also supports direct parameter control without controller slots:

#### Direct /param Format
```
Address: /param
Arguments: [ModuleID, ParameterID, Value]
Example: /param [2, 0, 0.5]  (Module 2, Parameter 0, Value 0.5)
```

This bypasses the controller slot system entirely.

### Visual Guide

```
OSCelot Interface:
┌─────────────────────────────────────┐
│ [●] [●] [●] [●]  ← Controller slots │
│                                     │
│ Mapped Parameters:                  │
│ ┌─────────────────────────────┐   │
│ │ Module 2, Param 0: Frequency │   │
│ │ Module 2, Param 1: Waveform  │   │
│ │ Module 3, Param 0: Cutoff    │   │
│ └─────────────────────────────┘   │
│                                     │
│ [Map] [Clear] [Settings]           │
└─────────────────────────────────────┘
```

### Step-by-Step Example: Mapping VCO Frequency

1. **Add VCO module** to your patch
2. **Click "Map"** in OSCelot
3. **Click the Frequency knob** on VCO
4. Parameter appears in list: "Module 2, Param 0: Frequency"
5. **Click first dot** (slot 0) on left
6. **Right-click** → Select **"Slider"**
7. **Set address**: `/fader`
8. **Set Controller ID**: 0
9. **Link**: Drag parameter to slot 0 (or click parameter, then slot)
10. Dot changes to slider icon ✓

### Testing Your Mapping

After mapping, test with OSC-MCP:

```python
# For controller slot mapping (slider/fader)
await send_osc("127.0.0.1", 10001, "/fader", [0, 0.5])  # Slot 0, value 0.5

# For direct parameter mapping
await send_osc("127.0.0.1", 10001, "/param", [2, 0, 0.5])  # Module 2, Param 0
```

### Common Issues

**Problem**: Dots don't change to tags/icons
- **Solution**: Right-click the dot to configure controller type first
- Make sure you've mapped a parameter before assigning to slot

**Problem**: Parameter mapped but not responding
- **Check**: Controller slot is configured (not just a dot)
- **Check**: OSC address matches (e.g., `/fader` not `/param`)
- **Check**: Controller ID matches slot number

**Problem**: Don't know which format to use
- **Use `/fader` format** if you configured controller slots
- **Use `/param` format** for direct control (simpler, no slots needed)

### Recommended Approach

For OSC-MCP integration, **use direct `/param` format**:

1. Map parameters in OSCelot (click Map, click knob)
2. Note the Module ID and Parameter ID from OSCelot's display
3. Use `/param [ModuleID, ParamID, Value]` format
4. No need to configure controller slots!

This is simpler and works directly with OSC-MCP's `vcv_manager` tool.

