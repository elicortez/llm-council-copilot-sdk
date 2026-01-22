"""GitHub Copilot SDK client for making LLM requests."""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable

from copilot import CopilotClient

from .config import DEFAULT_COUNCIL_MODELS, DEFAULT_CHAIRMAN_MODEL

logger = logging.getLogger(__name__)

# Singleton client instance
_client: Optional[CopilotClient] = None
_available_models: List[Dict[str, Any]] = []


async def start_client() -> None:
    """Start the Copilot client. Called once at app startup."""
    global _client, _available_models

    if _client is not None:
        return

    _client = CopilotClient()
    await _client.start()

    # Fetch available models
    try:
        _available_models = await _client.list_models()
        logger.info(f"Available models: {[m['id'] for m in _available_models]}")
    except Exception as e:
        logger.error(f"Failed to fetch models: {e}")
        _available_models = []

    # Validate default models at startup
    await validate_models()


async def stop_client() -> None:
    """Stop the Copilot client. Called at app shutdown."""
    global _client

    if _client is not None:
        await _client.stop()
        _client = None


async def validate_models() -> Dict[str, bool]:
    """
    Validate that default models are available.
    Logs warnings for unavailable models.

    Returns:
        Dict mapping model ID to availability status
    """
    available_ids = {m['id'] for m in _available_models}
    validation = {}

    all_defaults = set(DEFAULT_COUNCIL_MODELS) | {DEFAULT_CHAIRMAN_MODEL}

    for model_id in all_defaults:
        is_available = model_id in available_ids
        validation[model_id] = is_available
        if not is_available:
            logger.warning(f"Default model '{model_id}' is not available in your Copilot subscription")

    return validation


def get_available_models() -> List[Dict[str, Any]]:
    """
    Get list of available models.

    Returns:
        List of model info dicts with 'id', 'name', 'capabilities', etc.
    """
    return _available_models


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    streaming_callback: Optional[Callable[[str], None]] = None,
    timeout: float = 120.0
) -> Dict[str, Any]:
    """
    Query a single model via Copilot SDK.

    Args:
        model: Copilot model identifier (e.g., "gpt-5", "claude-sonnet-4.5")
        messages: List of message dicts with 'role' and 'content'
        streaming_callback: Optional callback for streaming token deltas
        timeout: Request timeout in seconds (not directly supported, for compatibility)

    Returns:
        Response dict with 'content', 'error' (if failed), and 'model'
    """
    global _client

    if _client is None:
        return {
            'model': model,
            'content': None,
            'error': 'Copilot client not initialized'
        }

    try:
        # Create ephemeral session for this query
        session = await _client.create_session({
            "model": model,
            "streaming": streaming_callback is not None
        })

        try:
            # Convert messages to prompt format
            # The SDK expects a single prompt, so we format the conversation
            prompt = _format_messages_to_prompt(messages)

            if streaming_callback:
                # Use event-based streaming
                content_parts = []
                done_event = asyncio.Event()
                error_holder = [None]

                def on_event(event):
                    if event.type.value == "assistant.message_delta":
                        delta = event.data.delta_content or ""
                        content_parts.append(delta)
                        streaming_callback(delta)
                    elif event.type.value == "assistant.message":
                        done_event.set()
                    elif event.type.value == "session.idle":
                        done_event.set()
                    elif event.type.value == "error":
                        error_holder[0] = getattr(event.data, 'message', str(event.data))
                        done_event.set()

                session.on(on_event)
                await session.send({"prompt": prompt})

                # Wait for completion with timeout
                try:
                    await asyncio.wait_for(done_event.wait(), timeout=timeout)
                except asyncio.TimeoutError:
                    return {
                        'model': model,
                        'content': None,
                        'error': f'Timeout after {timeout}s'
                    }

                if error_holder[0]:
                    return {
                        'model': model,
                        'content': None,
                        'error': error_holder[0]
                    }

                return {
                    'model': model,
                    'content': ''.join(content_parts)
                }
            else:
                # Use send_and_wait for non-streaming
                response = await session.send_and_wait({"prompt": prompt})

                if response is None:
                    return {
                        'model': model,
                        'content': None,
                        'error': 'No response received'
                    }

                return {
                    'model': model,
                    'content': response.data.content
                }

        finally:
            await session.destroy()

    except Exception as e:
        logger.error(f"Error querying model {model}: {e}")
        return {
            'model': model,
            'content': None,
            'error': str(e)
        }


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]],
    streaming_callback: Optional[Callable[[str, str], None]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Query multiple models in parallel.

    Args:
        models: List of Copilot model identifiers
        messages: List of message dicts to send to each model
        streaming_callback: Optional callback(model, delta) for streaming

    Returns:
        Dict mapping model identifier to response dict
    """
    # Create per-model streaming callbacks if provided
    def make_model_callback(model: str):
        if streaming_callback:
            return lambda delta: streaming_callback(model, delta)
        return None

    # Create tasks for all models
    tasks = [
        query_model(model, messages, make_model_callback(model))
        for model in models
    ]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return {model: response for model, response in zip(models, responses)}


def _format_messages_to_prompt(messages: List[Dict[str, str]]) -> str:
    """
    Format a list of messages into a single prompt string.

    The Copilot SDK session already maintains context, so for single-turn
    we just pass the user's message. For multi-turn, we format as conversation.
    """
    if len(messages) == 1 and messages[0].get('role') == 'user':
        return messages[0]['content']

    # Multi-turn: format as conversation
    parts = []
    for msg in messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if role == 'system':
            parts.append(f"System: {content}")
        elif role == 'assistant':
            parts.append(f"Assistant: {content}")
        else:
            parts.append(f"User: {content}")

    return "\n\n".join(parts)
