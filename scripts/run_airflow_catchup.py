from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.airflow.yml"


def run(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    command = ["docker", "compose", "-f", str(COMPOSE_FILE), *arguments]
    print(f"+ {' '.join(command)}", flush=True)
    return subprocess.run(command, cwd=PROJECT_ROOT, check=check, text=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run and verify bounded Airflow catchup")
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Stop the Airflow stack and remove its volumes after verification",
    )
    args = parser.parse_args()

    try:
        run("up", "airflow-init", "--abort-on-container-exit", "--exit-code-from", "airflow-init")
        run("up", "-d", "--wait", "airflow-scheduler", "airflow-webserver")
        run(
            "exec",
            "-T",
            "airflow-scheduler",
            "airflow",
            "dags",
            "unpause",
            "financial_dwh_pipeline",
        )
        run(
            "exec",
            "-T",
            "airflow-scheduler",
            "python",
            "/opt/airflow/project/scripts/check_airflow_catchup.py",
        )
        print("airflow_webserver=http://localhost:8080")
    finally:
        if args.cleanup:
            run("down", "--volumes", check=False)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from error
