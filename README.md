# LLM Council

![llmcouncil](header.jpg)

The idea of this repo is that instead of asking a question to your favorite LLM provider, you can group multiple models into your "LLM Council". This is a simple, local web app that looks like ChatGPT except it uses the **GitHub Copilot SDK** to send your query to multiple LLMs, it then asks them to review and rank each other's work, and finally a Chairman LLM produces the final response.

> **Note:** This is a fork of [karpathy/llm-council](https://github.com/karpathy/llm-council) that replaces OpenRouter with the GitHub Copilot SDK, allowing you to use your existing Copilot subscription to access multiple LLMs.

In a bit more detail, here is what happens when you submit a query:

1. **Stage 1: First opinions**. The user query is given to all LLMs individually, and the responses are collected. The individual responses are shown in a "tab view", so that the user can inspect them all one by one.
2. **Stage 2: Review**. Each individual LLM is given the responses of the other LLMs. Under the hood, the LLM identities are anonymized so that the LLM can't play favorites when judging their outputs. The LLM is asked to rank them in accuracy and insight.
3. **Stage 3: Final response**. The designated Chairman of the LLM Council takes all of the model's responses and compiles them into a single final answer that is presented to the user.

## Features

- **Dynamic Model Discovery**: Available models are fetched from your Copilot subscription
- **Model Picker UI**: Configure which models participate in the council via the Settings panel
- **Error Handling**: Shows warnings when models fail, continues with successful responses
- **No API Keys Required**: Uses your existing GitHub Copilot authentication

## Prerequisites

### 1. GitHub Copilot Subscription

You need an active GitHub Copilot subscription (Individual, Business, or Enterprise).

### 2. Install the Copilot CLI

Follow the [Copilot CLI installation guide](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli) to install the CLI.

### 3. Authenticate

```bash
copilot -i "auth login"
```

This opens a browser window to authenticate with your GitHub account.

## Setup

### 1. Ensure Copilot CLI is up to date

The SDK requires a recent version of the Copilot CLI with protocol v2 support:

```bash
npm update -g @github/copilot
copilot --version  # Should be 0.0.390 or higher
```

### 2. Install Dependencies

**Option A: Using uv (recommended)**

```bash
uv sync
```

**Option B: Using pip + venv**

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install github-copilot-sdk fastapi "uvicorn[standard]" pydantic
```

**Frontend:**
```bash
cd frontend
npm install
cd ..
```

## Running the Application

**Option 1: Use the start script**
```bash
./start.sh
```

**Option 2: Run manually**

Terminal 1 (Backend):
```bash
# If using uv:
uv run python -m backend.main

# If using venv:
source .venv/bin/activate && python -m backend.main
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

Then open http://localhost:5173 in your browser.

## Configuration

Click the **⚙️ Settings** button in the sidebar to:
- Select which models participate in the council (Stage 1 & 2)
- Choose the chairman model (Stage 3)

Available models depend on your Copilot subscription. Common models include:
- `gpt-5` / `gpt-4.1`
- `claude-sonnet-4.5` / `claude-sonnet-4`
- `claude-haiku-4.5`

## Tech Stack

- **Backend:** FastAPI (Python 3.10+), GitHub Copilot SDK
- **Frontend:** React + Vite, react-markdown for rendering
- **Storage:** JSON files in `data/conversations/`
- **Package Management:** uv for Python, npm for JavaScript
