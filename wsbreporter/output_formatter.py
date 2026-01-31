from . import config


def format_summary(summary_text: str) -> str:
    """
    Formats the summary text based on the configured output format.

    Args:
        summary_text (str): The raw summary text from the Gemini model.

    Returns:
        str: The formatted summary.
    """
    if config.OUTPUT_FORMAT == "markdown":
        # For simplicity, we assume the Gemini model already provides
        # a somewhat structured output that can be enhanced with Markdown.
        # This could be extended to add more specific Markdown elements
        # if the Gemini output needs further parsing/restructuring.
        return summary_text
    else:  # "plain" or any other value defaults to plain text
        return summary_text


if __name__ == "__main__":
    # This block is for testing purposes.
    sample_summary = (
        "Today's top discussions on r/wallstreetbets revolve around GameStop (GME) "
        "and AMC (AMC), with strong bullish sentiment. Users are encouraging "
        "each other to 'hold' their positions, anticipating a 'short squeeze'. "
        "Tesla (TSLA) also saw some activity with mixed sentiments regarding "
        "its recent price movements. A few discussions touched upon the broader "
        "market's reaction to inflation reports. The dominant theme remains "
        "community-driven stock speculation."
    )

    print("--- Markdown Output ---")
    config.OUTPUT_FORMAT = "markdown"
    print(format_summary(sample_summary))

    print("\n--- Plain Text Output ---")
    config.OUTPUT_FORMAT = "plain"
    print(format_summary(sample_summary))
