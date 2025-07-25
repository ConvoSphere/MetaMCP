#!/usr/bin/env python3
"""
Docker Utilities for MetaMCP

This module provides Docker-related utilities for the MetaMCP project.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any


class DockerUtils:
    """Docker utilities for MetaMCP project management."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

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

    def check_docker_available(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def check_docker_compose_available(self) -> bool:
        """Check if Docker Compose is available."""
        try:
            result = subprocess.run(
                ["docker", "compose", "version"], capture_output=True, text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def get_container_status(self) -> dict[str, Any]:
        """Get detailed container status."""
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode == 0:
                containers = []
                for line in result.stdout.strip().split("\n"):
                    if line:
                        containers.append(line)
                return {"containers": containers, "running": True}
            else:
                return {"containers": [], "running": False}
        except Exception as e:
            return {"containers": [], "running": False, "error": str(e)}

    def get_container_logs(self, service: str | None = None, lines: int = 50) -> str:
        """Get container logs."""
        cmd = ["docker", "compose", "logs", f"--tail={lines}"]
        if service:
            cmd.append(service)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.project_root
            )
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"Error getting logs: {e}"

    def get_container_stats(self) -> str:
        """Get container resource usage statistics."""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "stats",
                    "--no-stream",
                    "--format",
                    "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}",
                ],
                capture_output=True,
                text=True,
            )
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"Error getting stats: {e}"

    def build_containers(
        self, service: str | None = None, no_cache: bool = False
    ) -> int:
        """Build Docker containers."""
        cmd = ["docker", "compose", "build"]
        if no_cache:
            cmd.append("--no-cache")
        if service:
            cmd.append(service)

        return self.run_command(cmd)

    def start_containers(self, service: str | None = None) -> int:
        """Start Docker containers."""
        cmd = ["docker", "compose", "up", "-d"]
        if service:
            cmd.append(service)

        return self.run_command(cmd)

    def stop_containers(self, service: str | None = None) -> int:
        """Stop Docker containers."""
        cmd = ["docker", "compose", "down"]
        if service:
            cmd = ["docker", "compose", "stop", service]

        return self.run_command(cmd)

    def restart_containers(self, service: str | None = None) -> int:
        """Restart Docker containers."""
        cmd = ["docker", "compose", "restart"]
        if service:
            cmd.append(service)

        return self.run_command(cmd)

    def pull_images(self) -> int:
        """Pull latest Docker images."""
        return self.run_command(["docker", "compose", "pull"])

    def clean_containers(self) -> int:
        """Clean up stopped containers and unused images."""
        print("🧹 Cleaning up Docker resources...")

        # Remove stopped containers
        self.run_command(["docker", "container", "prune", "-f"])

        # Remove unused images
        self.run_command(["docker", "image", "prune", "-f"])

        # Remove unused networks
        self.run_command(["docker", "network", "prune", "-f"])

        # Remove unused volumes
        self.run_command(["docker", "volume", "prune", "-f"])

        print("✅ Docker cleanup complete")
        return 0

    def check_services_health(self) -> dict[str, bool]:
        """Check health of all services."""
        health_status = {}

        services = [
            ("metamcp-server", "http://localhost:9000/health"),
            ("postgres", "docker compose exec postgres pg_isready -U metamcp"),
            ("redis", "docker compose exec redis redis-cli ping"),
            ("opa", "http://localhost:8181/health"),
            ("weaviate", "http://localhost:9088/v1/meta"),
            ("grafana", "http://localhost:3000/api/health"),
            ("prometheus", "http://localhost:9090/-/healthy"),
        ]

        for service_name, health_check in services:
            try:
                if health_check.startswith("http"):
                    # HTTP health check
                    import requests

                    response = requests.get(health_check, timeout=5)
                    health_status[service_name] = response.status_code == 200
                else:
                    # Command health check
                    result = subprocess.run(
                        health_check.split(),
                        capture_output=True,
                        text=True,
                        cwd=self.project_root,
                    )
                    health_status[service_name] = result.returncode == 0
            except Exception:
                health_status[service_name] = False

        return health_status


def main():
    """Test the Docker utilities."""
    project_root = Path(__file__).parent.parent
    docker_utils = DockerUtils(project_root)

    print("🐳 Docker Utilities Test")
    print("=" * 40)

    # Check Docker availability
    print(f"Docker available: {docker_utils.check_docker_available()}")
    print(f"Docker Compose available: {docker_utils.check_docker_compose_available()}")

    # Get container status
    status = docker_utils.get_container_status()
    print(f"Containers running: {status['running']}")

    # Check service health
    health = docker_utils.check_services_health()
    print("\nService Health:")
    for service, healthy in health.items():
        status_icon = "✅" if healthy else "❌"
        print(f"  {status_icon} {service}")


if __name__ == "__main__":
    main()
