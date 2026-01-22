"""Configuration for the LLM Council."""

# Default council members - list of Copilot SDK model identifiers
# These will be validated against available models at startup
DEFAULT_COUNCIL_MODELS = [
    "gpt-5",
    "claude-sonnet-4.5",
    "claude-sonnet-4",
    "claude-haiku-4.5",
]

# Default chairman model - synthesizes final response
DEFAULT_CHAIRMAN_MODEL = "gpt-5"

# Data directory for conversation storage
DATA_DIR = "data/conversations"

# Settings file path
SETTINGS_FILE = "data/settings.json"
