import os
import re
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
        Instructs agent to follow Thought-Action-Observation format.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""You are an intelligent assistant. You have access to the following tools:

{tool_descriptions}

Follow this format strictly:
Thought: What do I need to do? What information do I need from the user?
Action: tool_name(argument)
Observation: [Result from tool execution]

Continue until you can provide a Final Answer.
Final Answer: Provide a clear, helpful response."""

    def run(self, user_input: str) -> str:
        """
        Execute the ReAct loop.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        current_prompt = user_input
        self.history = [{"role": "user", "content": user_input}]
        steps = 0
        full_response = ""

        while steps < self.max_steps:
            # 1. Generate LLM response
            result = self.llm.generate(
                prompt=current_prompt,
                system_prompt=self.get_system_prompt()
            )
            
            response_text = result["content"]
            full_response += response_text
            
            logger.log_event("AGENT_STEP", {
                "step": steps,
                "response_len": len(response_text),
                "tokens_used": result["usage"]["total_tokens"]
            })
            
            # 2. Check if we have Final Answer
            if "Final Answer:" in response_text:
                final_answer = response_text.split("Final Answer:")[-1].strip()
                logger.log_event("AGENT_END", {"steps": steps, "status": "completed"})
                return final_answer
            
            # 3. Parse Action from response
            action_match = re.search(r"Action:\s*(\w+)\((.*?)\)", response_text)
            
            if action_match:
                tool_name = action_match.group(1)
                args_str = action_match.group(2)
                
                # 4. Execute tool
                observation = self._execute_tool(tool_name, args_str)
                
                # 5. Append observation to prompt for next iteration
                current_prompt = f"""{full_response}

Observation: {observation}

Continue with your next Thought and Action, or provide a Final Answer."""
            else:
                # No valid action found, guide LLM back to format
                current_prompt = f"""{full_response}

Observation: Error - Could not find Action or Final Answer. Please follow the correct format:
Action: tool_name(argument)

Try again:"""
            
            steps += 1
        
        logger.log_event("AGENT_END", {"steps": steps, "status": "max_steps_reached"})
        return f"Max steps reached ({self.max_steps}). Partial Answer:\n{full_response}"

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
