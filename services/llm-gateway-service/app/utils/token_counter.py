"""Token counting utilities."""
import tiktoken
from typing import List, Dict, Any


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """
    Count tokens in a text string.

    Args:
        text: The text to count tokens for
        encoding_name: The tokenizer encoding to use (default: cl100k_base for GPT-4)

    Returns:
        Number of tokens
    """
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception:
        # Fallback to approximate counting if encoding fails
        return len(text) // 4  # Rough approximation: 1 token ≈ 4 characters


def count_messages_tokens(messages: List[Dict[str, str]], model: str = "gpt-4") -> int:
    """
    Count tokens in a list of messages.

    Based on OpenAI's token counting guide:
    https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb

    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: The model name to determine encoding

    Returns:
        Total number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    # Token calculation varies by model
    if model.startswith("gpt-3.5-turbo") or model.startswith("gpt-4"):
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        tokens_per_message = 3
        tokens_per_name = 1

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(str(value)))
            if key == "name":
                num_tokens += tokens_per_name

    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>

    return num_tokens


def format_document_block(content: str, source: str, doc_type: str, index: int) -> str:
    """
    Format content as a document block (similar to v1 format).

    Args:
        content: The document content
        source: Source identifier (file path or name)
        doc_type: Type of document (custom_instructions, curated_datasets, etc.)
        index: Document index number

    Returns:
        Formatted document block string
    """
    return f"""<document index="{index}">
<source>{source}</source>
<document_type>{doc_type}</document_type>
<document_content>
{content}
</document_content>
</document>
"""


def wrap_documents(documents: List[str]) -> str:
    """
    Wrap multiple document blocks in a documents container.

    Args:
        documents: List of formatted document blocks

    Returns:
        Wrapped documents string
    """
    if not documents:
        return ""

    return "<documents>\n" + "\n".join(documents) + "\n</documents>"


def human_format_number(num: float) -> str:
    """
    Convert a number to a human-readable format.

    Args:
        num: Number to format

    Returns:
        Formatted string (e.g., "1.5k", "2.3M")
    """
    num = float('{:.3g}'.format(num))
    magnitude = 0
    suffixes = ['', 'k', 'M', 'B', 'T']

    while abs(num) >= 1000 and magnitude < len(suffixes) - 1:
        magnitude += 1
        num /= 1000.0

    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), suffixes[magnitude])
