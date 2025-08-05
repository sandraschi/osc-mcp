# OSCMCP DXT Prompts

## OSC Message Handling

## Basic OSC Commands

- **Message Sending**
  - "Send /test 1 2 3 to 192.168.1.100:8000"
  - "Listen for /volume messages on port 9000"
  - "Route /audio/* to AudioMCP"
  - "Convert MIDI to OSC on channel 1"
  - "Forward all OSC messages to 10.0.0.5:7000"
  - "Log all incoming OSC messages to file"
  - "Create an OSC alias /brightness for /lights/dimmer"
  - "Throttle OSC messages to 30 FPS"
  - "Mirror /left to /right with inverted values"
  - "Add a 100ms delay to /video/effects"

## Message Transformation

- **Value Manipulation**
  - "Map /knob1 to range 0-127"
  - "Invert values for /fader5"
  - "Scale /input by 2.5"
  - "Add 0.5 to all values in /offset/*"
  - "Round /position/x to nearest integer"
  - "Convert /toggle to bang on change"
  - "Smooth /jogwheel with 200ms window"
  - "Quantize /pitch to nearest semitone"
  - "Limit /frequency to 20-20000 Hz"
  - "Apply low-pass filter to /motion/x"

## Routing & Filtering

- **Message Flow**
  - "Route /ableton/* to 127.0.0.1:9001"
  - "Block all messages from 192.168.1.42"
  - "Forward only /transport/* to QLab"
  - "Duplicate /master to /headphones"
  - "Merge /left and /right to /stereo"
  - "Split /xy to /x and /y"
  - "Only pass /sensor values > 0.5"
  - "Throttle /video/fps to 60Hz"
  - "Route by message size under 100 bytes"
  - "Filter OSC bundles by IP range"

## MIDI Integration

- **MIDI to OSC**
  - "Map CC#7 to /volume"
  - "Convert MIDI note 60 to /kick"
  - "Forward MIDI clock as /transport"
  - "Convert pitch bend to /pitch"
  - "Map aftertouch to /pressure"
  - "Convert program change to /preset"
  - "Split MIDI channels to /ch1/*/ch2/*"
  - "Convert NRPN to /param1, /param2"
  - "Forward MIDI start/stop/continue"
  - "Map sustain pedal to /reverb/on"

- **OSC to MIDI**
  - "Send /note to MIDI channel 1"
  - "Map /fader1 to CC#74"
  - "Convert /bang to MIDI note on"
  - "Route /clock to MIDI clock out"
  - "Map /chord to multiple MIDI notes"
  - "Convert /pressure to channel aftertouch"
  - "Send /alloff as MIDI all notes off"
  - "Map /program to MIDI program change"
  - "Convert /pitchbend to 14-bit MIDI"
  - "Send /panic as MIDI reset"

## Advanced Features

- **Message Generation**
  - "Generate LFO on /lfo1 at 2Hz"
  - "Create random walk on /noise"
  - "Pulse /metronome every quarter note"
  - "Record 10 seconds to /loop1"
  - "Playback /sequence1 at 120 BPM"
  - "Generate sine wave on /test"
  - "Create step sequencer on /seq1"
  - "Trigger /sample1 on /bang"
  - "Generate Perlin noise on /flow"
  - "Create Euclidean rhythm on /euclid"

- **Conditional Logic**
  - "If /x > 0.5 then /led on"
  - "When /button1 pressed, send /cue/1"
  - "While /hold is 1, loop /clip1"
  - "Unless /mute, forward /audio"
  - "After 5s, send /timeout"
  - "Every 2s, send /heartbeat"
  - "On /start, begin sequence"
  - "If /error > 0, flash /warning"
  - "When /level peaks, trigger /comp"
  - "While /recording, log to /data"

## Data Processing

- **Signal Processing**
  - "Average last 10 /sensor values"
  - "Calculate derivative of /position"
  - "Integrate /velocity to /position"
  - "Find peaks in /waveform"
  - "Smooth /jitter with moving average"
  - "Detect silence in /input"
  - "Normalize /levels to 0-1"
  - "Calculate FFT of /signal"
  - "Detect BPM from /tap"
  - "Apply hysteresis to /switch"

## System Integration

- **External Commands**
  - "On /shutdown, run cleanup script"
  - "When /error, send email alert"
  - "Log /status to database"
  - "On /backup, save current state"
  - "If /temperature > 80, trigger fan"
  - "When /show starts, launch QLab"
  - "On /midnight, run maintenance"
  - "If /disk > 90%, send warning"
  - "When /user arrives, load profile"
  - "On /emergency, all systems stop"

## Debugging

- **Troubleshooting**
  - "Show OSC traffic on port 8000"
  - "Log all errors to console"
  - "Monitor CPU/RAM usage"
  - "Test connection to 192.168.1.100"
  - "List all active OSC routes"
  - "Show message rate statistics"
  - "Dump current state to file"
  - "Test MIDI input/output"
  - "Measure latency to target"
  - "Generate test signal"

## Creative Applications

- **Interactive Installations**
  - "Map /distance to /volume"
  - "Convert camera input to OSC"
  - "Control lights with /gesture"
  - "Sonify /temperature data"
  - "React to /motion with sound"
  - "Visualize /network traffic"
  - "Create feedback loop with /mic"
  - "Generate music from /twitter"
  - "Control robot arm with /leap"
  - "Create theremin with /distance"

- **Performance Controls**
  - "Map /dance to visuals"
  - "Sync lights to /beat"
  - "Record performance to /take1"
  - "Fade lights on /crescendo"
  - "Trigger samples with /drum"
  - "Crossfade /scene1 to /scene2"
  - "Map /expression to filter"
  - "Sync video to /timeline"
  - "Generate visuals from /audio"
  - "Create lighting cues from /score"
