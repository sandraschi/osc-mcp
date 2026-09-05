"""OSC-MCP applications module.

This package contains applications that use the OSC-MCP bridge for specific use cases.

Note (2026-09-05): ableton.py, maxmsp.py, puredata.py, resolume.py, supercollider.py,
touchdesigner.py, and vcvrack.py were removed - confirmed via a repo-wide grep that
nothing referenced their classes outside this file's own blanket re-export. The live
`*_manager` MCP tools for all of those apps are implemented directly in
mcp_server.py/server.py with their own inline OSC sends; these were an abandoned
parallel implementation. obs.py, qlab.py, oscquery.py, midibridge.py, and vrchat.py
remain - server.py imports OBSOSC/QLabOSC from here, and dynamic_mapper.py/
midi_tools.py import from oscquery.py/midibridge.py respectively.
"""

from .obs import OBSOSC
from .qlab import QLabOSC
from .vrchat import VRChatOSC

__all__ = [
    "OBSOSC",
    "QLabOSC",
    "VRChatOSC",
]
