# Arazzo Workflow Engine Integration

This guide covers the integration of the Arazzo specification (v1.0.1) in the `osc-mcp` server for defining and executing complex, multi-step OSC automation sequences.

## 🌟 What is Arazzo?

[Arazzo](https://spec.openapis.org/arazzo/v1.0.1.html) is an OpenAPI specification designed to describe multi-step sequences of API calls (workflows). In the context of `osc-mcp`, Arazzo provides a standardized, machine-readable format for defining:
- Choreographed OSC message sequences.
- Timing, delays, and pacing.
- Conditional logic and dynamic parameter insertion.
- Application-specific initialization routines (e.g., VCV Rack patch setup).

## 🧰 Available Tools

The server provides three primary tools for interacting with Arazzo workflows, alongside an interactive UI component.

### 1. `list_arazzo_workflows`
Returns a JSON dictionary of all discovered Arazzo mission descriptors located in the `src/oscmcp/workflows/` directory.
- **Usage**: Use this to discover available workflow IDs and required parameters.

### 2. `show_available_workflows` (Prefab UI)
Returns an interactive FastMCP `PrefabApp` component rendering a DataTable.
- **Usage**: Ideal for chat clients to visualize the available workflows in a rich UI format.

### 3. `execute_osc_workflow`
Executes a specified workflow by ID, injecting any provided parameters.
- **Usage**: Call this tool with a `workflow_id` and an optional dictionary of `parameters` to trigger the sequence.

### 4. `generate_osc_workflow`
Leverages the native FastMCP context to dynamically generate a one-off workflow sequence to achieve a specific goal based on a natural language prompt.
- **Usage**: Ideal for one-shot complex sequences where authoring a YAML file is unnecessary.

## 📝 Authoring Workflows

Workflows are authored as standard YAML files following the Arazzo 1.0.1 specification and placed in the `src/oscmcp/workflows/` directory.

### Example: VCV Rack Initialization (`vcv-rack-init.yaml`)

```yaml
arazzo: 1.0.1
info:
  title: VCV Rack Initializer
  description: Sets up standard parameters for a new VCV Rack patch
  version: 1.0.0
sourceDescriptions:
  - name: osc_server
    url: http://127.0.0.1:8000
workflows:
  - workflowId: init_patch
    summary: Initialize Patch
    inputs:
      type: object
      properties:
        bpm:
          type: integer
          default: 120
    steps:
      - stepId: set_bpm
        description: Set Clock BPM
        operationId: send_osc_message
        parameters:
          - name: address
            in: body
            value: /clock/bpm
          - name: args
            in: body
            value: [$inputs.bpm]
      - stepId: reset_sequencer
        description: Reset main sequencer
        operationId: send_osc_message
        parameters:
          - name: address
            in: body
            value: /seq/reset
          - name: args
            in: body
            value: [1.0]
```

## 🚀 Execution Flow

When `execute_osc_workflow` is called:
1. The server loads the YAML descriptor.
2. It resolves any `inputs` passed to the tool.
3. It iterates through the `steps` array sequentially.
4. For each step, it executes the target `operationId` (e.g., `send_osc_message`) with the defined parameters.
5. Variables like `$inputs.bpm` are dynamically replaced at runtime.

## 🔍 Best Practices

- **Modularity**: Break down complex tasks into smaller workflows.
- **Documentation**: Provide clear `summary` and `description` fields to help the LLM understand when to use the workflow.
- **Defaults**: Provide sensible default values for `inputs` to make workflows easier to execute without strict parameter requirements.
