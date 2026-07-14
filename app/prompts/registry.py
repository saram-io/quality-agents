"""Prompt Configuration Registry managing decoupled system instructions with version mapping."""

import os
import re
from typing import Dict, Tuple
from contextvars import ContextVar

# Define task-local prompt overrides (maps agent_name -> (version, template_text))
shadow_prompt_override: ContextVar = ContextVar("shadow_prompt_override", default=None)


class PromptRegistry:
    """Manages decoupled, versioned agent prompt templates stored in Markdown assets."""

    def __init__(self, prompts_dir: str = None) -> None:
        """Initialize the registry pointing to the prompts folder location."""
        if prompts_dir is None:
            # Resolve prompts directory relative to this package file
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            prompts_dir = os.path.join(base_dir, "prompts")
        self.prompts_dir = prompts_dir
        self.cache: Dict[str, Tuple[str, str]] = {}  # Cache map: {agent_name: (version, template_text)}

    def _load_and_parse(self, agent_name: str) -> Tuple[str, str]:
        """Reads prompt markdown asset and splits YAML frontmatter from template body.

        Returns:
            Tuple of (version_string, template_text).
        """
        if agent_name in self.cache:
            return self.cache[agent_name]

        file_path = os.path.join(self.prompts_dir, f"{agent_name}.md")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"SOP prompt template file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Regex parsing of YAML frontmatter headers (delimited by ---)
            frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
            version = "1.0.0"
            template_text = content
            if frontmatter_match:
                frontmatter = frontmatter_match.group(1)
                template_text = frontmatter_match.group(2)
                for line in frontmatter.split("\n"):
                    if line.startswith("version:"):
                        version = line.split(":", 1)[1].strip()

            self.cache[agent_name] = (version, template_text)
            return version, template_text
        except Exception as e:
            raise IOError(f"Failed parsing markdown frontmatter for '{agent_name}': {str(e)}") from e

    def get_prompt_version(self, agent_name: str) -> str:
        """Retrieves metadata version of a target subagent prompt template."""
        overrides = shadow_prompt_override.get()
        if overrides and agent_name in overrides:
            return overrides[agent_name][0]
        version, _ = self._load_and_parse(agent_name)
        return version

    def get_prompt(self, agent_name: str, variables: dict) -> str:
        """Loads prompt template content and dynamically interpolates template variables.

        Args:
            agent_name: Target subagent template name.
            variables: Dict containing variable substitution values.
        """
        overrides = shadow_prompt_override.get()
        if overrides and agent_name in overrides:
            _, template_text = overrides[agent_name]
        else:
            _, template_text = self._load_and_parse(agent_name)
        try:
            return template_text.format(**variables)
        except KeyError as e:
            raise KeyError(f"Missing required prompt template variable {str(e)} for '{agent_name}'") from e

    def override_prompt(self, agent_name: str, version: str, template_text: str) -> None:
        """Injects a runtime override into the prompt template cache."""
        self.cache[agent_name] = (version, template_text)


# Export global registry instance
prompt_registry = PromptRegistry()
