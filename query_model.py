# import requests
# import json
# import sys
# import os
# from typing import Optional

# def query_model(
#     prompt: str,
#     model: str,
#     file_path: str = "",
#     debug: bool = False,
#     generate_json_response: bool = False,
#     server: str = "ollama"
# ) -> Optional[str]:
#     """
#     Simple query function for language models.
    
#     Args:
#         prompt (str): The input prompt for the model.
#         model (str): The name of the model to query.
#         file_path (str): Not used in simplified version.
#         debug (bool): If True, print debug messages.
#         generate_json_response (bool): Not used in simplified version.
#         server (str): The server type ('ollama', 'gemini', 'deepseek').

#     Returns:
#         Optional[str]: Response text from the model.
#     """
#     if debug:
#         print("Entering query_model")

#     try:
#         # Simple request based on server type
#         if server == "ollama":
#             response = requests.post(
#                 "http://192.168.13.162:11434/api/generate",
#                 json={"model": model, "prompt": prompt},
#                 stream=True,
#                 timeout=90,
#             )
            
#             # Handle Ollama streaming response
#             summary = ""
#             for line in response.iter_lines():
#                 if not line:
#                     continue
#                 try:
#                     data = json.loads(line.decode("utf-8"))
#                     response_text = data.get("response", "")
#                     summary += response_text
#                     print(response_text, end="", flush=True)
#                     if data.get("done", False):
#                         print()
#                         break
#                 except json.JSONDecodeError:
#                     continue
            
#             return summary

#         else:
#             raise ValueError(f"Unsupported server: {server}")

#     except Exception as e:
#         print(f"Error in query_model: {e}", file=sys.stderr)
#         return None


# if __name__ == "__main__":
#     # Simple test
#     result = query_model("TELLME ABOUT THE LLAMA3.1-B8 MODEL?", "llama3.1:8b", debug=True, server="ollama")
#     print(f"Result: {result}")




import requests
import json
import sys
import os
from typing import Optional
from langchain_core.language_models.llms import LLM
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from pydantic import Field

class CustomLLM:
    def __init__(self, model: str, server: str = "ollama", debug: bool = False):
        self.model = model
        self.server = server
        self.debug = debug
        self.bound_tools = []

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.1) -> Optional[str]:
        """
        Generate a response for the given prompt using the selected model.
        
        Args:
            prompt (str): The input text.
            max_tokens (int): Max number of tokens to generate (can be ignored if not used by server).
            temperature (float): Sampling temperature (can be ignored if not used by server).
        
        Returns:
            Optional[str]: The generated text.
        """
        if self.debug:
            print("Generating response with CustomLLM...")
        
        try:
            if self.server == "ollama":
                response = requests.post(
                    "http://192.168.13.162:11434/api/generate",
                    json={"model": self.model, "prompt": prompt},
                    stream=True,
                    timeout=90,
                )
                summary = ""
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line.decode("utf-8"))
                        response_text = data.get("response", "")
                        summary += response_text
                        print(response_text, end="", flush=True)
                        if data.get("done", False):
                            print()
                            break
                    except json.JSONDecodeError:
                        continue
                return summary
            else:
                raise ValueError(f"Unsupported server: {self.server}")

        except Exception as e:
            print(f"Error in CustomLLM.generate: {e}", file=sys.stderr)
            return None

class MCPCompatibleLLM(BaseChatModel):
    """ChatModel wrapper that makes CustomLLM compatible with MCPAgent"""
    
    custom_llm: CustomLLM = Field(description="The custom LLM instance to wrap")
    
    def __init__(self, custom_llm: CustomLLM, **kwargs):
        super().__init__(custom_llm=custom_llm, **kwargs)
    
    def _generate(self, messages: list[BaseMessage], stop=None, run_manager=None, **kwargs) -> ChatResult:
        """Generate response in ChatGeneration format for MCPAgent"""
        # Convert messages to prompt string
        prompt_str = self._convert_messages_to_string(messages)
        
        # Enhanced prompt for tool calling
        tool_calling_prompt = f"""
You are a network orchestration AI. When you need to use tools, respond with JSON in this exact format:

{{
  "tool_calls": [
    {{
      "name": "tool_name",
      "args": {{"parameter": "value"}},
      "id": "call_1"
    }}
  ]
}}

Available tools and their correct parameters:
- get_device_loss_and_latency_history: {{"args": {{}}, "id": "call_1"}}
- get_organization_uplinks_statuses: {{"args": {{}}, "id": "call_1"}}
- update_uplink: {{"args": {{"uplink_data": "Move device SERIAL to wan1"}}, "id": "call_1"}}
- update_appliance_settings: {{"args": {{"settings_data": "Set degradedLinks for wan1, wan2, wan3 to ok"}}, "id": "call_1"}}
- get_network_settings: {{"args": {{}}, "id": "call_1"}}

User request: {prompt_str}

IMPORTANT: Use the exact parameter names shown above. For update_uplink, use "uplink_data" as the parameter name.
"""
        
        # Get response from custom LLM
        response = self.custom_llm.generate(tool_calling_prompt)
        
        if response is None:
            response = "No response generated"
        
        # Check if response contains tool calls
        import json
        try:
            # Try to parse as JSON tool call
            if "tool_calls" in response:
                tool_data = json.loads(response)
                # Create AIMessage with tool calls
                message = AIMessage(
                    content="",
                    tool_calls=[{
                        "name": call["name"],
                        "args": call["args"],
                        "id": call["id"]
                    } for call in tool_data["tool_calls"]]
                )
                generation = ChatGeneration(message=message)
                return ChatResult(generations=[generation])
        except:
            pass
        
        # Create ChatGeneration with normal text response
        message = AIMessage(content=response)
        generation = ChatGeneration(message=message)
        
        return ChatResult(generations=[generation])
    
    async def _agenerate(self, messages: list[BaseMessage], stop=None, run_manager=None, **kwargs) -> ChatResult:
        """Async version"""
        return self._generate(messages, stop, run_manager, **kwargs)
    
    def _convert_messages_to_string(self, messages: list[BaseMessage]) -> str:
        """Convert LangChain messages to string"""
        prompt_parts = []
        for msg in messages:
            if hasattr(msg, 'content'):
                prompt_parts.append(msg.content)
            else:
                prompt_parts.append(str(msg))
        return "\n".join(prompt_parts)
    
    @property
    def _llm_type(self) -> str:
        return "custom_ollama_chat"
    
    def bind_tools(self, tools, **kwargs):
        """Store tools for potential use"""
        self.custom_llm.bound_tools = tools
        return self

# Usage in your main script
if __name__ == "__main__":

    print("Initializing CustomLLM as Latency Monitoring Agent...")
    custom_llm = CustomLLM(model="llama3.1:8b", server="ollama", debug=True)
    
    print("Creating Latency Monitoring Agent...")
   
    print( custom_llm.generate("TELLME ABOUT mcp?"))
