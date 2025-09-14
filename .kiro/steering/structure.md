# Project Structure

## Root Directory Layout
```
├── function_tester.py      # Main CLI application and core testing logic
├── web_interface.py        # Standalone web server interface
├── sample_functions.py     # Comprehensive test functions and classes
├── eda.ipynb              # Jupyter notebook for exploratory data analysis
├── README.md              # Comprehensive project documentation
├── .pageindex/            # Document processing subsystem
│   ├── config.yaml        # Configuration for document processing
│   ├── page_index.py      # Core document indexing logic
│   ├── page_index_md.py   # Markdown-specific processing
│   ├── utils.py           # Utility functions for document processing
│   └── __init__.py        # Package initialization
├── .git/                  # Git version control
├── .kiro/                 # Kiro IDE configuration and steering
└── __pycache__/           # Python bytecode cache
```

## Core Module Organization

### Main Application (`function_tester.py`)
- **FunctionTester Class**: Central orchestrator for all testing functionality
- **Function Discovery**: AST-based parsing and importlib dynamic loading
- **Input Generation**: LLM integration with rule-based fallbacks
- **Class Instance Handling**: Interactive and automatic class instantiation
- **Test Execution**: Safe function calling with error handling
- **Result Tracking**: Comprehensive test result logging and verification

### Web Interface (`web_interface.py`)
- **WebTestingHandler**: HTTP request handler extending BaseHTTPRequestHandler
- **RESTful Endpoints**: JSON API for function testing operations
- **Static HTML Template**: Embedded responsive web interface
- **Real-time Testing**: AJAX-based function execution and result display

### Sample Functions (`sample_functions.py`)
- **Basic Functions**: Mathematical operations, string processing, utility functions
- **Class Definitions**: Person, Rectangle, BankAccount with methods
- **Advanced Classes**: Calculator, StringProcessor, BankAccountAdvanced with static/class methods
- **PyTorch Components**: Neural network encoder/decoder examples
- **Test Cases**: Comprehensive examples for different parameter types

### Document Processing (`.pageindex/`)
- **page_index.py**: Main document processing engine with TOC extraction
- **page_index_md.py**: Markdown-specific document handling
- **utils.py**: Shared utilities for text processing and API calls
- **config.yaml**: Configuration for LLM models and processing parameters

## Naming Conventions
- **Files**: Snake_case for Python modules (`function_tester.py`)
- **Classes**: PascalCase (`FunctionTester`, `WebTestingHandler`)
- **Functions**: Snake_case (`discover_functions`, `generate_inputs`)
- **Variables**: Snake_case (`selected_function`, `test_results`)
- **Constants**: UPPER_SNAKE_CASE (in config files)

## Code Organization Patterns
- **Single Responsibility**: Each module has a clear, focused purpose
- **Dependency Injection**: API keys and configuration passed as parameters
- **Error Handling**: Graceful degradation when optional dependencies unavailable
- **Async Support**: Document processing uses async/await for concurrent operations
- **Modular Testing**: Sample functions organized by complexity and use case

## File Relationships
- `function_tester.py` → Core engine, can be imported or run standalone
- `web_interface.py` → Imports and wraps `FunctionTester` for web access
- `sample_functions.py` → Test target for both CLI and web interfaces
- `.pageindex/` → Independent subsystem for document processing
- `eda.ipynb` → Analysis notebook (currently empty template)

## Extension Points
- **New Input Generators**: Add methods to `FunctionTester` class
- **Additional Interfaces**: Create new handlers similar to `WebTestingHandler`
- **Custom Test Cases**: Extend `sample_functions.py` with domain-specific examples
- **Document Processors**: Add new modules to `.pageindex/` for different formats