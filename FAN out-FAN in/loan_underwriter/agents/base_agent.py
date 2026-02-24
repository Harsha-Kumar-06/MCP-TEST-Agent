"""
Base Agent class for all loan underwriting agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional
import time
import logging
import json

from google import genai
from google.genai import types

from ..config import config, AgentConfig

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents in the loan underwriting system."""

    def __init__(self, agent_config: AgentConfig):
        """Initialize the agent with configuration."""
        self.config = agent_config
        self.name = agent_config.name
        self.model = agent_config.model
        self.temperature = agent_config.temperature
        self.max_tokens = agent_config.max_tokens

        # Initialize the Google GenAI client
        self.client = genai.Client(api_key=config.google_api_key)

        # Define tools for the agent
        self.tools = self._define_tools()

        logger.info(f"Initialized {self.name}")

    @abstractmethod
    def _define_tools(self) -> list:
        """Define the tools available to this agent."""
        pass

    @abstractmethod
    def _get_system_instruction(self) -> str:
        """Get the system instruction for this agent."""
        pass

    @abstractmethod
    async def analyze(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform analysis on the application data."""
        pass

    async def _run_agent_loop(
        self,
        initial_prompt: str,
        tool_executor: Callable,
        max_iterations: int = 10
    ) -> tuple:
        """
        Run a multi-turn agent loop where the LLM autonomously calls tools.

        The LLM sees the prompt, decides which tools to call, receives results,
        and continues reasoning until it produces a final text answer.

        Returns: (final_text, captured_tool_results, elapsed_ms)
        """
        start_time = time.time()
        captured = {}  # accumulates every tool's raw return value

        contents = [
            types.Content(role="user", parts=[types.Part(text=initial_prompt)])
        ]

        final_text = ""
        iterations_used = 0

        for iteration in range(max_iterations):
            iterations_used = iteration + 1

            generation_config = types.GenerateContentConfig(
                system_instruction=self._get_system_instruction(),
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                tools=[self.tools] if self.tools else None,
            )

            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=generation_config,
            )

            candidate_content = response.candidates[0].content
            contents.append(candidate_content)

            # Collect any function calls in this response
            fn_calls = [
                part for part in candidate_content.parts
                if getattr(part, "function_call", None) is not None
            ]

            if not fn_calls:
                # No tool calls → this is the final answer
                final_text = response.text or ""
                break

            # Execute each tool call and collect responses
            fn_response_parts = []
            for part in fn_calls:
                fc = part.function_call
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}

                logger.info(f"{self.name}: invoking tool '{tool_name}' with args {tool_args}")

                try:
                    result = await tool_executor(tool_name, tool_args, captured)
                    captured[tool_name] = result
                except Exception as exc:
                    logger.error(f"{self.name}: tool '{tool_name}' raised {exc}")
                    result = {"error": str(exc), "status": "failed"}

                fn_response_parts.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=tool_name,
                            response={"result": result},
                        )
                    )
                )

            contents.append(types.Content(role="user", parts=fn_response_parts))

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"{self.name}: agent loop finished in {elapsed_ms}ms "
            f"({iterations_used} iterations)"
        )
        return final_text, captured, elapsed_ms

    def _parse_llm_json(self, text: str) -> dict:
        """Extract and parse the first JSON object found in LLM output."""
        if not text:
            return {}
        # Strip markdown code fences if present
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:])
            if cleaned.endswith("```"):
                cleaned = cleaned[: cleaned.rfind("```")]
        # Find the JSON object
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start:end])
            except json.JSONDecodeError:
                pass
        return {}

    async def _call_llm(self, prompt: str, tools: Optional[list] = None) -> str:
        """Make a single-turn call to the LLM (kept for simple summary calls)."""
        start_time = time.time()

        try:
            generation_config = types.GenerateContentConfig(
                system_instruction=self._get_system_instruction(),
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )

            if tools:
                generation_config.tools = tools

            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=generation_config
            )

            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(f"{self.name} LLM call completed in {elapsed_ms}ms")

            return response.text, elapsed_ms

        except Exception as e:
            logger.error(f"{self.name} LLM call failed: {str(e)}")
            raise

    def _calculate_risk_level(self, risk_score: float) -> str:
        """Calculate risk level based on risk score."""
        if risk_score >= 80:
            return "low"
        elif risk_score >= 60:
            return "medium"
        elif risk_score >= 40:
            return "high"
        else:
            return "critical"
