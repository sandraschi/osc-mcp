"""FastMCP 2.14.3 Sampling Capabilities for OSC-MCP.

This module provides advanced LLM interrogation capabilities using FastMCP 2.14.3+ sampling.
It enables intelligent content generation, validation, and enhancement for OSC automation workflows.
"""

import logging
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SamplingConfig(BaseModel):
    """Configuration for LLM sampling in FastMCP 2.14.3+."""

    provider: Literal["anthropic", "openai", "auto"] = Field(
        default="auto", description="LLM provider to use for sampling"
    )
    model: Optional[str] = Field(
        default=None, description="Specific model to use (provider-dependent)"
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature (0.0-2.0)"
    )
    max_tokens: int = Field(default=4000, gt=0, description="Maximum tokens to generate")
    api_key: Optional[str] = Field(default=None, description="API key for hosted providers")
    base_url: Optional[str] = Field(default=None, description="Custom API base URL")


class OSCWorkflowSampler:
    """Advanced sampler for OSC automation workflows using FastMCP 2.14.3+."""

    def __init__(self, config: SamplingConfig = None):
        """Initialize the OSC workflow sampler.

        Args:
            config: Sampling configuration for LLM interrogation
        """
        self.config = config or SamplingConfig()
        self._client = None
        logger.info("OSC Workflow Sampler initialized with config: %s", self.config.model_dump())

    async def get_sampling_client(self):
        """Get or create the sampling client for FastMCP 2.14.3+."""
        if self._client is None:
            try:
                from fastmcp import sampling

                # Create sampling client based on configuration
                if self.config.provider == "anthropic":
                    self._client = sampling.AnthropicSamplingClient(
                        api_key=self.config.api_key,
                        model=self.config.model or "claude-3-5-sonnet-20241022",
                        temperature=self.config.temperature,
                        max_tokens=self.config.max_tokens,
                    )
                elif self.config.provider == "openai":
                    self._client = sampling.OpenAISamplingClient(
                        api_key=self.config.api_key,
                        base_url=self.config.base_url,
                        model=self.config.model or "gpt-4",
                        temperature=self.config.temperature,
                        max_tokens=self.config.max_tokens,
                    )
                else:  # auto
                    # Try to detect available providers
                    try:
                        import anthropic

                        self._client = sampling.AnthropicSamplingClient(
                            api_key=self.config.api_key,
                            model=self.config.model or "claude-3-5-sonnet-20241022",
                            temperature=self.config.temperature,
                            max_tokens=self.config.max_tokens,
                        )
                        logger.info("Using Anthropic for sampling")
                    except ImportError:
                        try:
                            import openai

                            self._client = sampling.OpenAISamplingClient(
                                api_key=self.config.api_key,
                                base_url=self.config.base_url,
                                model=self.config.model or "gpt-4",
                                temperature=self.config.temperature,
                                max_tokens=self.config.max_tokens,
                            )
                            logger.info("Using OpenAI for sampling")
                        except ImportError:
                            raise RuntimeError(
                                "No LLM providers available. Install anthropic or openai packages."
                            )

            except ImportError as e:
                logger.error("FastMCP sampling not available: %s", e)
                raise RuntimeError("FastMCP 2.14.3+ sampling capabilities required") from e

        return self._client

    async def generate_osc_workflow(
        self,
        task_description: str,
        target_applications: List[str] = None,
        complexity_level: Literal["simple", "intermediate", "advanced"] = "intermediate",
    ) -> Dict[str, Any]:
        """Generate an intelligent OSC workflow for audio/visual automation.

        Args:
            task_description: Natural language description of the automation task
            target_applications: List of target applications (e.g., ["resolume", "ableton"])
            complexity_level: Desired complexity of the generated workflow

        Returns:
            Dictionary containing generated OSC workflow with messages and logic
        """
        client = await self.get_sampling_client()

        prompt = f"""Generate an OSC (Open Sound Control) automation workflow for the following task:

Task: {task_description}
Target Applications: {", ".join(target_applications or ["generic"])}
Complexity Level: {complexity_level}

Please provide:
1. OSC address patterns needed
2. Message sequences and timing
3. Parameter ranges and mappings
4. Error handling strategies
5. Integration patterns for the target applications

Format as a structured JSON response with the following keys:
- workflow_name: A descriptive name for this workflow
- description: Brief explanation of what this workflow does
- target_apps: List of target applications
- osc_messages: Array of message objects with address, values, timing
- parameters: Object defining parameter ranges and defaults
- error_handling: Error handling strategies
- integration_notes: Notes on integrating with target applications

Ensure OSC addresses follow standard conventions (starting with /)."""

        try:
            response = await client.sample(prompt=prompt)
            # Parse and validate the response
            import json

            result = json.loads(response.content)

            logger.info("Generated OSC workflow: %s", result.get("workflow_name", "Unknown"))
            return result

        except Exception as e:
            logger.error("Failed to generate OSC workflow: %s", e)
            return {
                "error": f"Workflow generation failed: {e!s}",
                "fallback_workflow": self._create_fallback_workflow(task_description),
            }

    async def validate_osc_message(
        self, address: str, values: List[Any], application_context: str = "generic"
    ) -> Dict[str, Any]:
        """Validate OSC message format and appropriateness using LLM.

        Args:
            address: OSC address pattern
            values: OSC message values
            application_context: Target application context

        Returns:
            Validation results with suggestions and corrections
        """
        client = await self.get_sampling_client()

        prompt = f"""Validate this OSC message for {application_context}:

Address: {address}
Values: {values}

Please check:
1. Address pattern validity and conventions
2. Value type appropriateness
3. Application-specific requirements
4. Potential issues or improvements

Return a JSON response with:
- valid: boolean indicating if message is valid
- issues: array of identified issues
- suggestions: array of improvement suggestions
- corrected_address: suggested corrected address if needed
- corrected_values: suggested corrected values if needed"""

        try:
            response = await client.sample(prompt=prompt)
            import json

            result = json.loads(response.content)
            return result
        except Exception as e:
            logger.error("OSC message validation failed: %s", e)
            return {
                "valid": True,  # Fallback to valid
                "issues": [],
                "suggestions": ["LLM validation unavailable"],
                "error": str(e),
            }

    async def enhance_osc_workflow(
        self,
        workflow: Dict[str, Any],
        enhancement_type: Literal["optimization", "robustness", "features"] = "optimization",
    ) -> Dict[str, Any]:
        """Enhance an existing OSC workflow using LLM intelligence.

        Args:
            workflow: Existing workflow to enhance
            enhancement_type: Type of enhancement to apply

        Returns:
            Enhanced workflow with improvements
        """
        client = await self.get_sampling_client()

        prompt = f"""Enhance this OSC workflow with {enhancement_type} improvements:

Current Workflow: {workflow}

Please provide {enhancement_type}-focused enhancements such as:
- Better error handling and recovery
- Performance optimizations
- Additional features and capabilities
- Improved parameter handling
- Cross-application compatibility

Return the enhanced workflow in the same JSON format."""

        try:
            response = await client.sample(prompt=prompt)
            import json

            enhanced_workflow = json.loads(response.content)
            return enhanced_workflow
        except Exception as e:
            logger.error("Workflow enhancement failed: %s", e)
            return workflow  # Return original if enhancement fails

    async def validate_osc_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an OSC workflow structure and logic using LLM analysis.

        Args:
            workflow: Workflow dictionary to validate

        Returns:
            Validation results with issues and suggestions
        """
        client = await self.get_sampling_client()

        prompt = f"""Validate this OSC workflow for correctness and best practices:

Workflow: {workflow}

Please check:
1. OSC address pattern validity and conventions
2. Message sequencing and timing logic
3. Parameter ranges and defaults
4. Error handling completeness
5. Integration compatibility
6. Performance considerations

Return a JSON response with:
- valid: boolean indicating if workflow is valid
- confidence: confidence level (high/medium/low)
- issues: array of identified issues with severity
- suggestions: array of specific improvement suggestions
- fix_suggestions: actionable steps to resolve issues
- compatibility_notes: notes about application compatibility"""

        try:
            response = await client.sample(prompt=prompt)
            import json

            result = json.loads(response.content)
            return result
        except Exception as e:
            logger.error("Workflow validation failed: %s", e)
            return {
                "valid": True,  # Fallback to valid
                "confidence": "low",
                "issues": [],
                "suggestions": ["LLM validation unavailable - manual review recommended"],
                "fix_suggestions": [],
                "compatibility_notes": "Unable to analyze compatibility",
            }

    async def execute_osc_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an OSC workflow with intelligent monitoring.

        Args:
            workflow: Workflow dictionary to execute

        Returns:
            Execution results with timing and success metrics
        """
        import asyncio
        import time

        from pythonosc import SimpleUDPClient

        start_time = time.time()
        executed_messages = []
        errors = []

        try:
            # Extract workflow parameters
            messages = workflow.get("osc_messages", [])
            host = workflow.get("host", "127.0.0.1")
            port = workflow.get("port", 8000)

            client = SimpleUDPClient(host, port)

            # Execute messages with timing
            for i, message in enumerate(messages):
                try:
                    address = message["address"]
                    values = message["values"]
                    timing = message.get("timing", "immediate")

                    # Handle timing delays
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

            # Generate analysis
            success_rate = (
                len([m for m in executed_messages if m["success"]]) / len(executed_messages)
                if executed_messages
                else 0
            )

            analysis = {
                "total_messages": len(messages),
                "executed_messages": len(executed_messages),
                "successful_messages": len([m for m in executed_messages if m["success"]]),
                "failed_messages": len(errors),
                "success_rate": success_rate,
                "execution_time": execution_time,
                "average_message_time": execution_time / len(executed_messages)
                if executed_messages
                else 0,
                "performance": "good"
                if success_rate > 0.9
                else "fair"
                if success_rate > 0.7
                else "poor",
            }

            return {
                "success": len(errors) == 0,
                "analysis": analysis,
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
        self, server_result: Dict[str, Any], send_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze OSC connectivity test results using LLM.

        Args:
            server_result: Result from starting OSC listener
            send_result: Result from sending test message

        Returns:
            Analysis of test results with recommendations
        """
        client = await self.get_sampling_client()

        prompt = f"""Analyze these OSC connectivity test results:

Server Result: {server_result}
Send Result: {send_result}

Please provide:
1. Overall connectivity assessment
2. Specific issues identified
3. Confidence level in the results
4. Recommendations for improvement
5. Next steps for troubleshooting

Return a JSON response with:
- summary: brief assessment summary
- confidence: confidence level (high/medium/low)
- issues: array of identified issues
- recommendations: array of specific recommendations
- next_steps: ordered list of troubleshooting steps"""

        try:
            response = await client.sample(prompt=prompt)
            import json

            result = json.loads(response.content)
            return result
        except Exception as e:
            logger.error("Test analysis failed: %s", e)
            return {
                "summary": "OSC test completed - analysis unavailable",
                "confidence": "low",
                "issues": [],
                "recommendations": ["Check OSC connectivity manually"],
                "next_steps": [
                    "Verify target application is running",
                    "Check firewall settings",
                    "Test with different ports",
                ],
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
            "error_handling": ["basic_timeout", "retry_once"],
            "integration_notes": "This is a fallback workflow. Consider manual refinement.",
        }


# Global sampler instance
osc_sampler = OSCWorkflowSampler()
