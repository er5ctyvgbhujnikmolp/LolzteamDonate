import logging
import re

logger = logging.getLogger("TextFiltering")


def filter_text_with_banwords(text: str, banwords: list) -> str:
    """Filter text using the provided list of banned words.

    Args:
        text: Text to filter
        banwords: List of banned words

    Returns:
        Filtered text
    """
    if not text or not banwords:
        return text

    filtered_text = text
    for word in banwords:
        if word and len(word) > 0:  # Check if word is not empty
            try:
                # Use regular expressions for case-insensitive replacement
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                filtered_text = pattern.sub('*' * len(word), filtered_text)
            except Exception as e:
                logger.error(f"Error filtering word '{word}': {str(e)}")

    return filtered_text


def filter_urls_from_text(text: str, should_filter: bool = True) -> str:
    """Filter URLs from text.

    Args:
        text: Text to filter
        should_filter: Whether URLs should be filtered

    Returns:
        Filtered text
    """
    if not text or not should_filter:
        return text

    try:
        # URL pattern
        url_pattern = re.compile(r'https?://\S+|www\.\S+')
        # Replace URLs with [URL REMOVED]
        return url_pattern.sub('[URL REMOVED]', text)
    except Exception as e:
        logger.error(f"Error filtering URLs: {str(e)}")
        return text
