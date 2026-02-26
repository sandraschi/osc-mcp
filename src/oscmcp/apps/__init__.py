"""OSC-MCP applications module.

This package contains applications that use the OSC-MCP bridge for specific use cases.
"""

from .ableton import AbletonLive
from .maxmsp import MaxMSPOSC
from .midibridge import MIDIBridge, MIDIMapping, MIDIType
from .oscquery import OSCQueryBrowser, OSCQueryServer, OSCQueryService
from .puredata import PureDataOSC
from .resolume import ResolumeArena
from .supercollider import SuperColliderOSC
from .touchdesigner import TouchDesignerOSC
from .vcvrack import VCVController
from .vrchat import VRChatOSC

__all__ = [
    "AbletonLive",
    "MIDIBridge",
    "MIDIMapping",
    "MIDIType",
    "MaxMSPOSC",
    "OSCQueryBrowser",
    "OSCQueryServer",
    "OSCQueryService",
    "PureDataOSC",
    "ResolumeArena",
    "SuperColliderOSC",
    "TouchDesignerOSC",
    "VCVController",
    "VRChatOSC",
]
