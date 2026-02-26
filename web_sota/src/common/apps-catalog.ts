import {
    Github,
    Bot,
    Brain,
    LayoutGrid,
    Scan,
    MonitorPlay,
    Box,
    Activity,
    Archive
} from 'lucide-react';

export interface AppEntry {
    id: string;
    label: string;
    description: string;
    icon: any;
    url: string; // Absolute URL for cross-app navigation
    port: number;
    tags: string[];
}

// SOTA App Catalog - Centralized Registry for Fleet Navigation
export const APPS_CATALOG: AppEntry[] = [
    {
        id: 'blender-mcp',
        label: 'Blender Control',
        description: '3D visualization and geometry orchestration.',
        icon: Box,
        url: 'http://localhost:10848',
        port: 10848,
        tags: ['creative', '3d']
    },
    {
        id: 'avatar-mcp',
        label: 'Avatar Control',
        description: 'VRM avatar management and animation orchestration.',
        icon: Bot,
        url: 'http://localhost:10792',
        port: 10792,
        tags: ['creative', 'avatar']
    },
    {
        id: 'alexa-mcp',
        label: 'Alexa Control',
        description: 'Acoustic bridge and voice command orchestration.',
        icon: Activity,
        url: 'http://localhost:10800',
        port: 10800,
        tags: ['control', 'voice']
    },
    {
        id: 'vienna-live-mcp',
        label: 'Vienna Live MCP',
        description: 'Transit and location-aware services in Vienna.',
        icon: LayoutGrid,
        url: 'http://localhost:10878',
        port: 10878,
        tags: ['transit', 'vienna']
    },
    {
        id: 'handbrake-mcp',
        label: 'Handbrake MCP',
        description: 'Automated media transcoding and pipeline management.',
        icon: MonitorPlay,
        url: 'http://localhost:10874',
        port: 10874,
        tags: ['media', 'video']
    },
    {
        id: 'virtualdj-mcp',
        label: 'VirtualDJ MCP',
        description: 'SOTA VJing and audio orchestration.',
        icon: Activity,
        url: 'http://localhost:10876',
        port: 10876,
        tags: ['media', 'audio']
    },
    {
        id: 'openfang',
        label: 'OpenFang',
        description: 'Fleet supervisor and modular agentic node controller.',
        icon: LayoutGrid,
        url: 'http://localhost:10870',
        port: 10870,
        tags: ['infra', 'admin']
    },
    {
        id: 'osc-mcp',
        label: 'OSC Control',
        description: 'Real-time control protocol bridge for high-end gear.',
        icon: Activity,
        url: 'http://localhost:10766',
        port: 10766,
        tags: ['control', 'media']
    },
    {
        id: 'rustdesk-mcp',
        label: 'RustDesk MCP',
        description: 'Secure remote access and fleet management.',
        icon: MonitorPlay,
        url: 'http://localhost:10804',
        port: 10804,
        tags: ['infra', 'remote']
    },
    {
        id: 'vroidstudio-mcp',
        label: 'VroidStudio MCP',
        description: 'Avatar creation and VR character pipeline.',
        icon: Bot,
        url: 'http://localhost:10880',
        port: 10880,
        tags: ['creative', 'avatar']
    },
    {
        id: 'obsidian-mcp',
        label: 'Obsidian MCP',
        description: 'Knowledge graph and second brain integration.',
        icon: Brain,
        url: 'http://localhost:10704',
        port: 10704,
        tags: ['knowledge', 'ai']
    },
    {
        id: 'vrchat-mcp',
        label: 'VRChat Control',
        description: 'Avatar and world orchestration for VRChat.',
        icon: Bot,
        url: 'http://localhost:10712',
        port: 10712,
        tags: ['vr', 'avatar']
    },
    {
        id: 'plex-mcp',
        label: 'Plex Control',
        description: 'Media management and streaming orchestration.',
        icon: MonitorPlay,
        url: 'http://localhost:10741',
        port: 10741,
        tags: ['media', 'streaming']
    },
    {
        id: 'resonite-mcp',
        label: 'Resonite Control',
        description: 'Virtual world and avatar orchestration for Resonite.',
        icon: Box,
        url: 'http://localhost:10714',
        port: 10714,
        tags: ['vr', 'creative']
    },
    {
        id: 'unity3d-mcp',
        label: 'Unity3D Control',
        description: 'Game engine and virtual robotics orchestration.',
        icon: LayoutGrid,
        url: 'http://localhost:10830',
        port: 10830,
        tags: ['dev', 'creative']
    },
    {
        id: 'dark-app-factory',
        label: 'Dark App Factory',
        description: 'SOTA dark mode application generation.',
        icon: LayoutGrid,
        url: 'http://localhost:10738',
        port: 10738,
        tags: ['dev', 'ide']
    },
    {
        id: 'mcp-central-docs',
        label: 'Docs MCP',
        description: 'Standardized MCP documentation and fleet registry.',
        icon: Activity,
        url: 'http://localhost:10720',
        port: 10720,
        tags: ['knowledge', 'admin']
    }
];
