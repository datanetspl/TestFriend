# Technology Stack

## Core Technologies
- **Python 3.6+**: Primary language with standard library dependencies
- **AST Module**: For parsing Python code and extracting function signatures
- **HTTP Server**: Built-in `http.server` for web interface
- **Threading**: For concurrent operations and web server management

## Key Libraries
- **Standard Library**: `ast`, `inspect`, `importlib`, `json`, `threading`, `webbrowser`
- **Optional Dependencies**:
  - `requests`: For OpenAI API integration (LLM features)
  - `torch`: For PyTorch neural network examples in sample functions
- **Web Technologies**: Pure HTML/CSS/JavaScript (no external frameworks)

## Architecture Patterns
- **Modular Design**: Separate modules for core testing (`function_tester.py`), web interface (`web_interface.py`), and document processing (`.pageindex/`)
- **Class-Based Structure**: Main functionality encapsulated in `FunctionTester` class
- **Async/Await**: Used in page indexing system for concurrent API calls
- **RESTful API**: Web interface uses JSON API endpoints for function testing

## Configuration
- **YAML Config**: `.pageindex/config.yaml` for document processing settings
- **Environment Variables**: `OPENAI_API_KEY` for LLM integration
- **Command Line Arguments**: Extensive CLI options for different modes and settings

## Common Commands

### Basic Usage
```bash
# Terminal interface (default)
python function_tester.py

# Specify target directory
python function_tester.py --directory /path/to/code

# Web interface
python function_tester.py --web
python web_interface.py  # Alternative standalone web server
```

### With LLM Integration
```bash
# Using API key argument
python function_tester.py --api-key your_openai_api_key

# Using environment variable
export OPENAI_API_KEY=your_key_here
python function_tester.py

# Web interface with LLM
python function_tester.py --web --api-key your_key
```

### Advanced Options
```bash
# Custom web port
python function_tester.py --web --port 9000

# Batch testing mode
python function_tester.py --batch

# Debug mode
python function_tester.py --debug
```

## Development Setup
```bash
# Install optional dependencies
pip install requests torch

# Run sample functions
python sample_functions.py

# Test web interface locally
python web_interface.py
```