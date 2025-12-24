"""OSC-MCP applications module.

This package contains applications that use the OSC-MCP bridge for specific use cases.
"""

from .ableton import AbletonLive
from .vrchat import VRChatOSC
from .touchdesigner import TouchDesignerOSC
from .vcvrack import VCVController
from .resolume import ResolumeArena
from .puredata import PureDataOSC
from .supercollider import SuperColliderOSC
from .maxmsp import MaxMSPOSC
from .oscquery import OSCQueryService, OSCQueryBrowser, OSCQueryServer
from .midibridge import MIDIBridge, MIDIType, MIDIMapping

__all__ = [
    "AbletonLive",
    "VRChatOSC",
    "TouchDesignerOSC",
    "VCVController",
    "ResolumeArena",
    "PureDataOSC",
    "SuperColliderOSC",
    "MaxMSPOSC",
    "OSCQueryService",
    "OSCQueryBrowser",
    "OSCQueryServer",
    "MIDIBridge",
    "MIDIType",
    "MIDIMapping",
]
