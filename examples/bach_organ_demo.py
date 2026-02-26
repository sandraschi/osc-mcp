#!/usr/bin/env python3
"""
Bach Organ Performance Demo - OSC-MCP Music Orchestrator

This demo shows how to use osc-mcp's music_orchestrator tool to:
1. Load J.S. Bach organ MIDI files
2. Auto-configure VCV Rack with organ synthesis modules
3. Synchronize with REAPER DAW
4. Perform the music with AI orchestration

Requirements:
- VCV Rack with Surge XT modules (free) or Bogaudio FM-OP (free)
- REAPER (optional, for enhanced mixing)
- Bach MIDI files (download from midi.org, kunstderfuge.com, etc.)

Free VCV Rack Modules Recommended:
- Surge XT: Professional wavetable synth, perfect for organs
- Bogaudio FM-OP: Excellent free wavetable oscillator
- Valley Audio Terrorform: Advanced wavetable with user tables

Usage:
1. Install Surge XT modules in VCV Rack Library
2. Download Bach organ MIDI (e.g., Toccata and Fugue)
3. Run this script or use Claude with osc-mcp server
"""

import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from src.oscmcp.mcp_server import (
        audio_workflow_manager,
        music_orchestrator,
        osc_recorder_manager,
        start_osc_server,
        stop_osc_server,
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure osc-mcp is properly installed or run from the project root")
    sys.exit(1)


async def bach_organ_demo():
    """
    Complete Bach organ performance orchestration demo
    """
    print("🎵 OSC-MCP Bach Organ Performance Demo")
    print("=" * 50)

    # Step 1: Start OSC server to receive feedback
    print("\n1. Starting OSC server for bidirectional communication...")
    server_result = await start_osc_server(10001)
    print(f"✅ Server: {server_result['message']}")

    try:
        # Step 2: Bach organ rig setup
        print("\n2. Configuring Bach organ synthesis rig...")
        bach_midi_path = "path/to/bach-toccata.mid"  # Replace with actual path

        organ_result = await music_orchestrator(
            operation="bach_organ_setup",
            midi_file_path=bach_midi_path,
            organ_module=1,  # Surge XT VCO in slot 1
            tempo=120.0,  # Appropriate for Bach organ
            sync_apps=True,
            record_performance=True,
            recording_name="bach_toccata_performance",
        )

        print("✅ Rig configuration:")
        for step in organ_result["steps"]:
            print(f"   • {step['step']}: {step['status']}")
        print(f"🎹 Ready message: {organ_result.get('ready_message', 'Setup complete!')}")

        # Step 3: Configure organ voice (drawbars, reverb)
        print("\n3. Setting up organ voice characteristics...")
        voice_result = await music_orchestrator(operation="organ_voice_setup", organ_module=1)

        print("✅ Organ voice configured:")
        for setting in voice_result["organ_settings"]:
            print(f"   • {setting['parameter']}: {setting['value']}")

        # Step 4: Start synchronized performance
        print("\n4. Starting synchronized performance...")
        print("🎼 Get ready for Bach!")

        perf_result = await music_orchestrator(operation="performance_start", sync_apps=True)

        print("✅ Performance started:")
        for app in perf_result["coordinated_apps"]:
            print(f"   • {app['app']}: {app['operation']}")

        # Step 5: Let it play for a bit, then demonstrate control
        print("\n5. Performance in progress...")
        print("💡 During performance, you can:")
        print("   • Monitor OSC messages with get_received_messages()")
        print("   • Adjust parameters in real-time")
        print("   • Stop with performance_stop()")

        # Simulate performance duration (in real use, this would be the actual play time)
        await asyncio.sleep(2)

        # Step 6: Stop performance and save recording
        print("\n6. Stopping performance and saving recording...")
        stop_result = await music_orchestrator(
            operation="performance_stop", recording_name="bach_toccata_performance"
        )

        print("✅ Performance stopped:")
        for app in stop_result["stopped_apps"]:
            print(f"   • {app['app']}: Stopped")

        # Step 7: Show recording info
        print("\n7. Performance recording saved:")
        record_info = await osc_recorder_manager(
            operation="get_recording_info", recording_name="bach_toccata_performance"
        )

        if record_info["status"] == "success":
            print(f"   • Duration: {record_info['duration']:.1f} seconds")
            print(f"   • Messages: {record_info['message_count']}")
            print(f"   • OSC addresses used: {', '.join(record_info['addresses'])}")

        # Step 8: Demonstrate replay
        print("\n8. Replaying performance at half speed...")
        replay_result = await osc_recorder_manager(
            operation="playback_recording",
            recording_name="bach_toccata_performance",
            playback_speed=0.5,
        )

        if replay_result["status"] == "success":
            print(f"✅ Replayed {replay_result['messages_sent']} messages at 50% speed")

        print("\n" + "=" * 50)
        print("🎵 Bach Organ Demo Complete!")
        print("\nKey takeaways:")
        print("• music_orchestrator handles complex multi-step workflows")
        print("• Automatic rig configuration for different instruments")
        print("• Cross-application synchronization (VCV + REAPER)")
        print("• Performance recording and replay capabilities")
        print("• Real-time OSC monitoring and control")

        print("\n📚 Try these next:")
        print("• Download more Bach MIDI from kunstderfuge.com")
        print("• Experiment with different Surge XT wavetables")
        print("• Add REAPER for mixing and effects")
        print("• Create custom workflows with create_custom_workflow")

    finally:
        # Cleanup
        print("\n🧹 Cleaning up OSC server...")
        cleanup_result = await stop_osc_server(10001)
        print(f"✅ Cleanup: {cleanup_result['message']}")


async def quick_bach_test():
    """
    Quick test without full MIDI file - demonstrates the orchestration concept
    """
    print("🎵 Quick Bach Organ Test (no MIDI file required)")

    # Start server
    await start_osc_server(10001)

    try:
        # Configure organ sound
        print("\nSetting up organ synthesis...")
        result = await music_orchestrator(operation="organ_voice_setup", organ_module=1)

        if result["status"] == "success":
            print("✅ Organ voice configured!")
            print("🎹 Ready to play Bach manually with vcv_manager tools")

            print("\nTry these manual controls:")
            print("• vcv_manager('set_vco_frequency', module_id=1, frequency=261.63)  # C4")
            print("• vcv_manager('set_envelope_attack', module_id=2, attack=0.1)     # Fast attack")
            print("• vcv_manager('play_midi', note=60, velocity=80)                  # Middle C")

        else:
            print(f"❌ Setup failed: {result.get('message', 'Unknown error')}")

    finally:
        await stop_osc_server(10001)


def show_free_module_recommendations():
    """
    Display recommendations for free VCV Rack modules
    """
    print("\n🎛️  FREE VCV Rack Modules for Organ Synthesis:")
    print("=" * 50)

    recommendations = [
        ("Surge XT Modules", "Professional wavetable synth - BEST for organs", "FREE"),
        ("Bogaudio FM-OP", "Excellent wavetable oscillator", "FREE"),
        ("Valley Audio Terrorform", "Advanced wavetable with user tables", "FREE"),
        ("VCV Wavetable VCO", "Built-in basic wavetable", "FREE"),
        ("Erica Synths Black Wavetable VCO", "Compact wavetable VCO", "FREE"),
        ("Vector Modular baseOsc", "Versatile oscillator with wavetable", "FREE"),
    ]

    for name, desc, cost in recommendations:
        print("15")

    print("\n📥 Install: Open VCV Rack → Library → Search for module name → Add")
    print("🎵 For organs: Surge XT gives professional results!")


def show_bach_midi_sources():
    """
    Show where to get free Bach MIDI files
    """
    print("\n🎼 FREE Bach Organ MIDI Files:")
    print("=" * 50)

    sources = [
        ("Kunst der Fuge", "kunstderfuge.com", "Extensive Bach organ collection"),
        ("MIDI DB", "mididb.com", "Toccata and Fugue, Preludes"),
        ("BitMidi", "bitmidi.com", "Various Bach organ works"),
        ("MIDIWorld", "midiworld.com", "Bach MIDI database"),
    ]

    for site, url, desc in sources:
        print("15")

    print("\n🔍 Search for: 'Bach organ toccata fugue MIDI'")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Bach Organ Performance Demo")
    parser.add_argument("--quick", action="store_true", help="Run quick test without MIDI file")
    parser.add_argument("--modules", action="store_true", help="Show free module recommendations")
    parser.add_argument("--midi", action="store_true", help="Show Bach MIDI sources")

    args = parser.parse_args()

    if args.modules:
        show_free_module_recommendations()
    elif args.midi:
        show_bach_midi_sources()
    elif args.quick:
        print("Running quick Bach organ test...")
        asyncio.run(quick_bach_test())
    else:
        print("🎵 Running full Bach organ performance demo...")
        print("💡 Tip: Use --quick for testing, --modules for VCV setup, --midi for Bach files")
        asyncio.run(bach_organ_demo())
