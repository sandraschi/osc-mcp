# cvOSCcv Setup Guide

## Step 1: Install cvOSCcv

1. **Open VCV Rack**
2. **Open Library menu** (top menu bar)
3. **Search for "cvOSCcv"** in the search box
4. **Click "Add"** next to cvOSCcv (by trowaSoft)
5. **Click "Update all"** in Library menu
6. **Restart VCV Rack** if prompted

## Step 2: Add cvOSCcv to Your Patch

1. **Right-click** empty space in VCV Rack
2. **Search for "cvOSCcv"** in module browser
3. **Click** to add cvOSCcv module to patch

## Step 3: Configure cvOSCcv

### Basic Configuration

1. **Set Port:**
   - Default: **10001** (same as OSCelot)
   - Change if needed in cvOSCcv's port field

2. **Set Host:**
   - Default: **127.0.0.1** (localhost)
   - Change if controlling from another computer

3. **Enable Channels:**
   - Click channel enable buttons (LEDs should light up when active)
   - Each channel can be independently enabled/disabled

### Configure OSC Addresses

For each channel you want to use:

1. **Click on channel** in cvOSCcv
2. **Set OSC address** (right-click or use context menu):
   - Channel 0: `/cv/0` or `/vco/freq`
   - Channel 1: `/cv/1` or `/filter/cutoff`
   - Channel 2: `/cv/2` or `/vca/level`
   - Or use custom addresses like `/my/patch/parameter1`

3. **Set Value Range:**
   - Default: 0.0 to 1.0 (normalized)
   - Can be changed to match CV range (-10V to +10V)

## Step 4: Connect CV Signals

### Example: VCO Frequency Control

1. **Add VCO module** to patch
2. **Connect VCO CV output** → **cvOSCcv input 0**
3. **Set cvOSCcv channel 0 address** to `/vco/freq` (or `/cv/0`)
4. **Enable channel 0** (LED should light up)

### Example: Multiple Parameters

```
VCO CV Out → cvOSCcv Input 0 (/vco/freq)
Filter CV Out → cvOSCcv Input 1 (/filter/cutoff)
VCA CV Out → cvOSCcv Input 2 (/vca/level)
LFO CV Out → cvOSCcv Input 3 (/lfo/rate)
```

## Step 5: Test with OSC-MCP

### Basic Test

```python
# Test channel 0
await send_osc("127.0.0.1", 10001, "/cv/0", [0.5])
# Or custom address:
await send_osc("127.0.0.1", 10001, "/vco/freq", [0.5])
```

### Using OSC-MCP vcv_manager

OSC-MCP's `vcv_manager` can be adapted, or use direct OSC:

```python
# Direct OSC control (simpler with cvOSCcv)
await send_osc("127.0.0.1", 10001, "/cv/0", [0.5])  # 50% value
await send_osc("127.0.0.1", 10001, "/cv/1", [0.7])  # 70% value
```

## Step 6: Verify It Works

1. **Check cvOSCcv LEDs:**
   - Enabled channels should show activity LEDs
   - LEDs blink when OSC messages are received

2. **Monitor CV outputs:**
   - Connect cvOSCcv outputs to modules
   - CV values should change when OSC messages arrive

3. **Test script:**
   - Run `test_cvosccv.py` (see below)
   - Should see parameter changes in VCV Rack

## OSC Message Format

### Sending to cvOSCcv

```
Address: /cv/{channel} (or custom address)
Value: [0.0 to 1.0] (normalized)
Example: /cv/0 [0.5]
```

### Receiving from cvOSCcv

cvOSCcv can also send OSC messages when CV inputs change:
- Configure output addresses in cvOSCcv
- Connect CV sources to cvOSCcv inputs
- cvOSCcv sends OSC when CV changes

## Advantages Over OSCelot

✅ **No mapping slots** - Just connect CVs  
✅ **Clear addresses** - Set custom OSC addresses per channel  
✅ **Visual feedback** - LEDs show activity  
✅ **Standard workflow** - Normal modular patching  
✅ **Bidirectional** - Send and receive OSC  

## Troubleshooting

**No response:**
- Check port matches (default: 10001)
- Verify channel is enabled (LED should be on)
- Check OSC address matches exactly
- Verify Windows Firewall allows UDP port 10001

**Wrong values:**
- Check value range (0.0-1.0 normalized vs -10V to +10V)
- Verify CV connections are correct
- Check attenuator settings in cvOSCcv

**LEDs not lighting:**
- Enable channel (click enable button)
- Check OSC messages are being sent
- Verify port and address are correct

## Next Steps

1. Replace OSCelot with cvOSCcv in your patches
2. Update OSC-MCP scripts to use cvOSCcv addresses
3. Create custom OSC address schemes for your patches
4. Use cvOSCcv expander for more channels if needed













