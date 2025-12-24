# How to Map Parameters in OSCelot

## Quick Mapping Steps

1. **Add a module to your patch** (e.g., VCO oscillator, MIDI module)
2. **Click on OSCelot** to select it
3. **Click the "Map" button** in OSCelot (or "Learn" mode)
4. **Click on a knob/slider** on your module (e.g., VCO frequency knob)
5. **OSCelot creates the mapping automatically**
6. **Note the module ID and parameter ID** that OSCelot shows

## What You Need to Map for Frère Jacques

To play the melody, you need:

### Option 1: MIDI Module (Easiest)
- Add a **MIDI-1** or **MIDI-CV** module
- Map it to receive MIDI notes
- The script will send MIDI notes directly

### Option 2: VCO + Sequencer
- Add a **VCO** (oscillator)
- Add a **Sequencer** or **Clock** module
- Map VCO frequency parameter
- Map sequencer trigger/gate

## Module IDs

- Module IDs start from **1** (not 0)
- First module in patch = ID 1
- Second module = ID 2, etc.
- Check OSCelot's mapping display to see module IDs

## After Mapping

Once mapped, you can:
- Control parameters via OSC
- See parameter changes in real-time
- Use the Frère Jacques script to play music

## Test Your Mapping

After mapping a parameter:
1. Run: `python test_vcv_connection.py`
2. Check if the mapped parameter responds
3. Adjust module_id and param_id in the script if needed

