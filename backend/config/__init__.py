import os
from dotenv import load_dotenv  # type: ignore

# Load environment variables from .env file
load_dotenv()

from config.app_config import AppConfig  # noqa: E402
from config.llm_config import LLMConfig  # noqa: E402
from config.pipeline_config import PipelineConfig  # noqa: E402
from config.pdf_config import pdf_config  # noqa: E402


class Config:
    """
    Central configuration registry providing organized access to all settings.\
    """
    app = AppConfig
    llm = LLMConfig
    pipeline = PipelineConfig
    pdf = pdf_config  # PDF processing configuration manager


# Create the global config instance
config = Config()
