#!/usr/bin/env python3
"""
Python Function Testing Automation Tool
Discovers functions in a codebase, allows interactive testing with custom inputs.
"""

import ast
import importlib.util
import inspect
import os
import sys
from typing import Any, Dict, List, Tuple, Callable


class FunctionTester:
    def __init__(self, target_directory: str = "."):
        self.target_directory = target_directory
        self.discovered_functions = {}

    def discover_functions(self) -> Dict[str, Callable]:
        """Discover all functions in Python files within the target directory."""
        functions = {}

        for root, dirs, files in os.walk(self.target_directory):
            # Skip hidden directories and common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["__pycache__", "venv", "env"]]

            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    file_path = os.path.join(root, file)
                    try:
                        functions.update(self._extract_functions_from_file(file_path))
                    except Exception as e:
                        print(f"Warning: Could not process {file_path}: {e}")

        self.discovered_functions = functions
        return functions

    def _extract_functions_from_file(self, file_path: str) -> Dict[str, Callable]:
        """Extract functions from a single Python file."""
        functions = {}

        # Parse the file to get function names
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                return functions

        # Get function definitions
        function_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                function_names.append(node.name)

        if not function_names:
            return functions

        # Import the module to get actual function objects
        try:
            spec = importlib.util.spec_from_file_location("temp_module", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for func_name in function_names:
                if hasattr(module, func_name):
                    func = getattr(module, func_name)
                    if callable(func):
                        key = f"{os.path.relpath(file_path)}::{func_name}"
                        functions[key] = func
        except Exception as e:
            print(f"Warning: Could not import functions from {file_path}: {e}")

        return functions

    def get_function_signature(self, func: Callable) -> Tuple[List[str], Dict[str, Any]]:
        """Get function parameters and their default values."""
        sig = inspect.signature(func)
        params = []
        defaults = {}

        for param_name, param in sig.parameters.items():
            params.append(param_name)
            if param.default != inspect.Parameter.empty:
                defaults[param_name] = param.default

        return params, defaults

    def prompt_for_inputs(self, func: Callable) -> Dict[str, Any]:
        """Interactively prompt user for function inputs."""
        params, defaults = self.get_function_signature(func)
        inputs = {}

        print(f"\nFunction: {func.__name__}")
        if func.__doc__:
            print(f"Description: {func.__doc__.strip()}")

        for param in params:
            default_val = defaults.get(param)
            prompt = f"Enter value for '{param}'"
            if default_val is not None:
                prompt += f" (default: {default_val})"
            prompt += ": "

            user_input = input(prompt).strip()

            if not user_input and default_val is not None:
                inputs[param] = default_val
            elif user_input:
                # Try to evaluate as Python literal, fallback to string
                try:
                    inputs[param] = ast.literal_eval(user_input)
                except (ValueError, SyntaxError):
                    inputs[param] = user_input
            else:
                inputs[param] = None

        return inputs

    def run_test(self, func: Callable, inputs: Dict[str, Any]) -> Tuple[Any, bool]:
        """Run the function with given inputs and return result and success status."""
        try:
            result = func(**inputs)
            return result, True
        except Exception as e:
            print(f"Error executing function: {e}")
            return str(e), False

    def interactive_testing_session(self):
        """Main interactive testing loop."""
        print("Python Function Testing Tool")
        print("=" * 40)

        # Discover functions
        print("Discovering functions...")
        functions = self.discover_functions()

        if not functions:
            print("No functions found in the current directory.")
            return

        while True:
            # Display available functions
            print(f"\nFound {len(functions)} functions:")
            func_list = list(functions.keys())
            for i, func_key in enumerate(func_list, 1):
                print(f"{i}. {func_key}")

            # Get user selection
            try:
                choice = input("\nSelect function number (or 'q' to quit): ").strip()
                if choice.lower() == "q":
                    break

                func_index = int(choice) - 1
                if 0 <= func_index < len(func_list):
                    selected_key = func_list[func_index]
                    selected_func = functions[selected_key]

                    # Get inputs from user
                    inputs = self.prompt_for_inputs(selected_func)

                    # Run the test
                    print(f"\nRunning {selected_func.__name__} with inputs: {inputs}")
                    result, success = self.run_test(selected_func, inputs)

                    # Display result
                    print(f"\nResult: {result}")
                    if success:
                        expected = input("Is this the expected output? (y/n): ").strip().lower()
                        if expected == "y":
                            print("✓ Test passed!")
                        else:
                            print("✗ Test failed - output not as expected")
                    else:
                        print("✗ Test failed - function threw an exception")

                    input("\nPress Enter to continue...")
                else:
                    print("Invalid selection.")

            except (ValueError, KeyboardInterrupt):
                print("Invalid input or interrupted.")
            except Exception as e:
                print(f"Error: {e}")


def main():
    """Entry point for the function tester."""
    import argparse

    parser = argparse.ArgumentParser(description="Interactive Python Function Tester")
    parser.add_argument("--directory", "-d", default=".", help="Directory to search for Python files (default: current directory)")

    args = parser.parse_args()

    tester = FunctionTester(args.directory)
    tester.interactive_testing_session()


if __name__ == "__main__":
    main()
