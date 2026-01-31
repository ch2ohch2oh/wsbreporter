from google import genai
from . import config


def generate_summary(all_posts_content: str) -> str | None:
    """
    Generates a one-page summary of the aggregated Reddit posts using the Gemini model.

    Args:
        all_posts_content (str): A concatenated string of titles, selftexts, and top comments
                                 from multiple Reddit posts.

    Returns:
        str: The generated one-page summary.
        None: If an error occurs during summarization.
    """
    try:
        # Initialize the client with API key
        client = genai.Client(api_key=config.GEMINI_API_KEY)

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

        current_date = datetime.now().strftime("%B %d, %Y")
        prompt = prompt_template.format(
            content=all_posts_content,
            model_name=config.GEMINI_MODEL_NAME,
            date=current_date,
        )

        response = client.models.generate_content(
            model=config.GEMINI_MODEL_NAME, contents=prompt
        )

        return response.text

    except Exception as e:
        print(f"Error generating summary with Gemini: {e}")
        return None
