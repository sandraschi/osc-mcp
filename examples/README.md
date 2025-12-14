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