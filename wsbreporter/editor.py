import os

from . import config
from . import llm


def edit_summary(source_content: str, draft_markdown: str) -> str | None:
    try:
        prompt_template = _load_prompt_template(config.EDITOR_PROMPT_TEMPLATE_PATH)
        prompt = prompt_template.format(
            content=source_content,
            draft=draft_markdown,
            model_name=config.get_llm_display_name(),
        )
        response = llm.generate([llm.LLMMessage(role="user", content=prompt)])
        return response.text
    except Exception as e:
        print(f"Error editing summary with {config.get_llm_display_name()}: {e}")
        return None


def _load_prompt_template(template_path: str) -> str:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.isabs(template_path):
        template_path = os.path.join(project_root, template_path)

    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()
