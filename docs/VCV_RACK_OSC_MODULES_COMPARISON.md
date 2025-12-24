# VCV Rack OSC Modules Comparison

## The Problem with OSCelot

OSCelot's UI is confusing:
- Unclear mapping workflow
- Dots/slots system is poorly documented
- Requires OSC controller during mapping
- Non-intuitive interface

## Alternatives

### 1. cvOSCcv (trowaSoft) - **RECOMMENDED**

**Author:** j4s0n-c (trowaSoft)  
**VCV Library:** https://library.vcvrack.com/trowaSoft/cvOSCcv  
**License:** BSD-3-Clause  
**Popularity:** 47,397 downloads

#### Features
- ✅ **Bidirectional OSC** - Send and receive CV signals
- ✅ **8 channels** (expandable with expander modules)
- ✅ **Polyphonic support**
- ✅ **Simpler interface** - Direct CV to OSC mapping
- ✅ **No confusing slot system** - Just connect CVs
- ✅ **Activity LEDs** - Visual feedback per channel

#### How It Works
1. **Add cvOSCcv module** to patch
2. **Connect CV outputs** from modules to cvOSCcv inputs
3. **Configure OSC addresses** per channel
4. **Set port** (default: 10001)
5. **Done!** CV values automatically sent as OSC

#### OSC Format
```
Address: /cv/{channel} (or custom address)
Value: CV voltage (-10V to +10V, normalized to 0.0-1.0)
Example: /cv/0 [0.5]  (Channel 0, 50% value)
```

#### Advantages Over OSCelot
- ✅ **Simpler**: Just connect CVs, no mapping slots
- ✅ **More intuitive**: Standard modular patching workflow
- ✅ **Visual feedback**: LEDs show activity
- ✅ **Bidirectional**: Can receive OSC and output CV
- ✅ **Expandable**: Add more channels with expander

#### Disadvantages
- ⚠️ Requires CV connections (not direct parameter mapping)
- ⚠️ Need to patch CV outputs to cvOSCcv inputs

### 2. Holonic Source (Holonic Systems)

**Author:** Holonic Systems  
**Website:** https://holon.ist/vcv/  
**Focus:** iOS app integration

#### Features
- ✅ **iOS app integration** (Holon.ist app)
- ✅ **Activity LEDs** per channel
- ✅ **Attenuators** for scaling values
- ✅ **Low-pass filters** to smooth signals
- ✅ **8 channels**

#### Use Case
- Best for: iOS device control via Holon.ist app
- Not ideal for: Programmatic OSC control

### 3. OSCelot (Current - Not Recommended)

**Author:** TheModularMind  
**Status:** Confusing UI, poor documentation

#### Problems
- ❌ Confusing dots/slots/tags system
- ❌ Requires OSC controller during mapping
- ❌ Poor documentation
- ❌ Non-intuitive workflow

#### Only Advantage
- ✅ Direct parameter mapping (no CV patching needed)

## Recommendation: Switch to cvOSCcv

### Why cvOSCcv is Better

1. **Simpler Workflow:**
   ```
   OSCelot: Click Map → Click Parameter → Send OSC → Configure Slot → ???
   cvOSCcv: Connect CV → Set Address → Done!
   ```

2. **Standard Modular Approach:**
   - Uses CV connections (normal modular workflow)
   - No special mapping modes
   - Visual feedback with LEDs

3. **Better for Programmatic Control:**
   - Clear OSC address format
   - No confusing slot system
   - Works directly with OSC-MCP

### Migration from OSCelot to cvOSCcv

**Old (OSCelot):**
```python
# Confusing - need to map parameters first
await send_osc("127.0.0.1", 10001, "/param", [2, 0, 0.5])
```

**New (cvOSCcv):**
```python
# Simple - just send to channel address
await send_osc("127.0.0.1", 10001, "/cv/0", [0.5])
# Or custom address: /vco/frequency [0.5]
```

### Setup cvOSCcv

1. **Install from VCV Library:**
   - Search "cvOSCcv" in Library
   - Add → Update all

2. **Add to Patch:**
   - Drag cvOSCcv module
   - Connect CV outputs to cvOSCcv inputs
   - Example: VCO CV output → cvOSCcv input 0

3. **Configure:**
   - Set port (default: 10001)
   - Set OSC address per channel (e.g., `/cv/0`, `/vco/freq`)
   - Enable channel (LED should light up)

4. **Control via OSC-MCP:**
   ```python
   await send_osc("127.0.0.1", 10001, "/cv/0", [0.5])
   ```

## Comparison Table

| Feature | OSCelot | cvOSCcv | Holonic Source |
|---------|---------|---------|----------------|
| **UI Complexity** | ❌ Confusing | ✅ Simple | ✅ Simple |
| **Mapping Workflow** | ❌ Complex | ✅ Easy | ✅ Easy |
| **Documentation** | ❌ Poor | ✅ Good | ✅ Good |
| **Direct Parameter Control** | ✅ Yes | ⚠️ Via CV | ⚠️ Via CV |
| **Bidirectional** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Visual Feedback** | ❌ Limited | ✅ LEDs | ✅ LEDs |
| **Programmatic Control** | ⚠️ Confusing | ✅ Clear | ⚠️ iOS-focused |
| **Expandable Channels** | ❌ No | ✅ Yes | ✅ Yes |

## Bottom Line

**Switch to cvOSCcv!** It's:
- ✅ Simpler to use
- ✅ Better documented
- ✅ More intuitive
- ✅ Better for programmatic control
- ✅ Standard modular workflow

The only trade-off: You need to patch CV connections instead of direct parameter mapping, but that's actually more flexible and follows standard modular synthesis workflow.













