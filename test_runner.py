"""test_runner.py

Simple test runner for ADK InMemoryRunner.

This script:
- loads a local `.env` (via python-dotenv if available) into the process
  environment before initializing the ADK runner;
- lazily initializes the runner via `adk_setup.ensure_runner()`;
- runs a single debug query and prints a concise text response (no raw repr).
"""

import asyncio
import os
from typing import Any, Optional
"""Minimal test runner for ADK InMemoryRunner.

This script:
- loads a local `.env` (via python-dotenv if available) into the process
  environment before initializing the ADK runner;
- lazily initializes the runner via `adk_setup.ensure_runner()`;
- runs a single debug query and prints a concise text response (no raw repr).
"""

import asyncio
import os
from typing import Any, Optional

# Load .env if present (prefer python-dotenv)
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and os.getenv(k) is None:
                        os.environ[k] = v
        except Exception:
            pass

import adk_setup


def extract_text_from_response(resp: Any) -> Optional[str]:
    """Extract readable text from common ADK response shapes."""
    try:
        content = getattr(resp, "content", None)
        if content is not None:
            parts = getattr(content, "parts", None)
            if parts and len(parts) > 0:
                part0 = parts[0]
                if hasattr(part0, "text"):
                    return getattr(part0, "text")
    except Exception:
        pass

    for attr in ("text", "output", "message", "result"):
        try:
            if hasattr(resp, attr):
                val = getattr(resp, attr)
                if isinstance(val, str):
                    return val
                if isinstance(val, (list, tuple)):
                    return "\n".join(map(str, val))
        except Exception:
            continue

    return None


async def main() -> None:
    try:
        runner: Any = adk_setup.ensure_runner()
    except Exception as e:
        print("⚠️ Failed to initialize ADK runner:", e)
        raise SystemExit(2)

    query = "What's the weather in Bengaluru?"
    print(f"Running debug call: {query!r}")

    try:
        response = await runner.run_debug(query)
    except Exception as e:
        print(f"🚨 Error while running runner.run_debug: {e}")
        raise

    text = extract_text_from_response(response)
    if text:
        print("\n--- Response ---")
        print(text)
    else:
        print("No textual output available from the response.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user")
        raise SystemExit(1)
    except Exception as e:
        # Print unexpected errors and exit with non-zero code so CI/automation can detect failure.
        print("Unhandled error while running test_runner:", e)
        raise SystemExit(2)
