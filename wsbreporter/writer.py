from . import config
from . import llm


def generate_summary(all_posts_content: str) -> str | None:
    """
    Generates a one-page summary of the aggregated Reddit posts using the configured LLM.

    Args:
        all_posts_content (str): A concatenated string of titles, selftexts, and top comments
                                 from multiple Reddit posts.

    Returns:
        str: The generated one-page summary.
        None: If an error occurs during summarization.
    """
    try:
        # Read the prompt template from file
        import os

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Allow absolute paths or paths relative to project root
        if os.path.isabs(config.PROMPT_TEMPLATE_PATH):
            template_path = config.PROMPT_TEMPLATE_PATH
        else:
            template_path = os.path.join(project_root, config.PROMPT_TEMPLATE_PATH)

        try:
            with open(template_path, "r") as f:
                prompt_template = f.read()
        except FileNotFoundError:
            print(f"Error: {template_path} not found.")
            return None

        # Fill in the template
        from datetime import datetime
        import pytz

        ny_tz = pytz.timezone("America/New_York")
        current_date = datetime.now(ny_tz).strftime("%B %d, %Y at %I:%M %p %Z")
        prompt = prompt_template.format(
            content=all_posts_content,
            model_name=config.get_llm_display_name(),
            date=current_date,
        )

        response = llm.generate([llm.LLMMessage(role="user", content=prompt)])

        return response.text

    except Exception as e:
        print(f"Error generating summary with {config.get_llm_display_name()}: {e}")
        return None
