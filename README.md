# AI Agent

Small demo workspace to load credentials from `.env`, create a Google ADK/GenAI Agent and run a local debug harness.

Files of interest

- `setup_gemini.py` — helper to load `.env` and optionally fetch Kaggle secrets.
- `adk_setup.py` — guarded ADK imports and lazy `ensure_runner()` helper.
- `test_runner.py` — runnable test harness that calls `runner.run_debug(...)` and prints concise text.

Quick start

1. Create a `.env` file in the repository root with your credentials, for example:

   ```env
   GOOGLE_API_KEY=your_api_key_here
   # or for Vertex AI:
   # GOOGLE_GENAI_USE_VERTEXAI=true
   # GOOGLE_CLOUD_PROJECT=your-project
   # GOOGLE_CLOUD_LOCATION=your-location
   ```

2. Install Python dependencies:

   ```powershell
   python -m pip install -r .\requirements.txt
   ```

3. Run the test harness:

   ```powershell
   python .\test_runner.py
   ```

Follow the instructions in this repository to initialize git and push to a GitHub repository. See the project root for `.gitignore` and `LICENSE` files.
