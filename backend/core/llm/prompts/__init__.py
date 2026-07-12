"""Jinja2 prompt templates for the customs analysis pipeline.

Each pipeline stage's user prompt lives in a .j2 file next to this module.
Templates render plain text for LLM consumption, so autoescape stays off and
literal braces in the embedded JSON examples survive verbatim.
"""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

_ENV = Environment(
    loader=FileSystemLoader(Path(__file__).parent),
    undefined=StrictUndefined,  # missing variable -> loud error, not a silent leak
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,
)


def load_prompt(template_name: str, **variables: Any) -> str:
    """Render a .j2 prompt template with the given variables."""
    return _ENV.get_template(template_name).render(**variables)
