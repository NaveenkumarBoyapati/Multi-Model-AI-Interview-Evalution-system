"""
Environment Variable Loader for AI Interview Evaluation System.

Loads environment variables from:
1. Workspace root `.env`
2. Backend directory `.env`
3. System / process environment variables

Supports comments (#), quoted values, and whitespace trimming.
Does not overwrite pre-existing system environment variables unless override=True.
"""

import os
from typing import Dict, Optional


def load_env(override: bool = False) -> Dict[str, str]:
    """
    Finds and parses .env files, setting them in os.environ.
    Returns the dictionary of loaded variables.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(current_dir)

    candidate_files = [
        os.path.join(workspace_root, ".env"),
        os.path.join(current_dir, ".env"),
    ]

    loaded_vars: Dict[str, str] = {}

    for env_path in candidate_files:
        if not os.path.isfile(env_path):
            continue

        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        continue

                    if "=" not in stripped:
                        continue

                    key, val = stripped.split("=", 1)
                    key = key.strip()
                    val = val.strip()

                    # Handle surrounding quotes
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    else:
                        # Strip inline comment if unquoted
                        if " #" in val:
                            val = val.split(" #", 1)[0].strip()

                    loaded_vars[key] = val
                    if override or key not in os.environ:
                        os.environ[key] = val
        except Exception as exc:
            print(f"[EnvLoader Warning] Failed reading {env_path}: {exc}")

    return loaded_vars


# Auto-load on import
load_env()
