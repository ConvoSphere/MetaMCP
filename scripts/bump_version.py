#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "package_init": ROOT / "metamcp" / "__init__.py",
    "pyproject": ROOT / "pyproject.toml",
    "k8s_deployment": ROOT / "k8s" / "deployment.yaml",
    "compose": ROOT / "docker-compose.yml",
}

VERSION_PATTERN_INIT = re.compile(r'__version__\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"')
VERSION_PATTERN_PYPROJECT = re.compile(
    r'^version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"', re.MULTILINE
)
VERSION_PATTERN_K8S = re.compile(r"version:\s*v([0-9]+\.[0-9]+\.[0-9]+)")
VERSION_PATTERN_COMPOSE = re.compile(r"APP_VERSION=([0-9]+\.[0-9]+\.[0-9]+)")


def read_version() -> str:
    content = FILES["package_init"].read_text(encoding="utf-8")
    m = VERSION_PATTERN_INIT.search(content)
    if not m:
        raise RuntimeError("Version not found in __init__.py")
    return m.group(1)


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    print(f"Updated {path}")


def bump(version: str, part: str) -> str:
    major, minor, patch = map(int, version.split("."))
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def replace_version_in_text(
    text: str, pattern: re.Pattern, new: str, repl_fmt: str
) -> str:
    def _repl(m: re.Match) -> str:
        return repl_fmt.format(old=m.group(1), new=new)

    return pattern.sub(_repl, text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bump project version across files")
    parser.add_argument(
        "part", choices=["major", "minor", "patch"], help="Which part to bump"
    )
    args = parser.parse_args()

    current = read_version()
    new_version = bump(current, args.part)

    # __init__.py
    init_text = FILES["package_init"].read_text(encoding="utf-8")
    init_text = re.sub(
        r'(__version__\s*=\s*")([0-9]+\.[0-9]+\.[0-9]+)(")',
        rf"\\g<1>{new_version}\\g<3>",
        init_text,
    )
    write_file(FILES["package_init"], init_text)

    # pyproject.toml
    py_text = FILES["pyproject"].read_text(encoding="utf-8")
    py_text = re.sub(
        r'(^version\s*=\s*")[0-9]+\.[0-9]+\.[0-9]+("\s*$)',
        rf"\\g<1>{new_version}\\g<2>",
        py_text,
        flags=re.MULTILINE,
    )
    write_file(FILES["pyproject"], py_text)

    # k8s deployment labels
    k8s_text = FILES["k8s_deployment"].read_text(encoding="utf-8")
    k8s_text = replace_version_in_text(
        k8s_text, VERSION_PATTERN_K8S, new_version, "version: v{new}"
    )
    write_file(FILES["k8s_deployment"], k8s_text)

    # docker-compose env
    compose_text = FILES["compose"].read_text(encoding="utf-8")
    compose_text = replace_version_in_text(
        compose_text, VERSION_PATTERN_COMPOSE, new_version, "APP_VERSION={new}"
    )
    write_file(FILES["compose"], compose_text)

    print(f"Bumped version: {current} -> {new_version}")


if __name__ == "__main__":
    main()
