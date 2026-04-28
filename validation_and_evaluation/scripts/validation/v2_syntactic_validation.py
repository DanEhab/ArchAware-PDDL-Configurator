"""
Stage V2: Syntactic Validation (VAL Tool)
==========================================
Validates a PDDL domain against a problem instance using the VAL
(Plan Validator) tool, containerised via Docker.

Based on Eli's validity.py, adapted for the ArchAware pipeline.

Docker command:
  docker run --rm -v /path:/pddl val_validator /pddl/domain.pddl /pddl/problem.pddl

Pass: exit code = 0
Fail: exit code != 0 -> REJECTED with reason 'syntactic_error'

Cross-platform notes:
  - On Windows (testing): Docker Desktop must be running, or use --skip-docker
  - On macOS/iMac (production): Docker runs natively
"""

import subprocess
import uuid
import platform
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ValResult:
    """Result of VAL syntactic validation."""
    is_valid: bool
    exit_code: int
    stdout: str
    stderr: str


def check_docker_available() -> bool:
    """Check if Docker is installed and running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def validate_with_val(
    domain_pddl_str: str,
    problem_file_path: str,
    docker_image: str = "val_validator",
    timeout: int = 60,
) -> ValResult:
    """
    Validate a PDDL domain string against a problem file using the
    VAL tool inside a Docker container.

    Args:
        domain_pddl_str: The PDDL domain content as a string.
        problem_file_path: Absolute path to a problem instance file.
        docker_image: Name of the Docker image containing VAL.
        timeout: Maximum seconds to wait for Docker.

    Returns:
        ValResult with validation outcome, exit code, and output.
    """
    tmp_domain_path = None
    try:
        problem_path = Path(problem_file_path).resolve()
        if not problem_path.exists():
            return ValResult(
                is_valid=False,
                exit_code=-1,
                stdout="",
                stderr=f"Problem file not found: {problem_path}",
            )

        # Write domain to a temporary file in the same directory as the problem
        mount_dir = problem_path.parent
        domain_filename = f"domain_val_tmp_{uuid.uuid4().hex[:8]}.pddl"
        tmp_domain_path = mount_dir / domain_filename

        with open(tmp_domain_path, "w", encoding="utf-8") as f:
            f.write(domain_pddl_str)

        # Build Docker command
        # On Windows, paths need forward slashes for Docker volume mounts
        mount_str = str(mount_dir)
        if platform.system() == "Windows":
            # Convert Windows path to Docker-compatible format
            # e.g., D:\path\to\dir -> /d/path/to/dir
            mount_str = "/" + mount_str.replace("\\", "/").replace(":", "")

        cmd = [
            "docker", "run", "--rm",
            "-v", f"{mount_str}:/pddl",
            docker_image,
            f"/pddl/{domain_filename}",
            f"/pddl/{problem_path.name}",
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )

        return ValResult(
            is_valid=(result.returncode == 0),
            exit_code=result.returncode,
            stdout=result.stdout.decode("utf-8", errors="replace"),
            stderr=result.stderr.decode("utf-8", errors="replace"),
        )

    except FileNotFoundError:
        return ValResult(
            is_valid=False,
            exit_code=-1,
            stdout="",
            stderr="Docker not found. Install Docker or use --skip-docker.",
        )
    except subprocess.TimeoutExpired:
        return ValResult(
            is_valid=False,
            exit_code=-2,
            stdout="",
            stderr=f"VAL validation timed out after {timeout}s.",
        )
    except Exception as e:
        return ValResult(
            is_valid=False,
            exit_code=-3,
            stdout="",
            stderr=f"VAL validation error: {e}",
        )
    finally:
        # Clean up temporary domain file
        if tmp_domain_path and tmp_domain_path.exists():
            try:
                tmp_domain_path.unlink()
            except OSError:
                pass
