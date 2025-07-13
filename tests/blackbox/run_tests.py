#!/usr/bin/env python3
"""
Black Box Test Runner für MetaMCP

Führt Black Box Tests für den MetaMCP Container aus.
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path
from typing import List, Optional

import httpx
import pytest


def wait_for_service(base_url: str = "http://localhost:8000", max_retries: int = 30, delay: float = 2.0) -> bool:
    """Warten bis der MetaMCP Service bereit ist."""
    print(f"Warte auf MetaMCP Service auf {base_url}...")
    
    for i in range(max_retries):
        try:
            response = httpx.get(f"{base_url}/api/v1/health", timeout=5.0)
            if response.status_code == 200:
                print(f"Service ist bereit nach {i + 1} Versuchen")
                return True
        except Exception as e:
            print(f"Versuch {i + 1}/{max_retries}: {e}")
        
        if i < max_retries - 1:
            time.sleep(delay)
    
    print(f"Service nicht erreichbar nach {max_retries} Versuchen")
    return False


def run_pytest_tests(test_paths: List[str], verbose: bool = True, parallel: bool = False) -> int:
    """Führt pytest Tests aus."""
    pytest_args = []
    
    if verbose:
        pytest_args.append("-v")
    
    if parallel:
        pytest_args.extend(["-n", "auto"])
    
    # JUnit XML Report
    pytest_args.extend(["--junitxml", "blackbox-results.xml"])
    
    # Test-Pfade hinzufügen
    pytest_args.extend(test_paths)
    
    print(f"Führe Tests aus: pytest {' '.join(pytest_args)}")
    
    # pytest.main() gibt Exit-Code zurück
    return pytest.main(pytest_args)


def get_test_categories() -> dict:
    """Gibt verfügbare Test-Kategorien zurück."""
    base_path = Path(__file__).parent
    
    categories = {
        "all": str(base_path),
        "rest_api": str(base_path / "rest_api"),
        "mcp_api": str(base_path / "mcp_api"),
        "integration": str(base_path / "integration"),
        "performance": str(base_path / "performance"),
        "auth": str(base_path / "rest_api" / "test_auth.py"),
        "tools": str(base_path / "rest_api" / "test_tools.py"),
        "health": str(base_path / "rest_api" / "test_health.py"),
        "protocol": str(base_path / "mcp_api" / "test_protocol.py"),
        "workflows": str(base_path / "integration" / "test_workflows.py"),
        "load": str(base_path / "performance" / "test_load.py"),
    }
    
    return categories


def main():
    """Hauptfunktion für Test-Ausführung."""
    parser = argparse.ArgumentParser(description="Black Box Test Runner für MetaMCP")
    
    parser.add_argument(
        "categories",
        nargs="*",
        default=["all"],
        help="Test-Kategorien (all, rest_api, mcp_api, integration, performance, auth, tools, health, protocol, workflows, load)"
    )
    
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="MetaMCP Service URL (Standard: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Nicht auf Service warten"
    )
    
    parser.add_argument(
        "--max-retries",
        type=int,
        default=30,
        help="Maximale Warte-Versuche (Standard: 30)"
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Verzögerung zwischen Versuchen in Sekunden (Standard: 2.0)"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduzierte Ausgabe"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Parallele Test-Ausführung"
    )
    
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="Liste verfügbare Test-Kategorien"
    )
    
    args = parser.parse_args()
    
    # Verfügbare Kategorien anzeigen
    if args.list_categories:
        categories = get_test_categories()
        print("Verfügbare Test-Kategorien:")
        for name, path in categories.items():
            print(f"  {name}: {path}")
        return 0
    
    # Test-Kategorien validieren
    available_categories = get_test_categories()
    test_paths = []
    
    for category in args.categories:
        if category not in available_categories:
            print(f"Fehler: Unbekannte Test-Kategorie '{category}'")
            print(f"Verfügbare Kategorien: {', '.join(available_categories.keys())}")
            return 1
        
        test_paths.append(available_categories[category])
    
    # Service-Verfügbarkeit prüfen
    if not args.no_wait:
        if not wait_for_service(args.base_url, args.max_retries, args.delay):
            print("Fehler: MetaMCP Service nicht erreichbar")
            return 1
    
    # Tests ausführen
    verbose = not args.quiet
    exit_code = run_pytest_tests(test_paths, verbose, args.parallel)
    
    if exit_code == 0:
        print("Alle Tests erfolgreich!")
    else:
        print(f"Tests fehlgeschlagen mit Exit-Code {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main()) 