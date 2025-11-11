"""setup_gemini.py

Helper to load the Gemini/Google API key from Kaggle secrets and set
the environment variables used by downstream code.

This file implements a safe, non-leaking helper and a tiny CLI so you
can run it in-place in your workspace.
"""

import os
from typing import Optional

try:
    # Optional Kaggle support if running in Kaggle notebooks
    from kaggle_secrets import UserSecretsClient  # type: ignore
except Exception:
    UserSecretsClient = None

try:
    # dotenv is optional; for local development we prefer python-dotenv
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None


def load_env_from_dotenv(dotenv_path: Optional[str] = None) -> bool:
    """Load environment variables from a .env file.

    If `dotenv_path` is None, will try to load a file named `.env` in CWD.
    Returns True on success (GOOGLE_API_KEY found), False otherwise.
    """
    if load_dotenv is None:
        print("⚠️ python-dotenv is not installed. Install with: pip install python-dotenv")
        return False

    # Load variables from the .env file into the environment (does not overwrite existing vars by default)
    load_dotenv(dotenv_path)
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        print("🔑 GOOGLE_API_KEY not found in .env or environment.")
        return False

    # Ensure the env var is set for downstream code
    os.environ["GOOGLE_API_KEY"] = key
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")
    print("✅ Loaded .env and set required environment variables.")
    return True


def setup_gemini_api_key_from_kaggle(use_vertex_ai: bool = False, secret_name: str = "GOOGLE_API_KEY") -> bool:
    """Load secret from Kaggle secrets (if available) and set environment variables.

    Returns True on success, False on failure or if Kaggle environment isn't detected.
    """
    if UserSecretsClient is None:
        print("⚠️ Kaggle environment not detected: 'kaggle_secrets' is unavailable.")
        return False

    try:
        usc = UserSecretsClient()
        key = usc.get_secret(secret_name)
        if not key:
            print(f"🔑 Secret '{secret_name}' not found or empty in Kaggle secrets.")
            return False

        os.environ["GOOGLE_API_KEY"] = key
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE" if use_vertex_ai else "FALSE"
        print(f"✅ Gemini API key setup complete (Vertex AI: {'enabled' if use_vertex_ai else 'disabled'}).")
        return True
    except Exception:
        print("🔑 Authentication Error: Please make sure you have added 'GOOGLE_API_KEY' to your Kaggle secrets.")
        return False


def setup_gemini_api_key(use_dotenv: bool = True, dotenv_path: Optional[str] = None, *,
                         use_vertex_ai: bool = False, kaggle_secret_name: str = "GOOGLE_API_KEY") -> bool:
    """High-level helper:

    - If `use_dotenv` is True (default), attempt to load from .env first.
    - Otherwise, or if .env loading fails, will try Kaggle secrets when available.

    Returns True if any method succeeds.
    """
    if use_dotenv:
        ok = load_env_from_dotenv(dotenv_path)
        if ok:
            # Ensure Vertex flag is set if requested (overrides .env value)
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE" if use_vertex_ai else os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")
            return True

    # Fallback to Kaggle method
    return setup_gemini_api_key_from_kaggle(use_vertex_ai=use_vertex_ai, secret_name=kaggle_secret_name)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Setup Gemini API key from .env or Kaggle secrets.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dotenv", dest="use_dotenv", action="store_true", help="Load API key from a .env file (default).")
    group.add_argument("--no-dotenv", dest="use_dotenv", action="store_false", help="Do not try .env; use Kaggle secrets instead.")
    parser.set_defaults(use_dotenv=True)

    parser.add_argument("--dotenv-path", default=None, help="Path to .env file (optional).")
    parser.add_argument("--vertex", action="store_true", help="Enable Vertex AI mode (sets GOOGLE_GENAI_USE_VERTEXAI=TRUE).")
    parser.add_argument("--secret-name", default="GOOGLE_API_KEY", help="Kaggle secret name (default GOOGLE_API_KEY).")
    args = parser.parse_args()

    ok = setup_gemini_api_key(use_dotenv=args.use_dotenv, dotenv_path=args.dotenv_path,
                              use_vertex_ai=args.vertex, kaggle_secret_name=args.secret_name)
    raise SystemExit(0 if ok else 2)
