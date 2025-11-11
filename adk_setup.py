"""adk_setup.py

ADK/Agent helper file with guarded imports and a helper to get the ADK proxy URL
for Kaggle Notebooks. This module is safe to import in non-Kaggle environments; it
will print helpful messages if required packages are missing.
"""

from typing import Optional

# Guard ADK imports so the file can be imported outside Kaggle without failing immediately.
try:
    from google.adk.agents import Agent
    from google.adk.runners import InMemoryRunner
    from google.adk.tools import google_search
    from google.genai import types
    ADK_AVAILABLE = True
except Exception as e:  # pragma: no cover - best-effort import
    Agent = None
    InMemoryRunner = None
    google_search = None
    types = None
    ADK_AVAILABLE = False
    _adk_import_error = e


print("✅ ADK components imported successfully." if ADK_AVAILABLE else "⚠️ ADK components unavailable. Install the ADK packages to use agents.")

# Notebook-only imports (guarded)
try:
    from IPython.core.display import display, HTML
    from jupyter_server.serverapp import list_running_servers
    NOTEBOOK_ENV = True
except Exception:
    # Not running inside a Jupyter server / Kaggle environment
    display = None
    HTML = None
    list_running_servers = None
    NOTEBOOK_ENV = False


def get_adk_proxy_url() -> str:
    """Return the proxied ADK UI URL prefix used in Kaggle notebooks and display a warning box.

    This function attempts to read the running jupyter server base_url and builds the
    Kaggle proxy URL used to reach the ADK web UI running on a proxied port.

    Returns:
        url_prefix (str): the path prefix part used by Kaggle proxy, e.g. '/k/<kernel>/<token>/proxy/proxy/8000'

    Raises:
        RuntimeError if called outside a notebook or the base URL can't be parsed.
    """
    if not NOTEBOOK_ENV or list_running_servers is None:
        raise RuntimeError("get_adk_proxy_url() requires a Jupyter notebook / server environment (Kaggle).")

    PROXY_HOST = "https://kkb-production.jupyter-proxy.kaggle.net"
    ADK_PORT = "8000"

    servers = list(list_running_servers())
    if not servers:
        raise RuntimeError("No running Jupyter servers found.")

    baseURL = servers[0].get("base_url", "")
    if not baseURL:
        raise RuntimeError("No base_url found for running Jupyter server.")

    # Attempt to parse kernel and token from the base URL. The Kaggle base_url often takes the
    # form '/user/<kernel>/<token>/...' but this can vary, so be defensive.
    path_parts = [p for p in baseURL.split("/") if p]
    try:
        # The user's snippet expected kernel at index 2 and token at index 3 (0-based when empty parts removed)
        kernel = path_parts[2]
        token = path_parts[3]
    except Exception as ex:
        raise RuntimeError(f"Could not parse kernel/token from base URL: {baseURL}") from ex

    url_prefix = f"/k/{kernel}/{token}/proxy/proxy/{ADK_PORT}"
    url = f"{PROXY_HOST}{url_prefix}"

    # Create a styled HTML box guiding the user to start the ADK web UI
    if display is not None and HTML is not None:
        styled_html = f"""
    <div style="padding: 15px; border: 2px solid #f0ad4e; border-radius: 8px; background-color: #fef9f0; margin: 20px 0;">
        <div style="font-family: sans-serif; margin-bottom: 12px; color: #333; font-size: 1.1em;">
            <strong>⚠️ IMPORTANT: Action Required</strong>
        </div>
        <div style="font-family: sans-serif; margin-bottom: 15px; color: #333; line-height: 1.5;">
            The ADK web UI is <strong>not running yet</strong>. You must start it in the next cell.
            <ol style="margin-top: 10px; padding-left: 20px;">
                <li style="margin-bottom: 5px;"><strong>Run the next cell</strong> (the one with <code>!adk web ...</code>) to start the ADK web UI.</li>
                <li style="margin-bottom: 5px;">Wait for that cell to show it is "Running" (it will not "complete").</li>
                <li>Once it's running, <strong>return to this button</strong> and click it to open the UI.</li>
            </ol>
            <em style="font-size: 0.9em; color: #555;">(If you click the button before running the next cell, you will get a 500 error.)</em>
        </div>
        <a href='{url}' target='_blank' style="
            display: inline-block; background-color: #1a73e8; color: white; padding: 10px 20px;
            text-decoration: none; border-radius: 25px; font-family: sans-serif; font-weight: 500;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2); transition: all 0.2s ease;">
            Open ADK Web UI (after running cell below) ↗
        </a>
    </div>
    """
        display(HTML(styled_html))

    return url_prefix


print("✅ Helper functions defined.")


# Lazy creation: expose functions to create the Agent and Runner at runtime.
# This avoids import-time initialization which may fail if credentials are not
# yet available in the environment.
root_agent = None
runner = None


def create_agent_and_runner(model: str = "gemini-2.5-flash-lite", *, name: str = "helpful_assistant",
                            description: str = "A simple agent that can answer general questions.",
                            instruction: str = "You are a helpful assistant. Use Google Search for current info or if unsure.",
                            tools: Optional[list] = None):
    """Create and return (agent, runner).

    This function attempts to create an Agent and InMemoryRunner using the ADK
    classes imported earlier. It raises RuntimeError with helpful messages if
    the ADK packages are not available or creation fails (for example missing
    credentials).
    """
    global root_agent, runner

    if not ADK_AVAILABLE or Agent is None or InMemoryRunner is None:
        raise RuntimeError("ADK packages are not available; install the ADK and google.genai packages first.")

    if tools is None:
        # default to google_search if available
        tools = [google_search] if google_search is not None else []

    try:
        agent = Agent(
            name=name,
            model=model,
            description=description,
            instruction=instruction,
            tools=tools,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to create Agent: {e}") from e

    try:
        runner_local = InMemoryRunner(agent=agent)
    except Exception as e:
        raise RuntimeError(f"Failed to create InMemoryRunner: {e}") from e

    root_agent = agent
    runner = runner_local
    return agent, runner


def ensure_runner() -> object:
    """Ensure `runner` exists and return it.

    If the runner was already created, returns it. Otherwise attempts to create
    the agent/runner using environment configuration (no hardcoded keys).
    """
    global runner
    if runner is not None:
        return runner

    # Create runner using defaults. This will pick up credentials from the
    # environment (e.g., GOOGLE_API_KEY or Vertex AI settings) as required by
    # the ADK/genai client.
    create_agent_and_runner()
    return runner
