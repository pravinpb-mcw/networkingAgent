"""
Custom GLM-4.5 Model for DeepEval
Based on Anthropic-compatible API via z.ai
"""

import os
from typing import Optional
from pydantic import BaseModel
from anthropic import Anthropic
import instructor

from deepeval.models import DeepEvalBaseLLM


class CustomGLM45(DeepEvalBaseLLM):
    """
    Custom LLM implementation for DeepEval using GLM-4.5
    via Anthropic-compatible API.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: str = "glm-4.5",
        max_tokens: int = 2048
    ):
        self.api_key = api_key or os.getenv(
            "ANTHROPIC_API_KEY", 
            "60b19768f0334766a3e3259590b14460.QTFX9bVQYgALL0Mj"
        )
        self.base_url = base_url or os.getenv(
            "ANTHROPIC_BASE_URL",
            "https://api.z.ai/api/anthropic"
        )
        self.model_name = model_name
        self.max_tokens = max_tokens
        self._client = None
        self._instructor_client = None
    
    @property
    def client(self) -> Anthropic:
        """Lazy-load the Anthropic client"""
        if self._client is None:
            self._client = Anthropic(
                base_url=self.base_url,
                api_key=self.api_key
            )
        return self._client
    
    @property
    def instructor_client(self):
        """Lazy-load the instructor-wrapped client"""
        if self._instructor_client is None:
            self._instructor_client = instructor.from_anthropic(self.client)
        return self._instructor_client
    
    def load_model(self):
        """Required by DeepEvalBaseLLM"""
        return self.client
    
    def generate(self, prompt: str, schema: BaseModel) -> BaseModel:
        """
        Generate structured output from the LLM.
        
        Args:
            prompt: The input prompt
            schema: Pydantic model for structured output
        
        Returns:
            Instance of the schema class with LLM response
        """
        resp = self.instructor_client.messages.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            response_model=schema,
        )
        return resp
    
    async def a_generate(self, prompt: str, schema: BaseModel) -> BaseModel:
        """
        Async version of generate (calls sync version for now).
        
        Args:
            prompt: The input prompt
            schema: Pydantic model for structured output
        
        Returns:
            Instance of the schema class with LLM response
        """
        return self.generate(prompt, schema)
    
    def get_model_name(self) -> str:
        """Return the model name for DeepEval"""
        return self.model_name


# Convenience singleton
_default_model = None

def get_default_model() -> CustomGLM45:
    """Get or create the default CustomGLM45 instance"""
    global _default_model
    if _default_model is None:
        _default_model = CustomGLM45()
    return _default_model
