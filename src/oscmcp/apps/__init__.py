"""OSC-MCP applications module.

This package contains applications that use the OSC-MCP bridge for specific use cases.
"""

from .ableton import AbletonLive
from .maxmsp import MaxMSPOSC
from .midibridge import MIDIBridge, MIDIMapping, MIDIType
from .obs import OBSOSC
from .oscquery import OSCQueryBrowser, OSCQueryServer, OSCQueryService
from .puredata import PureDataOSC
from .qlab import QLabOSC
from .resolume import ResolumeArena
from .supercollider import SuperColliderOSC
from .touchdesigner import TouchDesignerOSC
from .vcvrack import VCVController
from .vrchat import VRChatOSC

__all__ = [
    "OBSOSC",
    "AbletonLive",
    "MIDIBridge",
    "MIDIMapping",
    "MIDIType",
    "MaxMSPOSC",
    "OSCQueryBrowser",
    "OSCQueryServer",
    "OSCQueryService",
    "PureDataOSC",
    "QLabOSC",
    "ResolumeArena",
    "SuperColliderOSC",
    "TouchDesignerOSC",
    "VCVController",
    "VRChatOSC",
]
