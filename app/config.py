"""Configuration settings and environment variable controls for GxP multi-agent runs."""

import os


class QualitySystemConfig:
    """Enterprise-grade CSV validation configurations."""

    # 1. API Retry Controls
    API_MAX_RETRIES: int = int(os.getenv("CSV_API_MAX_RETRIES", "3"))
    API_TIMEOUT_SEC: float = float(os.getenv("CSV_API_TIMEOUT_SEC", "30.0"))
    API_INITIAL_DELAY_SEC: float = float(os.getenv("CSV_API_INITIAL_DELAY", "1.0"))
    API_BACKOFF_FACTOR: float = float(os.getenv("CSV_API_BACKOFF_FACTOR", "2.0"))

    # 1.5. Shadow Testing Engine Feature Flag
    SHADOW_ENABLED: bool = os.getenv("CSV_SHADOW_ENABLED", "True").lower() == "true"

    # 2. Model Routing Definitions
    @classmethod
    def get_primary_model(cls) -> str:
        """Detect and return primary configured LLM endpoint."""
        if model_env := os.getenv("CSV_MODEL_NAME"):
            return model_env
        if "ANTHROPIC_API_KEY" in os.environ:
            if model_name := os.getenv("ANTHROPIC_MODEL"):
                return f"anthropic:{model_name}"
            return "anthropic:claude-3-5-sonnet-latest"
        if "OPENAI_API_KEY" in os.environ:
            if model_name := os.getenv("OPENAI_MODEL"):
                return f"openai:{model_name}"
            return "openai:gpt-4o"
        if "GOOGLE_API_KEY" in os.environ:
            return "google:gemini-2.0-flash"
        # Fallback to test model if no keys present
        return "test"

    @classmethod
    def get_fallback_model(cls) -> str:
        """Detect and return high-availability secondary model endpoint."""
        if fallback_env := os.getenv("CSV_FALLBACK_MODEL_NAME"):
            return fallback_env
        # Fallback choices based on API keys present
        if "GOOGLE_API_KEY" in os.environ:
            return "google:gemini-2.0-flash"
        if "OPENAI_API_KEY" in os.environ:
            return "openai:gpt-4o-mini"
        if "ANTHROPIC_API_KEY" in os.environ:
            return "anthropic:claude-3-haiku-20240307"
        # Fallback to test model if no keys present
        return "test"
