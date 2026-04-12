"""Project type scaffolding — folders and starter files per type."""
from __future__ import annotations

from pathlib import Path


def scaffold_project(root: Path, project_type: str, name: str) -> list[str]:
    """
    Create project-type-specific folders and files.
    Returns list of created paths (relative to root) for display.
    """
    created = []

    def touch(rel: str, content: str = "") -> None:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_text(content)
            created.append(rel)

    def mkdir(rel: str) -> None:
        p = root / rel
        p.mkdir(parents=True, exist_ok=True)
        # create .gitkeep so empty dirs are tracked
        gk = p / ".gitkeep"
        if not gk.exists():
            gk.write_text("")
            created.append(f"{rel}/.gitkeep")

    if project_type == "python-api":
        touch("pyproject.toml", _pyproject(name))
        touch("src/__init__.py")
        touch(f"src/{_slug(name)}/__init__.py")
        touch(f"src/{_slug(name)}/main.py", _fastapi_main(name))
        touch(f"src/{_slug(name)}/routes/__init__.py")
        touch(f"src/{_slug(name)}/models/__init__.py")
        touch(f"src/{_slug(name)}/services/__init__.py")
        touch("tests/__init__.py")
        touch("tests/conftest.py", _conftest())
        touch("Dockerfile", _dockerfile_python(name))
        touch(".gitignore", _gitignore_python())
        mkdir("docs")

    elif project_type == "typescript-web":
        touch("package.json", _package_json(name))
        touch("tsconfig.json", _tsconfig())
        touch("src/app/page.tsx", _next_page(name))
        touch("src/app/layout.tsx", _next_layout(name))
        touch("src/components/.gitkeep")
        touch("src/lib/.gitkeep")
        touch("public/.gitkeep")
        touch(".gitignore", _gitignore_node())

    elif project_type == "cli-tool":
        touch("pyproject.toml", _pyproject_cli(name))
        touch(f"src/{_slug(name)}/__init__.py")
        touch(f"src/{_slug(name)}/main.py", _cli_main(name))
        touch(f"src/{_slug(name)}/commands/__init__.py")
        touch("tests/__init__.py")
        touch("tests/conftest.py", _conftest())
        touch(".gitignore", _gitignore_python())

    # blank: no extra scaffolding

    return created


def _slug(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _pyproject(name: str) -> str:
    slug = _slug(name)
    return f"""\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{slug}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.27",
    "pydantic>=2.6",
]

[project.optional-dependencies]
dev = ["pytest>=8", "httpx>=0.27", "pytest-asyncio>=0.23"]

[tool.hatch.build.targets.wheel]
packages = ["src/{slug}"]
"""


def _pyproject_cli(name: str) -> str:
    slug = _slug(name)
    return f"""\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{slug}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "typer[all]>=0.12",
    "rich>=13.7",
]

[project.scripts]
{slug} = "{slug}.main:app"

[project.optional-dependencies]
dev = ["pytest>=8", "ruff", "mypy"]

[tool.hatch.build.targets.wheel]
packages = ["src/{slug}"]
"""


def _fastapi_main(name: str) -> str:
    return f"""\
from fastapi import FastAPI

app = FastAPI(title="{name}")


@app.get("/health")
def health():
    return {{"status": "ok"}}
"""


def _cli_main(name: str) -> str:
    slug = _slug(name)
    return f"""\
import typer

app = typer.Typer(name="{slug}", no_args_is_help=True)


@app.command()
def hello():
    \"\"\"Say hello.\"\"\"
    typer.echo("Hello from {name}!")
"""


def _conftest() -> str:
    return """\
import pytest
"""


def _dockerfile_python(name: str) -> str:
    slug = _slug(name)
    return f"""\
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install -e .
COPY src/ src/
CMD ["uvicorn", "{slug}.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""


def _package_json(name: str) -> str:
    slug = _slug(name)
    return f"""\
{{
  "name": "{slug}",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  }},
  "dependencies": {{
    "next": "^14",
    "react": "^18",
    "react-dom": "^18"
  }},
  "devDependencies": {{
    "typescript": "^5",
    "@types/react": "^18",
    "@types/node": "^20"
  }}
}}
"""


def _tsconfig() -> str:
    return """\
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{"name": "next"}],
    "paths": {"@/*": ["./src/*"]}
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
"""


def _next_page(name: str) -> str:
    return f"""\
export default function Home() {{
  return <main><h1>{name}</h1></main>
}}
"""


def _next_layout(name: str) -> str:
    return f"""\
export const metadata = {{ title: "{name}" }}

export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{
  return (
    <html lang="en">
      <body>{{children}}</body>
    </html>
  )
}}
"""


def _gitignore_python() -> str:
    return """\
__pycache__/
*.pyc
.venv/
.env
dist/
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/
"""


def _gitignore_node() -> str:
    return """\
node_modules/
.next/
.env
.env.local
dist/
"""
