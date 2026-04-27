from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Check:
    """A named pre-gate check that must pass before a spec can enter at-gate."""
    name: str
    command: str
    description: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "command": self.command, "description": self.description}


@dataclass
class Config:
    # Tooling
    author: str = ""
    ai_provider: str = "claude-code"   # claude-code | anthropic | openai
    ai_model: str = ""                 # leave blank to use provider default
    ai_base_url: str = ""              # for openai provider (Ollama, Groq, etc.)
    default_template: str = "feature"
    git_auto_commit: bool = True       # auto-commit .spec/ on transitions

    # Pre-gate checks — commands that must pass before entering at-gate
    checks: list = field(default_factory=list)   # list of Check objects

    # Project context — used to enrich AI drafts
    project_name: str = ""
    description: str = ""
    languages: list = field(default_factory=list)
    frameworks: list = field(default_factory=list)
    libraries: list = field(default_factory=list)
    testing: str = ""          # e.g. "pytest, coverage > 80%, no mocks for DB"
    architecture: str = ""     # e.g. "hexagonal, event-driven"
    conventions: list = field(default_factory=list)  # e.g. ["snake_case", "REST not GraphQL"]
    out_of_bounds: list = field(default_factory=list)  # things never to do

    extra: dict = field(default_factory=dict)

    def context_summary(self) -> str:
        """Returns a human/AI-readable summary of the project context."""
        lines = []
        if self.project_name:
            lines.append(f"Project: {self.project_name}")
        if self.description:
            lines.append(f"Description: {self.description}")
        if self.languages:
            lines.append(f"Languages: {', '.join(self.languages)}")
        if self.frameworks:
            lines.append(f"Frameworks: {', '.join(self.frameworks)}")
        if self.libraries:
            lines.append(f"Libraries: {', '.join(self.libraries)}")
        if self.testing:
            lines.append(f"Testing: {self.testing}")
        if self.architecture:
            lines.append(f"Architecture: {self.architecture}")
        if self.conventions:
            lines.append(f"Conventions: {', '.join(self.conventions)}")
        if self.out_of_bounds:
            lines.append(f"Out of bounds: {', '.join(self.out_of_bounds)}")
        if self.checks:
            check_names = ", ".join(f"{c.name} (`{c.command}`)" for c in self.checks)
            lines.append(f"Checks (must pass before at-gate): {check_names}")
        return "\n".join(lines)


_KNOWN_FIELDS = {
    "author", "ai_provider", "ai_model", "ai_base_url", "default_template",
    "git_auto_commit", "checks",
    "project_name", "description", "languages", "frameworks",
    "libraries", "testing", "architecture", "conventions", "out_of_bounds",
}


def load_config(root: Path) -> Config:
    config_path = root / ".spec" / "config.yaml"
    if not config_path.exists():
        return Config()
    try:
        data = yaml.safe_load(config_path.read_text()) or {}
    except Exception:
        return Config()
    extra = {k: v for k, v in data.items() if k not in _KNOWN_FIELDS}

    raw_checks = data.get("checks") or []
    checks = []
    for c in raw_checks:
        if isinstance(c, dict) and "name" in c and "command" in c:
            checks.append(Check(
                name=c["name"],
                command=c["command"],
                description=c.get("description", ""),
            ))

    return Config(
        author=data.get("author", ""),
        ai_provider=data.get("ai_provider", "claude-code"),
        ai_model=data.get("ai_model", ""),
        ai_base_url=data.get("ai_base_url", ""),
        default_template=data.get("default_template", "feature"),
        git_auto_commit=data.get("git_auto_commit", True),
        checks=checks,
        project_name=data.get("project_name", ""),
        description=data.get("description", ""),
        languages=data.get("languages") or [],
        frameworks=data.get("frameworks") or [],
        libraries=data.get("libraries") or [],
        testing=data.get("testing", ""),
        architecture=data.get("architecture", ""),
        conventions=data.get("conventions") or [],
        out_of_bounds=data.get("out_of_bounds") or [],
        extra=extra,
    )


def save_config(config: Config, root: Path) -> None:
    config_path = root / ".spec" / "config.yaml"
    data: dict = {}
    data["author"] = config.author
    data["ai_provider"] = config.ai_provider
    data["ai_model"] = config.ai_model
    data["ai_base_url"] = config.ai_base_url
    data["default_template"] = config.default_template
    data["git_auto_commit"] = config.git_auto_commit
    if config.checks:
        data["checks"] = [c.to_dict() for c in config.checks]
    if config.project_name:
        data["project_name"] = config.project_name
    if config.description:
        data["description"] = config.description
    if config.languages:
        data["languages"] = config.languages
    if config.frameworks:
        data["frameworks"] = config.frameworks
    if config.libraries:
        data["libraries"] = config.libraries
    if config.testing:
        data["testing"] = config.testing
    if config.architecture:
        data["architecture"] = config.architecture
    if config.conventions:
        data["conventions"] = config.conventions
    if config.out_of_bounds:
        data["out_of_bounds"] = config.out_of_bounds
    data.update(config.extra)
    config_path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True))
