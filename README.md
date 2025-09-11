# Python Function Testing Tool

An interactive tool to automatically discover and test Python functions in your codebase.

## Features

- **Dual Interface**: Terminal and modern web interface options
- Automatically discovers all public functions in Python files
- Interactive function selection with visual feedback
- **LLM-powered intelligent input generation** with OpenAI API integration
- **Enhanced rule-based input generation** for common parameter patterns
- Dynamic input prompting with smart suggestions
- Handles default parameters
- Multiple testing modes: manual, auto-generate, and batch testing
- Real-time function execution and result display
- Manual verification of expected outputs
- Responsive web design for desktop and mobile

## Usage

### Terminal Interface (Default)
```bash
# Basic usage
python function_tester.py

# Specify directory
python function_tester.py --directory /path/to/your/code

# With LLM-powered input generation
python function_tester.py --api-key your_openai_api_key
```

### Web Interface
```bash
# Launch web interface
python function_tester.py --web

# Web interface with custom port
python function_tester.py --web --port 9000

# Web interface with LLM support
python function_tester.py --web --api-key your_openai_api_key

# Or use the standalone web interface
python web_interface.py
```

## How It Works

1. **Discovery**: Scans Python files in the specified directory for function definitions
2. **Selection**: Presents a numbered list of discovered functions
3. **Mode Selection**: Choose between manual input, auto-generation, or batch testing
4. **Input Generation**: 
   - **Manual**: Prompts for each parameter with intelligent suggestions
   - **Auto-generate**: Creates appropriate inputs based on parameter names and context
   - **Batch**: Generates multiple test cases automatically
5. **Execution**: Runs the function with provided inputs
6. **Verification**: Asks you to confirm if the output matches expectations

## Intelligent Input Generation

### LLM-Powered Analysis (with OpenAI API)
When an API key is provided, the tool uses GPT to analyze parameters and generate contextually appropriate test values:
- Analyzes parameter names, function docstrings, and context
- Determines appropriate data types and realistic values
- Provides reasoning for each generated value
- Handles complex domain-specific parameters intelligently

### Enhanced Rule-Based Generation (fallback)
For cases without API access, the tool uses comprehensive pattern matching:

- **Numbers**: `weight` → 50.0-120.0 kg, `height` → 1.5-2.1 m, `age` → 18-80, `year` → 1990-2024
- **Strings**: `name` → realistic names, `email` → valid format, `city` → major cities
- **Booleans**: `is_active`, `has_permission` → True/False
- **Lists**: `numbers` → `[1, 5, 3]`, `items` → `['item1', 'item2']`
- **Coordinates**: `latitude` → -90 to 90, `longitude` → -180 to 180
- **Special cases**: BMI functions get appropriate weight/height, factorial gets small numbers

## Input Types

The tool automatically handles various input types:
- Numbers: `42`, `3.14`
- Strings: `hello world`
- Lists: `[1, 2, 3]`
- Dictionaries: `{"key": "value"}`
- Booleans: `True`, `False`
- None: `None`

## Example Sessions

### Manual Input with Suggestions
```
Select function number (or 'q' to quit): 1

Function: add_numbers
Description: Add two numbers together.

Auto-generate inputs? (y/n, default: n): n
Enter value for 'a' (suggested: 5): 10
Enter value for 'b' (suggested: 3): 20

Running add_numbers with inputs: {'a': 10, 'b': 20}
Result: 30
Is this the expected output? (y/n): y
✓ Test passed!
```

### Auto-Generated Inputs (with LLM)
```
🤖 LLM-powered intelligent input generation enabled

Select function number (or 'q' to quit): 8

Testing mode:
1. Manual input
2. Auto-generate inputs  
3. Batch test (multiple auto-generated inputs)
Select mode (1-3, default: 1): 2

Function: calculate_bmi
  LLM suggestion for 'weight': 75.2 (weight is typically measured in kg as a float)
  LLM suggestion for 'height': 1.78 (height is typically measured in meters as a float)
Running calculate_bmi with inputs: {'weight': 75.2, 'height': 1.78}
Result: 23.74
Is this the expected output? (y/n): y
✓ Test passed!
```

### Batch Testing
```
Select function number (or 'q' to quit): 5

Testing mode:
1. Manual input
2. Auto-generate inputs
3. Batch test (multiple auto-generated inputs)
Select mode (1-3, default: 1): 3
Number of test cases to generate (default: 5): 3

Running 3 auto-generated test cases for calculate_bmi:
--------------------------------------------------

Test 1: {'weight': 70, 'height': 1.75}
Result: 22.857142857142858
Expected? (y/n/s to skip remaining): y
✓ Test passed!

Test 2: {'weight': 85, 'height': 1.80}
Result: 26.234567901234566
Expected? (y/n/s to skip remaining): y
✓ Test passed!
```

### Web Interface
```bash
$ python function_tester.py --web
📝 Using rule-based input generation
🔍 Discovering functions...
✅ Found 14 functions
🌐 Web interface starting at http://localhost:8080
```

The web interface will automatically open in your browser, showing:
- A sidebar with all discovered functions
- Function details with parameter forms
- Auto-generate and run test buttons
- Real-time results with visual feedback
- Interactive verification section to mark results as correct/incorrect
- Test result logging and tracking
- Comprehensive test summary with statistics and detailed results

## Web Interface Features

The web interface provides a modern, user-friendly alternative to the terminal:

- **Visual Function Browser**: Browse functions with syntax highlighting
- **Interactive Parameter Forms**: Easy-to-use input fields with validation
- **One-Click Auto-Generation**: Generate intelligent inputs with a button click
- **Real-Time Results**: See function outputs immediately with success/error indicators
- **Interactive Verification**: Mark results as correct/incorrect with visual feedback
- **Test Result Logging**: Track verification results with timestamps
- **Comprehensive Test Summary**: View detailed summary of all tests at the end
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Auto-Launch**: Automatically opens your browser when started
- **No Installation**: Pure HTML/CSS/JavaScript - no additional dependencies

## Requirements

- Python 3.6+
- No external dependencies for basic functionality
- `requests` library for LLM integration (install with `pip install requests`)
- OpenAI API key for enhanced intelligent input generation (optional)
- Modern web browser for web interface

## Setup for LLM Features

1. Install requests: `pip install requests`
2. Get an OpenAI API key from https://platform.openai.com/api-keys
3. Either:
   - Pass it as argument: `--api-key your_key_here`
   - Set environment variable: `export OPENAI_API_KEY=your_key_here`