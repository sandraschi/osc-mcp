#!/usr/bin/env python3
"""
TouchDesigner OSC-MCP Comprehensive Demo

This script demonstrates all the TouchDesigner operations available through
the OSC-MCP TouchDesigner manager tool. Run this while TouchDesigner is running
with OSC enabled (default port 9000).

Make sure TouchDesigner is set up with:
1. OSC In CHOP or OSC In DAT listening on port 9000
2. Operators with matching paths as used in this demo

Usage:
    python touchdesigner_demo.py

Or call individual operations via MCP:
    await touchdesigner_manager("set_waveform_freq", component_path="/project/wave1", frequency=440)
"""

import asyncio

from oscmcp.apps.touchdesigner import TouchDesignerOSC


async def demo_basic_operations(td: TouchDesignerOSC):
    """Demonstrate basic parameter operations."""
    print("🎛️  Testing basic operations...")

    # Basic parameter control
    td.set_constant("/project/const1", 0.5)
    await asyncio.sleep(0.5)

    td.set_slider("/project/slider1", 0.75)
    await asyncio.sleep(0.5)

    td.set_toggle("/project/toggle1", True)
    await asyncio.sleep(0.5)

    td.trigger_button("/project/button1")
    await asyncio.sleep(0.5)

    print("✅ Basic operations completed")


async def demo_chop_operations(td: TouchDesignerOSC):
    """Demonstrate CHOP (Channel Operator) operations."""
    print("🎵 Testing CHOP operations...")

    # Waveform control
    td.set_waveform_freq("/project/waveform1", 440.0)  # A4 note
    await asyncio.sleep(0.5)

    td.set_waveform_amp("/project/waveform1", 0.8)
    await asyncio.sleep(0.5)

    td.set_waveform_phase("/project/waveform1", 0.0)
    await asyncio.sleep(0.5)

    # Audio control
    td.set_audio_level("/project/audioin1", 0.7)
    await asyncio.sleep(0.5)

    # Filter control
    td.set_filter_cutoff("/project/filter1", 1000.0)
    await asyncio.sleep(0.5)

    # Math operations
    td.set_math_multiply("/project/math1", 2.0)
    await asyncio.sleep(0.5)

    # LFO control
    td.set_lfo_rate("/project/lfo1", 0.5)
    await asyncio.sleep(0.5)

    # Channel operations
    td.set_chop_channel("/project/chop1", 0, 0.8)  # Channel 0
    td.set_chop_channel_by_name("/project/chop1", "chan1", 0.6)  # Named channel

    print("✅ CHOP operations completed")


async def demo_top_operations(td: TouchDesignerOSC):
    """Demonstrate TOP (Texture Operator) operations."""
    print("🎬 Testing TOP operations...")

    # Movie playback control
    td.set_movie_play("/project/movie1", True)
    await asyncio.sleep(1.0)
    td.set_movie_play("/project/movie1", False)
    await asyncio.sleep(0.5)

    # Level adjustments
    td.set_level_brightness("/project/level1", 1.2)
    await asyncio.sleep(0.5)

    td.set_level_contrast("/project/level1", 1.1)
    await asyncio.sleep(0.5)

    td.set_level_gamma("/project/level1", 0.9)
    await asyncio.sleep(0.5)

    # Transform operations
    td.set_transform_scale("/project/transform1", 1.5, 1.5, 1.0)
    await asyncio.sleep(0.5)

    td.set_transform_rotate("/project/transform1", 45.0, 0.0, 0.0)
    await asyncio.sleep(0.5)

    td.set_transform_translate("/project/transform1", 100.0, 50.0, 0.0)
    await asyncio.sleep(0.5)

    # Composite operations
    td.set_composite_opacity("/project/composite1", 0.7)

    print("✅ TOP operations completed")


async def demo_sop_operations(td: TouchDesignerOSC):
    """Demonstrate SOP (Surface Operator) operations."""
    print("🔺 Testing SOP operations...")

    # Primitive geometry
    td.set_sphere_radius("/project/sphere1", 0.8)
    await asyncio.sleep(0.5)

    td.set_box_size("/project/box1", 2.0, 1.5, 1.0)
    await asyncio.sleep(0.5)

    td.set_torus_major("/project/torus1", 1.0)
    td.set_torus_minor("/project/torus1", 0.3)
    await asyncio.sleep(0.5)

    # Transform operations
    td.set_transform_sop_tx("/project/transform_sop1", 100.0)
    await asyncio.sleep(0.5)

    td.set_transform_sop_ty("/project/transform_sop1", 50.0)
    await asyncio.sleep(0.5)

    td.set_transform_sop_tz("/project/transform_sop1", 25.0)
    await asyncio.sleep(0.5)

    # Rotations
    td.set_transform_sop_rx("/project/transform_sop1", 45.0)
    await asyncio.sleep(0.5)

    td.set_transform_sop_ry("/project/transform_sop1", 30.0)
    await asyncio.sleep(0.5)

    td.set_transform_sop_rz("/project/transform_sop1", 15.0)

    print("✅ SOP operations completed")


async def demo_dat_operations(td: TouchDesignerOSC):
    """Demonstrate DAT (Data Operator) operations."""
    print("📊 Testing DAT operations...")

    # Table operations
    td.set_table_cell("/project/table1", 0, 0, "Name")
    td.set_table_cell("/project/table1", 0, 1, "Value")
    await asyncio.sleep(0.5)

    td.set_table_cell("/project/table1", 1, 0, "Frequency")
    td.set_table_cell("/project/table1", 1, 1, 440.0)
    await asyncio.sleep(0.5)

    # Text operations
    td.set_text_string("/project/text1", "Hello from OSC-MCP!")
    await asyncio.sleep(0.5)

    # Script triggering
    td.trigger_script("/project/script1")
    await asyncio.sleep(0.5)

    # Parameter DAT
    td.set_parameter_dat("/project/param1", "value", 0.75)

    print("✅ DAT operations completed")


async def demo_mat_operations(td: TouchDesignerOSC):
    """Demonstrate MAT (Material Operator) operations."""
    print("✨ Testing MAT operations...")

    # Phong material properties
    td.set_phong_diffuse("/project/phong1", 1.0, 0.5, 0.0)  # Orange
    await asyncio.sleep(0.5)

    td.set_phong_specular("/project/phong1", 1.0, 1.0, 1.0)  # White specular
    await asyncio.sleep(0.5)

    td.set_phong_emissive("/project/phong1", 0.1, 0.1, 0.1)  # Slight glow
    await asyncio.sleep(0.5)

    td.set_phong_shininess("/project/phong1", 0.8)

    print("✅ MAT operations completed")


async def demo_comp_operations(td: TouchDesignerOSC):
    """Demonstrate COMP (Component) operations."""
    print("🖼️  Testing COMP operations...")

    # Container operations
    td.set_container_opacity("/project/container1", 0.8)
    await asyncio.sleep(0.5)

    # Base component operations
    td.set_base_position("/project/base1", 150.0, 100.0)
    await asyncio.sleep(0.5)

    td.set_base_size("/project/base1", 400.0, 300.0)
    await asyncio.sleep(0.5)

    # Window operations
    td.set_window_position("/project/window1", 200.0, 150.0)

    print("✅ COMP operations completed")


async def demo_animated_sequence(td: TouchDesignerOSC):
    """Demonstrate an animated sequence combining multiple operator types."""
    print("🎭 Running animated sequence...")

    # Create a rhythmic animation
    for i in range(10):
        # Audio modulation
        td.set_waveform_freq("/project/waveform1", 220 + i * 44)  # Rising pitch
        td.set_waveform_amp("/project/waveform1", 0.5 + 0.05 * i)  # Rising volume

        # Visual modulation
        td.set_level_brightness("/project/level1", 0.8 + 0.04 * i)
        td.set_transform_scale("/project/transform1", 1.0 + 0.1 * i, 1.0 + 0.1 * i)

        # 3D animation
        td.set_transform_sop_ry("/project/transform_sop1", i * 36)  # Full rotation

        # Material animation
        hue = i / 10.0  # Cycle through hues
        td.set_phong_diffuse("/project/phong1", hue, 1.0 - hue, 0.5)

        await asyncio.sleep(0.2)

    print("✅ Animated sequence completed")


async def main():
    """Main demo function."""
    print("🎨 TouchDesigner OSC-MCP Comprehensive Demo")
    print("=" * 50)
    print("Make sure TouchDesigner is running with OSC enabled on port 9000")
    print("Create operators with paths matching the demo calls")
    print()

    # Create TouchDesigner OSC interface
    td = TouchDesignerOSC(host="127.0.0.1", listen_port=9000, target_port=9000)

    try:
        # Start the OSC interface
        await td.start()
        print("🔗 OSC interface started - listening on port 9000")

        print("\n🚀 Starting demo sequence...")
        print("Each demo will run for a few seconds with delays between operations")
        print("Watch TouchDesigner for visual feedback!\n")

        # Run all demos
        await demo_basic_operations(td)
        await asyncio.sleep(1)

        await demo_chop_operations(td)
        await asyncio.sleep(1)

        await demo_top_operations(td)
        await asyncio.sleep(1)

        await demo_sop_operations(td)
        await asyncio.sleep(1)

        await demo_dat_operations(td)
        await asyncio.sleep(1)

        await demo_mat_operations(td)
        await asyncio.sleep(1)

        await demo_comp_operations(td)
        await asyncio.sleep(1)

        await demo_animated_sequence(td)

        print("\n🎉 Demo completed successfully!")
        print("All TouchDesigner operations have been tested.")
        print("Check your TouchDesigner network for the results.")

    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
    finally:
        await td.stop()
        print("🔌 OSC interface stopped")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
