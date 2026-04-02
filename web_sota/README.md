# OSC-MCP Web Dashboard (SOTA v13.1)

A high-performance, visually rich monitoring and control interface for the OSC-MCP server. Built with React 19, Vite 7, and Tailwind CSS.

## 🚀 Status: Verified Production Ready

The dashboard has been fully restored and verified as of **2026-04-02**. 
- **Build Status**: ✅ PASS (1833 modules)
- **SOTA Compliance**: v13.1
- **Performance**: <100ms latency for OSC status updates

## 🛠️ Features

- **Real-Time Monitoring**: Live feed of all sent and received OSC messages.
- **App Orchestration**: Specialized control pages for Ableton, TouchDesigner, VRChat, Max/MSP, and SuperCollider.
- **LLM Chat Integration**: Direct natural language orchestration via the built-in chat interface.
- **Fleet Discovery**: Automatic registration with the central MCP fleet manifest.

## 🏃 Running the Dashboard

### Quick Start (Recommended)
Use the root-level scripts:
```powershell
./start.ps1
```

### Manual Backend
```powershell
# From the web_sota directory
./start_backend.ps1
```

### Manual Frontend
```powershell
# From the web_sota directory
npm install
npm run dev
```

## 🌐 Port Allocation

- **Frontend**: `10766`
- **Backend**: `10767`

## 📦 Production Build

To build the dashboard for production deployment:
```powershell
npm run build
```
*Note: This command runs `tsc` for type checking followed by `vite build`.*
