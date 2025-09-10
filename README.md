# Python Function Testing Tool

An interactive tool to automatically discover and test Python functions in your codebase.

## Features

- Automatically discovers all public functions in Python files
- Interactive function selection
- Dynamic input prompting based on function signatures
- Handles default parameters
- Executes functions and captures results
- Manual verification of expected outputs

## Usage

### Basic Usage
```bash
python function_tester.py
```

### Specify Directory
```bash
python function_tester.py --directory /path/to/your/code
```

## How It Works

1. **Discovery**: Scans Python files in the specified directory for function definitions
2. **Selection**: Presents a numbered list of discovered functions
3. **Input**: Prompts for each function parameter, respecting defaults
4. **Execution**: Runs the function with provided inputs
5. **Verification**: Asks you to confirm if the output matches expectations

## Input Types

The tool automatically handles various input types:
- Numbers: `42`, `3.14`
- Strings: `hello world`
- Lists: `[1, 2, 3]`
- Dictionaries: `{"key": "value"}`
- Booleans: `True`, `False`
- None: `None`

## Example Session

```
Python Function Testing Tool
========================================
Discovering functions...

Found 7 functions:
1. sample_functions.py::add_numbers
2. sample_functions.py::multiply
3. sample_functions.py::reverse_string
4. sample_functions.py::calculate_area
5. sample_functions.py::greet
6. sample_functions.py::factorial
7. sample_functions.py::is_even

Select function number (or 'q' to quit): 1

Function: add_numbers
Description: Add two numbers together.
Enter value for 'a': 5
Enter value for 'b': 3

Running add_numbers with inputs: {'a': 5, 'b': 3}

Result: 8
Is this the expected output? (y/n): y
✓ Test passed!
```

## Requirements

- Python 3.6+
- No external dependencies required