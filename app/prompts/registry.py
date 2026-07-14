"""Prompt Configuration Registry managing decoupled system instructions with version mapping."""

import os
import re
from typing import Dict, Tuple


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
                frontmatter_raw = frontmatter_match.group(1)
                template_text = frontmatter_match.group(2)

                # Extract version metadata parameter
                for line in frontmatter_raw.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        if k.strip() == "version":
                            version = v.strip()

            self.cache[agent_name] = (version, template_text)
            return version, template_text
        except Exception as e:
            raise IOError(f"Failed to read or parse prompt file '{agent_name}': {str(e)}") from e

    def get_prompt_version(self, agent_name: str) -> str:
        """Retrieves the version string registered on the prompt template."""
        version, _ = self._load_and_parse(agent_name)
        return version

    def get_prompt(self, agent_name: str, variables: dict) -> str:
        """Loads prompt template content and dynamically interpolates template variables.

        Args:
            agent_name: Target subagent template name.
            variables: Dict containing variable substitution values.
        """
        _, template_text = self._load_and_parse(agent_name)
        try:
            return template_text.format(**variables)
        except KeyError as e:
            raise KeyError(f"Missing required prompt template variable {str(e)} for '{agent_name}'") from e


# Export global registry instance
prompt_registry = PromptRegistry()
