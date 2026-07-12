# 📚 OSC-MCP Documentation Index

Welcome to the central documentation index for **OSC-MCP**, a SOTA Model Context Protocol server enabling natural language orchestration of audio/visual and creative applications via the Open Sound Control (OSC) protocol.

---

## 🎨 OSC Automation & Workflows

Guides on automated workflow descriptors, mappings, and live show control.
* 📄 **[Arazzo Workflows Guide](ARAZZO_WORKFLOWS_GUIDE.md)**: Tutorial on constructing multi-step mission workflows utilizing Arazzo 1.0.1 YAML schemas.
* 📄 **[OBS Studio Integration & Plugin Landscape Guide](OBS_PLUGINS_GUIDE.md)**: Deep dive into OBS Studio control, native C++ plugins vs WebSocket middleware, the SLOBS trademark history, VTuber OSC tracking integrations, and the built-in python WebSocket bridge.
* 📄 **[OSCELOT Mapping Guide](OSCELOT_MAPPING_GUIDE.md)**: Reference guide for mapping complex OSC addresses to dynamic UI widgets.
* 📄 **[OSCELOT Simple Workflow Guide](OSCELOT_SIMPLE_WORKFLOW.md)**: Quick-start configuration examples for standard OSCELOT UI orchestrations.
* 📄 **[OSCELOT UI Mappings Explained](OSCELOT_UI_MAPPING_EXPLAINED.md)**: Detailed conceptual breakdown of UI-to-OSC parameter mappings.

---

## 🎹 Audio/Visual & Module Integrations

Comparing and integrating specific creative target platforms.
* 📄 **[VCV Rack OSC Modules Comparison](VCV_RACK_OSC_MODULES_COMPARISON.md)**: In-depth analysis of VCV Rack modules (VCV Host, Stoermelder, and internal core modules) supporting OSC.
* 📄 **[CV-to-OSC-to-CV Setup Guide](CVOSCCV_SETUP_GUIDE.md)**: Hardware/software routing setup for converting control voltage signals to OSC packets and back.

---

## 🔧 API & Tool Standards

Developer guidelines and references for the FastMCP tool definitions.
* 📄 **[Application Tools Analysis](APPLICATION_TOOLS_ANALYSIS.md)**: Complete breakdown of application-specific manager integrations (Ableton Live, TouchDesigner, VRChat, Resolume, QLab, Max/MSP, etc.).
* 📄 **[Tool Docstring Standards](TOOL_DOCSTRING_STANDARD.md)**: Coding standards, formatting guidelines, and type mappings for FastMCP tool declarations.
* 📄 **[Tool Docstring Migration Checklist](TOOL_DOCSTRING_MIGRATION.md)**: Migration ledger tracking docstring formatting updates across the codebase.

---

## 📊 Project State & Analysis

Architecture assessments and platform alignment checks.
* 📄 **[Project Analysis](PROJECT_ANALYSIS.md)**: SOTA status verification, package bundling checks, and code quality audits.
* 📄 **[Critical Architecture Analysis](CRITICAL_ANALYSIS.md)**: Deep technical review of standard SLIP-framed TCP streams, subnet scanning concurrencies, and transport performance.

---

## 💻 Standard MCP Server Development Guides

Generic documentation for MCP server management located in the subdirectories.
* 📂 **[MCP Technical Hub](mcp-technical/README.md)**: Core folder for standard server configurations.
  * 📄 [Claude Desktop Debugging](mcp-technical/CLAUDE_DESKTOP_DEBUGGING.md)
  * 📄 [MCP Production Readiness Checklist](mcp-technical/MCP_PRODUCTION_CHECKLIST.md)
  * 📄 [FastMCP v2.12 Troubleshooting Guide](mcp-technical/TROUBLESHOOTING_FASTMCP_2.12.md)
* 📂 **[Development Guide Hub](development/README.md)**: Coding guides and troubleshooting logs.
  * 📄 [AI Development Rules & Guidelines](development/AI_DEVELOPMENT_RULES.md)
  * 📄 [AI Development Tools Comparison](development/AI_DEVELOPMENT_TOOLS_COMPARISON.md)
  * 📄 [Debugging Lessons Learned](development/DEBUGGING_LESSONS_LEARNED.md)
  * 📄 [Python Dependency Hell Fix Guide](development/PYTHON_DEPENDENCY_HELL_FIX.md)
  * 📄 [MCP Sync Debugging Guide](development/MCP_SYNC_DEBUGGING_GUIDE.md)
