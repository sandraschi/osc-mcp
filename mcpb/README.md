# oscmcp (MCPB Bundle)

FastMCP 3.1.0 OSC Server with conversational AI and LLM sampling

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "oscmcp": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos", "python", "-m", "oscmcp"],
      "env": { "PYTHONPATH": "\D:\Dev\repos/src" }
    }
  }
}
\\\

## Tools

- **send_osc**: send_osc
- **start_osc_server**: start_osc_server
- **stop_osc_server**: stop_osc_server
- **get_received_messages**: get_received_messages
- **get_latest_message**: get_latest_message
- **get_osc_server_stats**: get_osc_server_stats
- **clear_osc_message_buffer**: clear_osc_message_buffer
- **test_osc_echo**: test_osc_echo
- **ableton_manager**: ableton_manager
- **vrchat_manager**: vrchat_manager
- **touchdesigner_manager**: touchdesigner_manager
- **vcv_manager**: vcv_manager
- **osc_recorder_manager**: osc_recorder_manager
- **music_loader_manager**: music_loader_manager
- **music_orchestrator**: music_orchestrator
- **supercollider_manager**: supercollider_manager
- **maxmsp_manager**: maxmsp_manager
- **resolume_manager**: resolume_manager
- **audio_workflow_manager**: audio_workflow_manager
- **puredata_manager**: puredata_manager
- **send_osc_message**: send_osc_message
- **start_osc_listener**: start_osc_listener
- **generate_osc_workflow**: generate_osc_workflow
- **execute_osc_workflow**: execute_osc_workflow
- **list_arazzo_workflows**: list_arazzo_workflows
- **main_stdio**: main(stdio)
- **main_http**: main(http)
- **main_sse**: main(sse)
- **health**: health
- **stats**: stats

## Requirements

- Python 3.12+
- uv
