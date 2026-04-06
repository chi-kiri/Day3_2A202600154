import os
import re
import json
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ReActAgent:
    """
    A generic ReAct-style Agent that follows the Thought-Action-Observation loop.
    Uses provided tools to perform actions and reach a goal.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        System prompt for ReAct-style agent.
        Instructs agent to use JSON for Action blocks.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""You are an intelligent assistant. You have access to the following tools:

{tool_descriptions}

Follow this format strictly:

Thought: What do I need to do? What information do I need from the user?
Action:
```json
{{
  "action": "tool_name",
  "action_input": "target_argument"
}}
```

The recipient of the Action will provide an Observation.
Observation: [Result from tool execution]

Continue this Thought/Action/Observation loop as needed.
When you have the final answer, output:

Final Answer: [Your clear and helpful response here]"""

    def run(self, user_input: str) -> str:
        """
        Execute the ReAct loop.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        current_prompt = user_input
        self.history = [{"role": "user", "content": user_input}]
        steps = 0
        full_response = ""
        
        # Metrics accumulation
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_latency_ms = 0
        start_time_all = os.times().elapsed if hasattr(os, 'times') else 0 # Simple way to get wall clock if available, but time.time() is safer

        import time
        start_time_all = time.time()

        while steps < self.max_steps:
            # 1. Generate LLM response
            result = self.llm.generate(
                prompt=current_prompt,
                system_prompt=self.get_system_prompt()
            )
            
            response_text = result["content"]
            full_response += response_text

            # Update metrics
            step_prompt_tokens = result["usage"].get("prompt_tokens", 0)
            step_completion_tokens = result["usage"].get("completion_tokens", 0)
            step_latency = result["latency_ms"]
            
            total_prompt_tokens += step_prompt_tokens
            total_completion_tokens += step_completion_tokens
            total_latency_ms += step_latency

            print(f"Response Text: {response_text}")
            print(f"Step {steps} Metrics: Input={step_prompt_tokens}, Output={step_completion_tokens}, Latency={step_latency}ms")
            print(f"Cumulative Metrics: Input={total_prompt_tokens}, Output={total_completion_tokens}, LLM Latency={total_latency_ms}ms")
            
            logger.log_event("AGENT_STEP", {
                "step": steps,
                "type": "llm_generation",
                "response_len": len(response_text),
                "prompt_tokens": step_prompt_tokens,
                "completion_tokens": step_completion_tokens,
                "latency_ms": step_latency,
                "total_prompt_so_far": total_prompt_tokens,
                "total_completion_so_far": total_completion_tokens
            })
            
            # 2. Check if we have Final Answer
            if "Final Answer:" in response_text:
                final_answer = response_text.split("Final Answer:")[-1].strip()
                wall_latency = int((time.time() - start_time_all) * 1000)
                metrics = {
                    "steps": steps + 1,
                    "total_prompt_tokens": total_prompt_tokens,
                    "total_completion_tokens": total_completion_tokens,
                    "total_latency_ms": wall_latency,
                    "llm_only_latency_ms": total_latency_ms
                }
                logger.log_event("AGENT_END", {"status": "completed", **metrics})
                return {
                    "answer": final_answer,
                    "metrics": metrics
                }
            
            # 3. Parse JSON Action from response
            # Look for JSON blocks inside ```json ... ``` or just { ... }
            action_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
            if not action_match:
                # Fallback to finding the first { and last }
                action_match = re.search(r"({.*})", response_text, re.DOTALL)
            
            if action_match:
                try:
                    action_json = json.loads(action_match.group(1))
                    tool_name = action_json.get("action")
                    args_str = action_json.get("action_input")
                    
                    if tool_name and args_str is not None:
                        # Ensure args_str is a string for the tool functions
                        if not isinstance(args_str, str):
                            args_str = str(args_str)
                            
                        # 4. Execute tool
                        print(f"Executing Tool: {tool_name} with args: {args_str}")
                        observation = self._execute_tool(tool_name, args_str)
                        print(f"Tool Observation: {observation}")
                        
                        logger.log_event("AGENT_STEP", {
                            "step": steps,
                            "type": "tool_execution",
                            "tool_name": tool_name,
                            "args_str": args_str,
                            "observation": observation
                        })
                        
                        # 5. Append observation to prompt for next iteration
                        current_prompt = f"""{full_response}

Observation: {observation}

Continue with your next Thought and Action, or provide a Final Answer."""
                    else:
                        raise ValueError("Missing 'action' or 'action_input' in JSON")
                except (json.JSONDecodeError, ValueError) as e:
                    current_prompt = f"""{full_response}

Observation: Error parsing Action JSON: {str(e)}. Please ensure your Action is a valid JSON block with "action" and "action_input" keys."""
            else:
                # No valid action found, guide LLM back to format
                current_prompt = f"""{full_response}

Observation: Error - Could not find a valid JSON Action block or Final Answer. Please follow the required format:
Action:
```json
{{
  "action": "tool_name",
  "action_input": "argument"
}}
```

Try again:"""
            
            steps += 1
        
        wall_latency = int((time.time() - start_time_all) * 1000)
        metrics = {
            "steps": steps,
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_latency_ms": wall_latency,
            "llm_only_latency_ms": total_latency_ms
        }
        logger.log_event("AGENT_END", {"status": "max_steps_reached", **metrics})
        return {
            "answer": f"Max steps reached ({self.max_steps}). Partial Answer:\n{full_response}",
            "metrics": metrics
        }

    def _execute_tool(self, tool_name: str, args_str: str) -> str:
        """
        Execute tools by name using self.tools list.
        """
        for tool in self.tools:
            if tool['name'] == tool_name:
                func = tool.get('func')
                if callable(func):
                    try:
                        return str(func(args_str))
                    except Exception as e:
                        return f"Error executing tool {tool_name}: {str(e)}"
                return f"Tool {tool_name} is missing a callable function."
        return f"Tool '{tool_name}' not found. Available tools: {', '.join([t['name'] for t in self.tools])}"

    def get_provider_info(self):
        return self.llm.get_provider_info()
