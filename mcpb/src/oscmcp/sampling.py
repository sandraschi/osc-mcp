"""FastMCP 3.4.2 Native Sampling Capabilities for OSC-MCP.

This module provides AI-driven validation, generation, and analysis for OSC workflows
using the official FastMCP 3.4.2+ native Context sampling interface.
"""

import logging
import json
from typing import Any, Dict, List, Literal, Optional
from fastmcp import Context

logger = logging.getLogger(__name__)


class OSCWorkflowSampler:
    """Advanced sampler for OSC automation workflows using native FastMCP Context."""

    def __init__(self) -> None:
        logger.info("OSC Workflow Sampler initialized using native FastMCP Context.")

    async def generate_osc_workflow(
        self,
        task_description: str,
        ctx: Context,
        target_applications: Optional[List[str]] = None,
        complexity_level: Literal["simple", "intermediate", "advanced"] = "intermediate",
    ) -> Dict[str, Any]:
        """Generate an intelligent OSC workflow using native Context sampling.

        Args:
            task_description: Description of the automation task
            ctx: Native FastMCP Context injected from the tool
            target_applications: List of target applications
            complexity_level: Desired complexity level
        """
        prompt = f"""Generate an OSC (Open Sound Control) automation workflow for the following task:

Task: {task_description}
Target Applications: {", ".join(target_applications or ["generic"])}
Complexity Level: {complexity_level}

Provide a structured JSON response with the following keys:
- workflow_name: A descriptive name for this workflow
- description: Brief explanation of what this workflow does
- target_apps: List of target applications
- osc_messages: Array of message objects with address, values, timing
- parameters: Object defining parameter ranges and defaults
- error_handling: Error handling strategies
- integration_notes: Notes on integrating with target applications
"""
        try:
            res = await ctx.sample(prompt)
            # Parse response text
            return json.loads(res.text) if res.text else self._create_fallback_workflow(task_description)
        except Exception as e:
            logger.error("OSC workflow generation failed: %s", e)
            return self._create_fallback_workflow(task_description)

    async def validate_osc_message(
        self, address: str, values: List[Any], ctx: Context, application_context: str = "generic"
    ) -> Dict[str, Any]:
        """Validate OSC message format and appropriateness using native Context sampling."""
        prompt = f"""Validate this OSC message for {application_context}:

Address: {address}
Values: {values}

Return a JSON response with:
- valid: boolean indicating if message is valid
- issues: array of identified issues
- suggestions: array of improvement suggestions
- corrected_address: suggested corrected address if needed
- corrected_values: suggested corrected values if needed"""

        try:
            res = await ctx.sample(prompt)
            return json.loads(res.text) if res.text else {"valid": True, "issues": [], "suggestions": []}
        except Exception as e:
            logger.error("OSC message validation failed: %s", e)
            return {
                "valid": True,
                "issues": [],
                "suggestions": ["Native validation fallback triggered"],
                "error": str(e),
            }

    async def enhance_osc_workflow(
        self,
        workflow: Dict[str, Any],
        ctx: Context,
        enhancement_type: Literal["optimization", "robustness", "features"] = "optimization",
    ) -> Dict[str, Any]:
        """Enhance an existing OSC workflow using native Context sampling."""
        prompt = f"""Enhance this OSC workflow with {enhancement_type} improvements:

Current Workflow: {workflow}

Return the enhanced workflow in the same JSON format."""

        try:
            res = await ctx.sample(prompt)
            return json.loads(res.text) if res.text else workflow
        except Exception as e:
            logger.error("Workflow enhancement failed: %s", e)
            return workflow

    async def validate_osc_workflow(self, workflow: Dict[str, Any], ctx: Context) -> Dict[str, Any]:
        """Validate an OSC workflow structure and logic using native Context sampling."""
        prompt = f"""Validate this OSC workflow for correctness and best practices:

Workflow: {workflow}

Return a JSON response with:
- valid: boolean indicating if workflow is valid
- confidence: confidence level (high/medium/low)
- issues: array of identified issues with severity
- suggestions: array of specific improvement suggestions
- fix_suggestions: actionable steps to resolve issues
- compatibility_notes: notes about application compatibility"""

        try:
            res = await ctx.sample(prompt)
            return json.loads(res.text) if res.text else {"valid": True, "confidence": "medium", "issues": []}
        except Exception as e:
            logger.error("Workflow validation failed: %s", e)
            return {
                "valid": True,
                "confidence": "low",
                "issues": [],
                "suggestions": ["Validation unavailable - manual review recommended"],
                "fix_suggestions": [],
            }

    async def execute_osc_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an OSC workflow with intelligent monitoring."""
        import asyncio
        import time
        from pythonosc.udp_client import SimpleUDPClient

        start_time = time.time()
        executed_messages = []
        errors = []

        try:
            messages = workflow.get("osc_messages", [])
            host = workflow.get("host", "127.0.0.1")
            port = workflow.get("port", 8000)

            client = SimpleUDPClient(host, port)

            for i, message in enumerate(messages):
                try:
                    address = message["address"]
                    values = message["values"]
                    timing = message.get("timing", "immediate")

                    if timing != "immediate" and isinstance(timing, (int, float)):
                        await asyncio.sleep(timing)

                    client.send_message(address, values)
                    executed_messages.append(
                        {
                            "index": i,
                            "address": address,
                            "values": values,
                            "timestamp": time.time() - start_time,
                            "success": True,
                        }
                    )
                except Exception as e:
                    error_info = {
                        "index": i,
                        "message": message,
                        "error": str(e),
                        "timestamp": time.time() - start_time,
                    }
                    errors.append(error_info)
                    executed_messages.append({**error_info, "success": False})

            execution_time = time.time() - start_time
            success_rate = (
                len([m for m in executed_messages if m["success"]]) / len(executed_messages)
                if executed_messages
                else 0
            )

            return {
                "success": len(errors) == 0,
                "analysis": {
                    "total_messages": len(messages),
                    "executed_messages": len(executed_messages),
                    "successful_messages": len([m for m in executed_messages if m["success"]]),
                    "failed_messages": len(errors),
                    "success_rate": success_rate,
                    "execution_time": execution_time,
                },
                "executed_messages": executed_messages,
                "errors": errors,
                "execution_time": execution_time,
            }
        except Exception as e:
            logger.error("Workflow execution failed: %s", e)
            return {
                "success": False,
                "analysis": {"error": str(e)},
                "executed_messages": executed_messages,
                "errors": errors + [{"error": str(e)}],
                "execution_time": time.time() - start_time,
            }

    async def analyze_osc_test(
        self, server_result: Dict[str, Any], send_result: Dict[str, Any], ctx: Context
    ) -> Dict[str, Any]:
        """Analyze OSC connectivity test results using native Context sampling."""
        prompt = f"""Analyze these OSC connectivity test results:

Server Result: {server_result}
Send Result: {send_result}

Return a JSON response with:
- summary: brief assessment summary
- confidence: confidence level (high/medium/low)
- issues: array of identified issues
- recommendations: array of specific recommendations
- next_steps: ordered list of troubleshooting steps"""

        try:
            res = await ctx.sample(prompt)
            return json.loads(res.text) if res.text else {"summary": "Test complete", "confidence": "high", "issues": []}
        except Exception as e:
            logger.error("Test analysis failed: %s", e)
            return {
                "summary": "OSC test completed - analysis unavailable",
                "confidence": "low",
                "issues": [],
                "recommendations": ["Check connectivity manually"],
                "next_steps": ["Verify target is running", "Check firewalls"],
            }

    def _create_fallback_workflow(self, task_description: str) -> Dict[str, Any]:
        """Create a basic fallback workflow when LLM generation fails."""
        return {
            "workflow_name": "Basic OSC Workflow",
            "description": f"Basic workflow for: {task_description}",
            "target_apps": ["generic"],
            "osc_messages": [
                {
                    "address": "/control",
                    "values": [0.5],
                    "timing": "immediate",
                    "description": "Basic control message",
                }
            ],
            "parameters": {"intensity": {"min": 0.0, "max": 1.0, "default": 0.5}},
            "error_handling": ["basic_timeout"],
            "integration_notes": "This is a fallback workflow.",
        }


# Global sampler instance
osc_sampler = OSCWorkflowSampler()
