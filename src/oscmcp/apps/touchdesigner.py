"""TouchDesigner integration for OSC-MCP.

This module provides integration with TouchDesigner's OSC protocol, enabling
bidirectional communication for interactive media and visual programming.
"""

import logging
from collections.abc import Callable
from typing import Any

from ..osc.client import OSCClient
from ..osc.server import OSCServer

logger = logging.getLogger(__name__)


class TouchDesignerOSC:
    """Main class for TouchDesigner OSC integration.

    Handles both sending and receiving OSC messages to/from TouchDesigner.
    """

    DEFAULT_PORT = 10000  # Default TouchDesigner OSC port

    def __init__(
        self,
        host: str = "127.0.0.1",
        listen_port: int = DEFAULT_PORT,
        target_port: int = DEFAULT_PORT,
    ):
        """Initialize the TouchDesigner OSC interface.

        Args:
            host: Host where TouchDesigner is running
            listen_port: Port to receive OSC messages from TouchDesigner
            target_port: Port to send OSC messages to TouchDesigner
        """
        self.host = host
        self.listen_port = listen_port
        self.target_port = target_port

        # OSC client for sending to TouchDesigner
        self.client = OSCClient(host, target_port)

        # OSC server for receiving from TouchDesigner
        self.server = OSCServer(host, listen_port)

        # Callback storage
        self.callbacks: dict[str, list[Callable[[str, Any], None]]] = {}

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default OSC message handlers."""
        # Default handler for all messages
        self.server.dispatcher.set_default_handler(self._handle_message)

    async def start(self) -> None:
        """Start the OSC server to receive messages from TouchDesigner."""
        await self.server.start()
        logger.info(
            f"TouchDesigner OSC interface started. Listening on port {self.listen_port}, sending to port {self.target_port}"
        )

    async def stop(self) -> None:
        """Stop the OSC server."""
        await self.server.stop()
        logger.info("TouchDesigner OSC interface stopped")

    def _handle_message(self, address: str, *args) -> None:
        """Handle incoming OSC messages.

        Args:
            address: OSC address pattern
            *args: Message arguments
        """
        # Remove any trailing slashes for consistency
        address = address.rstrip("/")

        # Log the message
        logger.debug(f"Received OSC message: {address} {args}")

        # Call registered callbacks
        self._trigger_callbacks(address, args)

        # Also trigger callbacks for parent paths
        parts = address.split("/")
        for i in range(1, len(parts)):
            parent_path = "/".join(parts[: i + 1])
            self._trigger_callbacks(parent_path, args)

    def _trigger_callbacks(self, address: str, args: tuple) -> None:
        """Trigger callbacks for a specific address.

        Args:
            address: OSC address pattern
            args: Message arguments
        """
        if address in self.callbacks:
            for callback in self.callbacks[address]:
                try:
                    callback(address, args[0] if len(args) == 1 else args)
                except Exception as e:
                    logger.error(f"Error in callback for '{address}': {e}")

    def on_message(self, address: str, callback: Callable[[str, Any], None]) -> None:
        """Register a callback for messages to a specific address.

        Args:
            address: OSC address pattern to listen to
            callback: Function that takes (address, value) as arguments
        """
        # Ensure address starts with a slash
        if not address.startswith("/"):
            address = "/" + address

        if address not in self.callbacks:
            self.callbacks[address] = []

        self.callbacks[address].append(callback)

    def send(self, address: str, *args) -> None:
        """Send an OSC message to TouchDesigner.

        Args:
            address: OSC address pattern
            *args: Values to send (will be converted to appropriate OSC types)
        """
        # Ensure address starts with a slash
        if not address.startswith("/"):
            address = "/" + address

        self.client.send(address, *args)
        logger.debug(f"Sent OSC message: {address} {args}")

    # Common TouchDesigner operations

    def set_parameter(self, component_path: str, parameter: str, value: Any) -> None:
        """Set a parameter value in TouchDesigner.

        Args:
            component_path: Path to the component (e.g., '/project1/constant1')
            parameter: Parameter name (e.g., 'value1')
            value: New value for the parameter
        """
        address = f"{component_path}/{parameter}"
        self.send(address, value)

    def pulse(self, component_path: str, pulse_name: str = "pulse") -> None:
        """Trigger a pulse parameter in TouchDesigner.

        Args:
            component_path: Path to the component (e.g., '/project1/button1')
            pulse_name: Name of the pulse parameter (default: 'pulse')
        """
        self.set_parameter(component_path, pulse_name, 1)

    def get_channel(self, channel_path: str) -> None:
        """Request a channel value from TouchDesigner.

        Args:
            channel_path: Path to the channel (e.g., '/project1/chop1/chan1')
        """
        self.send(channel_path)

    # Convenience methods for common components

    def set_constant(self, component_path: str, value: Any) -> None:
        """Set the value of a constant component.

        Args:
            component_path: Path to the constant component
            value: New value for the constant
        """
        self.set_parameter(component_path, "value1", value)

    def set_slider(self, component_path: str, value: float) -> None:
        """Set the value of a slider component.

        Args:
            component_path: Path to the slider component
            value: New value for the slider
        """
        self.set_parameter(component_path, "value", value)

    def set_toggle(self, component_path: str, value: bool) -> None:
        """Set the state of a toggle component.

        Args:
            component_path: Path to the toggle component
            value: New state for the toggle
        """
        self.set_parameter(component_path, "value", 1 if value else 0)

    def trigger_button(self, component_path: str) -> None:
        """Trigger a button component.

        Args:
            component_path: Path to the button component
        """
        self.pulse(component_path)

    def pulse_momentary(self, component_path: str) -> None:
        """Pulse a momentary button component.

        Args:
            component_path: Path to the momentary button component
        """
        self.pulse(component_path)

    # CHOP Operations (Channel Operators)

    def set_chop_channel(self, component_path: str, channel_index: int, value: float) -> None:
        """Set a CHOP channel value by index.

        Args:
            component_path: Path to the CHOP
            channel_index: Channel index (0-based)
            value: New value for the channel
        """
        self.send(f"{component_path}/chan{channel_index}", value)

    def set_chop_channel_by_name(self, component_path: str, channel_name: str, value: float) -> None:
        """Set a CHOP channel value by name.

        Args:
            component_path: Path to the CHOP
            channel_name: Channel name
            value: New value for the channel
        """
        self.send(f"{component_path}/{channel_name}", value)

    def set_waveform_freq(self, component_path: str, frequency: float) -> None:
        """Set waveform CHOP frequency.

        Args:
            component_path: Path to the waveform CHOP
            frequency: Frequency in Hz
        """
        self.set_parameter(component_path, "frequency", frequency)

    def set_waveform_amp(self, component_path: str, amplitude: float) -> None:
        """Set waveform CHOP amplitude.

        Args:
            component_path: Path to the waveform CHOP
            amplitude: Amplitude value
        """
        self.set_parameter(component_path, "amplitude", amplitude)

    def set_waveform_phase(self, component_path: str, phase: float) -> None:
        """Set waveform CHOP phase.

        Args:
            component_path: Path to the waveform CHOP
            phase: Phase value (0-1)
        """
        self.set_parameter(component_path, "phase", phase)

    def set_audio_level(self, component_path: str, level: float) -> None:
        """Set audio device CHOP level.

        Args:
            component_path: Path to the audio device CHOP
            level: Audio level (0.0-1.0)
        """
        self.set_parameter(component_path, "level", level)

    def set_filter_cutoff(self, component_path: str, cutoff: float) -> None:
        """Set filter CHOP cutoff frequency.

        Args:
            component_path: Path to the filter CHOP
            cutoff: Cutoff frequency in Hz
        """
        self.set_parameter(component_path, "cutoff", cutoff)

    def set_math_multiply(self, component_path: str, multiplier: float) -> None:
        """Set math CHOP multiply value.

        Args:
            component_path: Path to the math CHOP
            multiplier: Multiply value
        """
        self.set_parameter(component_path, "multiply", multiplier)

    def set_lfo_rate(self, component_path: str, rate: float) -> None:
        """Set LFO CHOP rate.

        Args:
            component_path: Path to the LFO CHOP
            rate: LFO rate (Hz)
        """
        self.set_parameter(component_path, "rate", rate)

    # TOP Operations (Texture Operators)

    def set_movie_play(self, component_path: str, play: bool) -> None:
        """Control movie file TOP playback.

        Args:
            component_path: Path to the movie file TOP
            play: True to play, False to pause
        """
        self.set_parameter(component_path, "play", 1 if play else 0)

    def set_level_brightness(self, component_path: str, brightness: float) -> None:
        """Set level TOP brightness.

        Args:
            component_path: Path to the level TOP
            brightness: Brightness value
        """
        self.set_parameter(component_path, "brightness", brightness)

    def set_level_contrast(self, component_path: str, contrast: float) -> None:
        """Set level TOP contrast.

        Args:
            component_path: Path to the level TOP
            contrast: Contrast value
        """
        self.set_parameter(component_path, "contrast", contrast)

    def set_level_gamma(self, component_path: str, gamma: float) -> None:
        """Set level TOP gamma.

        Args:
            component_path: Path to the level TOP
            gamma: Gamma value
        """
        self.set_parameter(component_path, "gamma", gamma)

    def set_transform_scale(
        self, component_path: str, x: float | None = None, y: float | None = None, z: float | None = None
    ) -> None:
        """Set transform TOP scale.

        Args:
            component_path: Path to the transform TOP
            x: Scale X value
            y: Scale Y value
            z: Scale Z value (for 3D transforms)
        """
        values = []
        if x is not None:
            values.append(x)
        if y is not None:
            values.append(y)
        if z is not None:
            values.append(z)
        if values:
            self.send(f"{component_path}/scale", *values)

    def set_transform_rotate(
        self, component_path: str, x: float | None = None, y: float | None = None, z: float | None = None
    ) -> None:
        """Set transform TOP rotation.

        Args:
            component_path: Path to the transform TOP
            x: Rotate X value (degrees)
            y: Rotate Y value (degrees)
            z: Rotate Z value (degrees)
        """
        values = []
        if x is not None:
            values.append(x)
        if y is not None:
            values.append(y)
        if z is not None:
            values.append(z)
        if values:
            self.send(f"{component_path}/rotate", *values)

    def set_transform_translate(
        self, component_path: str, x: float | None = None, y: float | None = None, z: float | None = None
    ) -> None:
        """Set transform TOP translation.

        Args:
            component_path: Path to the transform TOP
            x: Translate X value
            y: Translate Y value
            z: Translate Z value
        """
        values = []
        if x is not None:
            values.append(x)
        if y is not None:
            values.append(y)
        if z is not None:
            values.append(z)
        if values:
            self.send(f"{component_path}/translate", *values)

    def set_composite_opacity(self, component_path: str, opacity: float) -> None:
        """Set composite TOP opacity.

        Args:
            component_path: Path to the composite TOP
            opacity: Opacity value (0.0-1.0)
        """
        self.set_parameter(component_path, "opacity", opacity)

    # SOP Operations (Surface Operators)

    def set_sphere_radius(self, component_path: str, radius: float) -> None:
        """Set sphere SOP radius.

        Args:
            component_path: Path to the sphere SOP
            radius: Radius value
        """
        self.set_parameter(component_path, "radius", radius)

    def set_box_size(
        self, component_path: str, x: float | None = None, y: float | None = None, z: float | None = None
    ) -> None:
        """Set box SOP size.

        Args:
            component_path: Path to the box SOP
            x: Size X value
            y: Size Y value
            z: Size Z value
        """
        values = []
        if x is not None:
            values.append(x)
        if y is not None:
            values.append(y)
        if z is not None:
            values.append(z)
        if values:
            self.send(f"{component_path}/size", *values)

    def set_torus_major(self, component_path: str, radius: float) -> None:
        """Set torus SOP major radius.

        Args:
            component_path: Path to the torus SOP
            radius: Major radius value
        """
        self.set_parameter(component_path, "majorradius", radius)

    def set_torus_minor(self, component_path: str, radius: float) -> None:
        """Set torus SOP minor radius.

        Args:
            component_path: Path to the torus SOP
            radius: Minor radius value
        """
        self.set_parameter(component_path, "minorradius", radius)

    def set_transform_sop_tx(self, component_path: str, value: float) -> None:
        """Set SOP transform translate X.

        Args:
            component_path: Path to the transform SOP
            value: Translate X value
        """
        self.set_parameter(component_path, "tx", value)

    def set_transform_sop_ty(self, component_path: str, value: float) -> None:
        """Set SOP transform translate Y.

        Args:
            component_path: Path to the transform SOP
            value: Translate Y value
        """
        self.set_parameter(component_path, "ty", value)

    def set_transform_sop_tz(self, component_path: str, value: float) -> None:
        """Set SOP transform translate Z.

        Args:
            component_path: Path to the transform SOP
            value: Translate Z value
        """
        self.set_parameter(component_path, "tz", value)

    def set_transform_sop_rx(self, component_path: str, value: float) -> None:
        """Set SOP transform rotate X.

        Args:
            component_path: Path to the transform SOP
            value: Rotate X value (degrees)
        """
        self.set_parameter(component_path, "rx", value)

    def set_transform_sop_ry(self, component_path: str, value: float) -> None:
        """Set SOP transform rotate Y.

        Args:
            component_path: Path to the transform SOP
            value: Rotate Y value (degrees)
        """
        self.set_parameter(component_path, "ry", value)

    def set_transform_sop_rz(self, component_path: str, value: float) -> None:
        """Set SOP transform rotate Z.

        Args:
            component_path: Path to the transform SOP
            value: Rotate Z value (degrees)
        """
        self.set_parameter(component_path, "rz", value)

    # DAT Operations (Data Operators)

    def set_table_cell(self, component_path: str, row: int, col: int, value: Any) -> None:
        """Set table DAT cell value.

        Args:
            component_path: Path to the table DAT
            row: Row index
            col: Column index
            value: Cell value
        """
        self.send(f"{component_path}/cell/{row}/{col}", value)

    def set_text_string(self, component_path: str, text: str) -> None:
        """Set text DAT string.

        Args:
            component_path: Path to the text DAT
            text: Text content
        """
        self.set_parameter(component_path, "text", text)

    def trigger_script(self, component_path: str) -> None:
        """Execute script DAT.

        Args:
            component_path: Path to the script DAT
        """
        self.pulse(component_path)

    def set_parameter_dat(self, component_path: str, parameter: str, value: Any) -> None:
        """Set parameter DAT value.

        Args:
            component_path: Path to the parameter DAT
            parameter: Parameter name
            value: Parameter value
        """
        self.set_parameter(component_path, parameter, value)

    # MAT Operations (Material Operators)

    def set_phong_diffuse(self, component_path: str, r: float, g: float, b: float) -> None:
        """Set phong MAT diffuse color.

        Args:
            component_path: Path to the phong MAT
            r: Red component (0.0-1.0)
            g: Green component (0.0-1.0)
            b: Blue component (0.0-1.0)
        """
        self.send(f"{component_path}/diffusecolor", r, g, b)

    def set_phong_specular(self, component_path: str, r: float, g: float, b: float) -> None:
        """Set phong MAT specular color.

        Args:
            component_path: Path to the phong MAT
            r: Red component (0.0-1.0)
            g: Green component (0.0-1.0)
            b: Blue component (0.0-1.0)
        """
        self.send(f"{component_path}/specularcolor", r, g, b)

    def set_phong_emissive(self, component_path: str, r: float, g: float, b: float) -> None:
        """Set phong MAT emissive color.

        Args:
            component_path: Path to the phong MAT
            r: Red component (0.0-1.0)
            g: Green component (0.0-1.0)
            b: Blue component (0.0-1.0)
        """
        self.send(f"{component_path}/emissivecolor", r, g, b)

    def set_phong_shininess(self, component_path: str, shininess: float) -> None:
        """Set phong MAT shininess.

        Args:
            component_path: Path to the phong MAT
            shininess: Shininess value
        """
        self.set_parameter(component_path, "shininess", shininess)

    # COMP Operations (Components)

    def set_container_opacity(self, component_path: str, opacity: float) -> None:
        """Set container COMP opacity.

        Args:
            component_path: Path to the container COMP
            opacity: Opacity value (0.0-1.0)
        """
        self.set_parameter(component_path, "opacity", opacity)

    def set_base_position(self, component_path: str, x: float, y: float) -> None:
        """Set base COMP position.

        Args:
            component_path: Path to the base COMP
            x: X position
            y: Y position
        """
        self.send(f"{component_path}/position", x, y)

    def set_base_size(self, component_path: str, width: float, height: float) -> None:
        """Set base COMP size.

        Args:
            component_path: Path to the base COMP
            width: Component width
            height: Component height
        """
        self.send(f"{component_path}/size", width, height)

    def set_window_position(self, component_path: str, x: float, y: float) -> None:
        """Set window COMP position.

        Args:
            component_path: Path to the window COMP
            x: Window X position
            y: Window Y position
        """
        self.send(f"{component_path}/winpos", x, y)


# Example usage
async def example_usage():
    """Example of using the TouchDesignerOSC class."""
    import asyncio

    # Create TouchDesigner OSC interface
    td = TouchDesignerOSC()

    # Define callbacks
    def on_parameter_changed(address, value):
        logger.info(f"Parameter '{address}' changed to: {value}")

    # Register callbacks
    td.on_message("/project1/constant1", on_parameter_changed)

    try:
        # Start the OSC server
        await td.start()

        # Main loop
        while True:
            # Example: Send some test parameters
            td.set_constant("/project1/constant1", 0.5)
            td.trigger_button("/project1/button1")

            # Wait for a bit
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        await td.stop()


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
