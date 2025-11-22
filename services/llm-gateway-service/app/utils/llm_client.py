"""LLM client utilities using LiteLLM."""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from litellm import completion, model_cost
import litellm

from .token_counter import count_messages_tokens


class LLMClient:
    """Client for interacting with LLM providers via LiteLLM."""

    def __init__(self):
        """Initialize the LLM client."""
        # Enable verbose logging in development
        litellm.set_verbose = False

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to an LLM provider.

        Args:
            model: Model identifier (e.g., "gpt-4", "claude-3-sonnet")
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters for the model

        Returns:
            Dictionary containing response data
        """
        try:
            response = completion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs
            )

            # Extract response content
            if not stream:
                content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
                usage = response.get('usage', {})

                return {
                    "content": content,
                    "model": response.get('model', model),
                    "usage": {
                        "prompt_tokens": usage.get('prompt_tokens', 0),
                        "completion_tokens": usage.get('completion_tokens', 0),
                        "total_tokens": usage.get('total_tokens', 0)
                    },
                    "finish_reason": response.get('choices', [{}])[0].get('finish_reason', 'unknown')
                }
            else:
                # For streaming, return the generator
                return {"stream": response}

        except Exception as e:
            raise Exception(f"LLM API error: {str(e)}")

    def calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> Optional[Decimal]:
        """
        Calculate the cost of an LLM request.

        Args:
            model: Model identifier
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            Cost in USD as Decimal, or None if pricing not available
        """
        try:
            # Get model pricing from LiteLLM
            if model in model_cost:
                model_info = model_cost[model]

                input_cost_per_token = model_info.get('input_cost_per_token', 0)
                output_cost_per_token = model_info.get('output_cost_per_token', 0)

                total_cost = (
                    Decimal(str(prompt_tokens)) * Decimal(str(input_cost_per_token)) +
                    Decimal(str(completion_tokens)) * Decimal(str(output_cost_per_token))
                )

                return total_cost
            else:
                return None

        except Exception:
            return None

    def prepare_messages(
        self,
        prompt: str,
        system_content: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        supports_system_role: bool = True
    ) -> List[Dict[str, str]]:
        """
        Prepare messages array for LLM request.

        Args:
            prompt: User's current prompt
            system_content: System instructions and context
            conversation_history: Previous messages in conversation
            supports_system_role: Whether the model supports system role

        Returns:
            List of formatted message dictionaries
        """
        messages = []

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Handle system content
        if system_content and system_content.strip():
            if supports_system_role:
                # Add as system message
                if not conversation_history:  # Only add if not in history already
                    messages.insert(0, {"role": "system", "content": system_content})
            else:
                # Add as user message for models that don't support system role
                messages.insert(0, {"role": "user", "content": system_content})

        # Add current user prompt
        messages.append({"role": "user", "content": prompt})

        return messages

    def estimate_tokens(self, messages: List[Dict[str, str]], model: str) -> int:
        """
        Estimate token count for messages.

        Args:
            messages: List of message dictionaries
            model: Model identifier

        Returns:
            Estimated token count
        """
        return count_messages_tokens(messages, model)


# Global client instance
llm_client = LLMClient()
