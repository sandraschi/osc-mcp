# OSC-MCP Examples

This directory contains example scripts demonstrating OSC-MCP functionality.

## VCV Rack Demo (`vcv_rack_demo.py`)

A comprehensive demonstration of the extended VCV Rack OSC integration tools.

### Features Demonstrated
- MIDI note control (play/stop notes, send CC messages)
- Parameter control (module parameters 0.0-1.0 range)
- CV control (control voltages -10.0 to +10.0V)
- Light control (module LEDs 0.0-1.0 brightness)
- Trigger events (module triggers)
- Module-specific controls:
  - VCO frequency (Hz, auto-converted)
  - VCA level (0.0-1.0)
  - LFO rate (0.0-1.0)
  - Filter cutoff (0.0-1.0)
  - ADSR envelope controls (attack, decay, sustain, release)

### Prerequisites
- VCV Rack with OSC module installed (OSCelot, cvOSCcv, or Holonic Source recommended)
- OSC module configured to listen on port 10001 (default)
- Python environment with osc-mcp installed

### Usage
```bash
cd /path/to/osc-mcp
python examples/vcv_rack_demo.py
```

### Expected Output
The script sends various OSC messages to demonstrate all functionality. Check your VCV Rack patch for parameter changes, MIDI notes, CV signals, and light changes.

### Integration with Claude Desktop
Use natural language commands like:
- "Play a C4 note in VCV Rack"
- "Set the VCO frequency to 440Hz"
- "Send 5 volts to CV input 1 on module 2"
- "Trigger the envelope on module 3"

## Bach Organ Performance Demo (`bach_organ_demo.py`)

A high-level orchestration demo showing complex multi-step music production workflows using the `music_orchestrator` tool.

### Features Demonstrated
- **Complete rig setup**: Automatic VCV Rack configuration for organ synthesis
- **Bach MIDI loading**: Parse and prepare organ music for performance
- **Cross-application sync**: Coordinate VCV Rack with REAPER DAW
- **Performance recording**: Capture and replay OSC automation sequences
- **Organ voice configuration**: Drawbar settings, reverb, and cathedral acoustics
- **Real-time orchestration**: Start/stop/control synchronized performances

### Prerequisites
- **VCV Rack** with wavetable synthesis modules (see recommendations below)
- **Bach MIDI files** (download from free sources listed in script)
- **Optional: REAPER DAW** for enhanced mixing and effects
- **Surge XT modules** (free, professional wavetable synth) OR **Bogaudio FM-OP** (excellent free wavetable)

### Free Wavetable Modules for Organ Synthesis

| Module | Description | Why for Organs |
|--------|-------------|----------------|
| **Surge XT** | Professional hybrid synth with wavetable oscillators | 🎯 **BEST** - Full wavetable synth with effects |
| **Bogaudio FM-OP** | Excellent free wavetable oscillator | Great FM + wavetable hybrid |
| **Valley Audio Terrorform** | Advanced wavetable with user tables | Load custom organ wavetables |
| **VCV Wavetable VCO** | Built-in basic wavetable | Simple but effective |
| **Erica Synths Black Wavetable VCO** | Compact wavetable VCO | Good basic wavetable |

### Usage
```bash
# Full Bach performance demo (requires MIDI file)
python examples/bach_organ_demo.py

# Quick test without MIDI file
python examples/bach_organ_demo.py --quick

# Show free module recommendations
python examples/bach_organ_demo.py --modules

# Show Bach MIDI file sources
python examples/bach_organ_demo.py --midi
```

### What It Does
1. **Auto-configures organ synthesis** in VCV Rack using Surge XT wavetables
2. **Sets up classic organ voice** (drawbars: 8', 4', 2', reverb, tremolo)
3. **Loads Bach MIDI** and converts to CV sequences for modular synth
4. **Synchronizes tempo** across VCV Rack and REAPER
5. **Records performance** for later replay or debugging
6. **Provides manual controls** for real-time performance adjustments

### Free Bach MIDI Sources
- **Kunst der Fuge**: Extensive Bach organ collection
- **MIDI DB**: Toccata and Fugue, Preludes and Fugues
- **BitMidi**: Various Bach organ works
- **MIDIWorld**: Bach MIDI database

### Integration with Claude Desktop
Use high-level commands like:
- "Set up a Bach organ performance in my rig"
- "Load Toccata and Fugue and configure organ synthesis"
- "Start synchronized performance across VCV Rack and REAPER"
- "Record this performance for later replay"