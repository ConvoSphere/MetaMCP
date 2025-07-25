#!/usr/bin/env python3
"""
Documentation Utilities for MetaMCP

This module provides documentation-related utilities for the MetaMCP project.
"""

import subprocess
import sys
from pathlib import Path


class DocsUtils:
    """Documentation utilities for MetaMCP project management."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.docs_dir = project_root / "docs"

    def run_command(self, command: list[str], cwd: Path | None = None) -> int:
        """Run a shell command and return exit code."""
        try:
            result = subprocess.run(
                command, cwd=cwd or self.project_root, capture_output=True, text=True
            )
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return result.returncode
        except Exception as e:
            print(f"Error running command: {e}", file=sys.stderr)
            return 1

    def check_docs_dependencies(self) -> dict[str, bool]:
        """Check if documentation dependencies are available."""
        dependencies = {}

        # Check mkdocs
        try:
            result = subprocess.run(
                [sys.executable, "-m", "mkdocs", "--version"],
                capture_output=True,
                text=True,
            )
            dependencies["mkdocs"] = result.returncode == 0
        except Exception:
            dependencies["mkdocs"] = False

        # Check mkdocs-material
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import mkdocs_material; print(mkdocs_material.__version__)",
                ],
                capture_output=True,
                text=True,
            )
            dependencies["mkdocs-material"] = result.returncode == 0
        except Exception:
            dependencies["mkdocs-material"] = False

        # Check pymdown-extensions
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import pymdownx; print('pymdown-extensions available')",
                ],
                capture_output=True,
                text=True,
            )
            dependencies["pymdown-extensions"] = result.returncode == 0
        except Exception:
            dependencies["pymdown-extensions"] = False

        return dependencies

    def build_docs(self, clean: bool = True) -> int:
        """Build documentation."""
        print("📚 Building documentation...")

        if clean and (self.project_root / "site").exists():
            print("   Cleaning previous build...")
            self.run_command(["rm", "-rf", "site"])

        return self.run_command([sys.executable, "-m", "mkdocs", "build"])

    def serve_docs(self, host: str = "127.0.0.1", port: int = 8000) -> int:
        """Serve documentation locally."""
        print(f"📖 Serving documentation at http://{host}:{port}...")
        return self.run_command(
            [sys.executable, "-m", "mkdocs", "serve", "--dev-addr", f"{host}:{port}"]
        )

    def deploy_docs(self, target: str = "gh-pages") -> int:
        """Deploy documentation to GitHub Pages."""
        print(f"🚀 Deploying documentation to {target}...")
        return self.run_command([sys.executable, "-m", "mkdocs", "gh-deploy"])

    def validate_docs(self) -> int:
        """Validate documentation structure and links."""
        print("🔍 Validating documentation...")

        # Check if mkdocs.yml exists
        mkdocs_config = self.project_root / "mkdocs.yml"
        if not mkdocs_config.exists():
            print("❌ mkdocs.yml not found")
            return 1

        # Check if docs directory exists
        if not self.docs_dir.exists():
            print("❌ docs directory not found")
            return 1

        # Check for common documentation files
        required_files = [
            "docs/index.md",
            "docs/getting-started/quick-start.md",
            "docs/user-guide/api-reference.md",
        ]

        missing_files = []
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)

        if missing_files:
            print("⚠️  Missing documentation files:")
            for file_path in missing_files:
                print(f"   - {file_path}")

        # Build docs to check for errors
        print("   Building documentation to check for errors...")
        result = self.build_docs()

        if result == 0:
            print("✅ Documentation validation passed")
        else:
            print("❌ Documentation validation failed")

        return result

    def generate_api_docs(self) -> int:
        """Generate API documentation from code."""
        print("🔧 Generating API documentation...")

        # Create API docs directory
        api_docs_dir = self.docs_dir / "api"
        api_docs_dir.mkdir(exist_ok=True)

        # Generate documentation for main modules
        modules = [
            "metamcp.api",
            "metamcp.composition",
            "metamcp.proxy",
            "metamcp.security",
            "metamcp.monitoring",
        ]

        for module in modules:
            print(f"   Generating docs for {module}...")
            # This would typically use a tool like pdoc or sphinx
            # For now, we'll just create placeholder files
            module_docs_file = api_docs_dir / f"{module.replace('.', '_')}.md"
            module_docs_file.write_text(
                f"# {module}\n\nAPI documentation for {module}\n"
            )

        print("✅ API documentation generated")
        return 0

    def update_docs_index(self) -> int:
        """Update the main documentation index."""
        print("📝 Updating documentation index...")

        index_file = self.docs_dir / "index.md"

        # Create a comprehensive index
        index_content = """# MetaMCP Documentation

Welcome to the MetaMCP documentation!

## Quick Start

- [Quick Start Guide](getting-started/quick-start.md)
- [Proxy Quick Start](getting-started/proxy-quick-start.md)

## User Guide

- [API Reference](user-guide/api-reference.md)
- [Proxy Wrapper](user-guide/proxy-wrapper.md)
- [Security](user-guide/security.md)

## Developer Guide

- [Architecture](developer-guide/architecture.md)
- [Code Structure](developer-guide/code-structure.md)
- [Development Setup](developer-guide/development-setup.md)
- [Testing](developer-guide/testing.md)

## Reference

- [Configuration](reference/configuration.md)
- [Environment Variables](reference/environment-variables.md)
- [Proxy API](reference/proxy-api.md)

## Monitoring

- [Monitoring Overview](monitoring/index.md)
- [Production Setup](monitoring/production-setup.md)
- [Telemetry](monitoring/telemetry.md)

## API Documentation

- [API Reference](api/index.md)

## OAuth Integration

- [FastMCP Integration](oauth/fastmcp-integration.md)
"""

        index_file.write_text(index_content)
        print("✅ Documentation index updated")
        return 0

    def create_docs_structure(self) -> int:
        """Create the basic documentation structure."""
        print("📁 Creating documentation structure...")

        # Create main documentation directories
        dirs = [
            "docs/getting-started",
            "docs/user-guide",
            "docs/developer-guide",
            "docs/reference",
            "docs/monitoring",
            "docs/oauth",
            "docs/api",
        ]

        for dir_path in dirs:
            (self.project_root / dir_path).mkdir(parents=True, exist_ok=True)
            print(f"   Created: {dir_path}")

        # Create basic mkdocs.yml if it doesn't exist
        mkdocs_config = self.project_root / "mkdocs.yml"
        if not mkdocs_config.exists():
            config_content = """site_name: MetaMCP Documentation
site_description: Documentation for the MetaMCP project
site_author: MetaMCP Team

theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - search.suggest
    - search.highlight

plugins:
  - search

nav:
  - Home: index.md
  - Getting Started:
    - Quick Start: getting-started/quick-start.md
    - Proxy Quick Start: getting-started/proxy-quick-start.md
  - User Guide:
    - API Reference: user-guide/api-reference.md
    - Proxy Wrapper: user-guide/proxy-wrapper.md
    - Security: user-guide/security.md
  - Developer Guide:
    - Architecture: developer-guide/architecture.md
    - Code Structure: developer-guide/code-structure.md
    - Development Setup: developer-guide/development-setup.md
    - Testing: developer-guide/testing.md
  - Reference:
    - Configuration: reference/configuration.md
    - Environment Variables: reference/environment-variables.md
    - Proxy API: reference/proxy-api.md
  - Monitoring:
    - Overview: monitoring/index.md
    - Production Setup: monitoring/production-setup.md
    - Telemetry: monitoring/telemetry.md
  - OAuth:
    - FastMCP Integration: oauth/fastmcp-integration.md
  - API:
    - API Reference: api/index.md

markdown_extensions:
  - admonition
  - codehilite
  - footnotes
  - meta
  - pymdownx.arithmatex:
      generic: true
  - pymdownx.betterem:
      smart_enable: all
  - pymdownx.caret
  - pymdownx.details
  - pymdownx.emoji:
      emoji_generator: !!python/name:materialx.emoji.to_svg
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.keys
  - pymdownx.magiclink
  - pymdownx.mark
  - pymdownx.smartsymbols
  - pymdownx.snippets:
      check_paths: true
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tabbed
  - pymdownx.tasklist:
      custom_checkbox: true
  - pymdownx.tilde
"""
            mkdocs_config.write_text(config_content)
            print("   Created: mkdocs.yml")

        print("✅ Documentation structure created")
        return 0


def main():
    """Test the documentation utilities."""
    project_root = Path(__file__).parent.parent
    docs_utils = DocsUtils(project_root)

    print("📚 Documentation Utilities Test")
    print("=" * 40)

    # Check dependencies
    dependencies = docs_utils.check_docs_dependencies()
    print("Dependencies:")
    for dep, available in dependencies.items():
        status_icon = "✅" if available else "❌"
        print(f"  {status_icon} {dep}")

    # Check docs structure
    docs_dir = project_root / "docs"
    mkdocs_config = project_root / "mkdocs.yml"

    print("\nDocumentation structure:")
    print(f"  {'✅' if docs_dir.exists() else '❌'} docs/ directory")
    print(f"  {'✅' if mkdocs_config.exists() else '❌'} mkdocs.yml")


if __name__ == "__main__":
    main()
