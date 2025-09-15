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
import random
import re
import json
from typing import Any, Dict, List, Tuple, Callable, Union, Optional


class FunctionTester:
    def __init__(self, target_directory: str = ".", api_key: Optional[str] = None):
        self.target_directory = target_directory
        self.discovered_functions = {}
        self.discovered_classes = {}  # Store discovered classes
        self.api_key = api_key
        self.llm_available = api_key is not None
        self.test_results = []  # Track all test results

    def discover_functions(self) -> Dict[str, Callable]:
        """Discover all functions and classes in Python files within the target directory."""
        functions = {}
        classes = {}

        for root, dirs, files in os.walk(self.target_directory):
            # Skip hidden directories and common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["__pycache__", "venv", "env"]]

            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    file_path = os.path.join(root, file)
                    try:
                        file_functions, file_classes = self._extract_functions_and_classes_from_file(file_path)
                        functions.update(file_functions)
                        classes.update(file_classes)
                    except Exception as e:
                        print(f"Warning: Could not process {file_path}: {e}")

        self.discovered_functions = functions
        self.discovered_classes = classes
        return functions

    def _extract_functions_and_classes_from_file(self, file_path: str) -> Tuple[Dict[str, Callable], Dict[str, type]]:
        """Extract functions, classes, and class methods from a single Python file."""
        functions = {}
        classes = {}

        # Parse the file to get function and class names with their methods
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                return functions, classes

        # Get function, class, and method definitions
        function_names = []
        class_info = {}  # {class_name: [method_names]}

        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                function_names.append(node.name)
            elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                class_name = node.name
                method_names = []

                for class_node in node.body:
                    if isinstance(class_node, ast.FunctionDef) and not class_node.name.startswith("_"):
                        method_names.append(class_node.name)

                class_info[class_name] = method_names

        if not function_names and not class_info:
            return functions, classes

        # Import the module to get actual function and class objects
        try:
            spec = importlib.util.spec_from_file_location("temp_module", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Extract standalone functions
            for func_name in function_names:
                if hasattr(module, func_name):
                    func = getattr(module, func_name)
                    if callable(func):
                        key = f"{os.path.relpath(file_path)}::{func_name}"
                        functions[key] = func

            # Extract classes and their methods
            for class_name, method_names in class_info.items():
                if hasattr(module, class_name):
                    cls = getattr(module, class_name)
                    if inspect.isclass(cls):
                        classes[class_name] = cls

                        # Extract methods from the class
                        for method_name in method_names:
                            if hasattr(cls, method_name):
                                method = getattr(cls, method_name)
                                if callable(method):
                                    # Determine method type
                                    if isinstance(inspect.getattr_static(cls, method_name), staticmethod):
                                        method_type = "static"
                                    elif isinstance(inspect.getattr_static(cls, method_name), classmethod):
                                        method_type = "class"
                                    else:
                                        method_type = "instance"

                                    key = f"{os.path.relpath(file_path)}::{class_name}.{method_name}"
                                    functions[key] = {"method": method, "class": cls, "type": method_type, "name": method_name}

        except Exception as e:
            print(f"Warning: Could not import from {file_path}: {e}")

        return functions, classes

    def get_function_signature(self, func: Union[Callable, Dict]) -> Tuple[List[str], Dict[str, Any], Dict[str, Any]]:
        """Get function parameters and their default values."""
        # Handle class methods
        if isinstance(func, dict) and "method" in func:
            method_info = func
            method = method_info["method"]
            method_type = method_info["type"]

            if method_type == "static":
                # Static method - use method signature as-is
                sig = inspect.signature(method)
            elif method_type == "class":
                # Class method - use method signature as-is (cls parameter handled automatically)
                sig = inspect.signature(method)
            else:
                # Instance method - we'll handle 'self' parameter specially
                sig = inspect.signature(method)
        else:
            # Regular function
            sig = inspect.signature(func)

        params = []
        defaults = {}
        annotations = {}

        for param_name, param in sig.parameters.items():
            # Skip 'self' and 'cls' parameters for display purposes
            if param_name in ["self", "cls"]:
                continue

            params.append(param_name)
            if param.default != inspect.Parameter.empty:
                defaults[param_name] = param.default
            if param.annotation != inspect.Parameter.empty:
                annotations[param_name] = param.annotation

        return params, defaults, annotations

    def discover_available_classes(self) -> Dict[str, type]:
        """Get the discovered classes."""
        return self.discovered_classes.copy()

    def get_class_constructor_info(self, cls: type) -> Tuple[List[str], Dict[str, Any]]:
        """Get class constructor parameters and defaults."""
        try:
            sig = inspect.signature(cls.__init__)
            params = []
            defaults = {}

            for param_name, param in sig.parameters.items():
                if param_name != "self":  # Skip 'self' parameter
                    params.append(param_name)
                    if param.default != inspect.Parameter.empty:
                        defaults[param_name] = param.default

            return params, defaults
        except (ValueError, TypeError):
            return [], {}

    def generate_intelligent_inputs(self, func: Union[Callable, Dict]) -> Dict[str, Any]:
        """Generate intelligent test inputs based on function signature and context."""
        params, defaults, annotations = self.get_function_signature(func)
        inputs = {}

        # Get docstring - handle both regular functions and class methods
        if isinstance(func, dict) and "method" in func:
            docstring = func["method"].__doc__ or ""
        else:
            docstring = func.__doc__ or ""

        available_classes = self.discover_available_classes()

        for param in params:
            if param in defaults:
                # Use default value as a starting point
                inputs[param] = defaults[param]
            else:
                # Check if parameter expects a class instance
                annotation = annotations.get(param)
                if annotation and inspect.isclass(annotation) and annotation in available_classes.values():
                    inputs[param] = self._generate_class_instance(annotation, available_classes)
                else:
                    # Check if parameter name suggests a class (heuristic)
                    potential_class = None
                    for class_name, class_type in available_classes.items():
                        if param.lower().endswith(class_name.lower()) or param.lower().replace("_", "").endswith(class_name.lower()) or class_name.lower() in param.lower():
                            potential_class = class_type
                            break

                    if potential_class:
                        inputs[param] = self._generate_class_instance(potential_class, available_classes)
                    else:
                        # Generate based on parameter name and context
                        inputs[param] = self._generate_value_for_parameter(param, func, docstring)

        return inputs

    def _call_llm_for_parameter_analysis(self, param_name: str, func_name: str, docstring: str) -> Optional[Dict]:
        """Use LLM to analyze parameter and suggest appropriate test value."""
        if not self.llm_available:
            return None

        try:
            import requests

            prompt = f"""
            Analyze this Python function parameter and suggest an appropriate test value:
            
            Function: {func_name}
            Parameter: {param_name}
            Docstring: {docstring or "No docstring provided"}
            
            Based on the parameter name and context, determine:
            1. The most likely data type (int, float, str, bool, list, dict)
            2. An appropriate test value
            3. A brief reasoning
            
            Respond with valid JSON only:
            {{
                "data_type": "int|float|str|bool|list|dict",
                "test_value": <actual_value>,
                "reasoning": "brief explanation"
            }}
            
            Examples:
            - weight → {{"data_type": "float", "test_value": 70.5, "reasoning": "weight is typically a decimal number in kg"}}
            - name → {{"data_type": "str", "test_value": "John Doe", "reasoning": "name is a string identifier"}}
            - is_active → {{"data_type": "bool", "test_value": true, "reasoning": "boolean flag parameter"}}
            """

            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

            data = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": prompt}], "max_tokens": 150, "temperature": 0.3}

            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=10)

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()

                # Extract JSON from response
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())

        except Exception as e:
            print(f"LLM analysis failed: {e}")

        return None

    def _generate_value_for_parameter(self, param_name: str, func: Callable, docstring: str) -> Any:
        """Generate a value for a specific parameter based on its name and context."""
        # Try LLM analysis first if available
        if self.llm_available:
            llm_result = self._call_llm_for_parameter_analysis(param_name, func.__name__, docstring)
            if llm_result and "test_value" in llm_result:
                print(f"  LLM suggestion for '{param_name}': {llm_result['test_value']} ({llm_result.get('reasoning', 'No reasoning')})")
                return llm_result["test_value"]

        param_lower = param_name.lower()

        # Enhanced number-related parameters
        number_keywords = ["num", "count", "size", "length", "width", "height", "age", "year", "weight", "mass", "distance", "speed", "price", "cost", "amount", "quantity", "volume", "area", "radius", "diameter", "score", "rating"]

        if any(word in param_lower for word in number_keywords):
            if "age" in param_lower:
                return random.randint(18, 80)
            elif "year" in param_lower:
                return random.randint(1990, 2024)
            elif "weight" in param_lower or "mass" in param_lower:
                return round(random.uniform(50.0, 120.0), 1)  # kg
            elif "height" in param_lower:
                return round(random.uniform(1.5, 2.1), 2)  # meters
            elif any(word in param_lower for word in ["length", "width", "distance", "radius"]):
                return round(random.uniform(1.0, 100.0), 1)
            elif any(word in param_lower for word in ["price", "cost", "amount"]):
                return round(random.uniform(10.0, 1000.0), 2)
            elif any(word in param_lower for word in ["score", "rating"]):
                return random.randint(1, 10)
            elif "percentage" in param_lower or "percent" in param_lower:
                return random.randint(0, 100)
            else:
                return random.randint(1, 100)

        # Enhanced string-related parameters
        string_keywords = ["name", "text", "string", "message", "word", "title", "description", "address", "city", "country", "subject", "content", "label"]

        if any(word in param_lower for word in string_keywords):
            if "name" in param_lower:
                if "first" in param_lower:
                    return random.choice(["Alice", "Bob", "Charlie", "Diana", "Eve"])
                elif "last" in param_lower:
                    return random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones"])
                else:
                    return random.choice(["Alice Smith", "Bob Johnson", "Charlie Brown"])
            elif "email" in param_lower:
                return "test@example.com"
            elif "address" in param_lower:
                return "123 Main St, Anytown, USA"
            elif "city" in param_lower:
                return random.choice(["New York", "London", "Tokyo", "Paris", "Sydney"])
            elif "country" in param_lower:
                return random.choice(["USA", "UK", "Japan", "France", "Australia"])
            elif "subject" in param_lower or "title" in param_lower:
                return random.choice(["Important Update", "Meeting Reminder", "Project Status"])
            elif "message" in param_lower or "content" in param_lower:
                return random.choice(["Hello World", "This is a test message", "Sample content"])
            else:
                return "sample_text"

        # Boolean parameters
        bool_keywords = ["is_", "has_", "can_", "should_", "flag", "enabled", "active", "valid"]
        if any(word in param_lower for word in bool_keywords):
            return random.choice([True, False])

        # List/array parameters
        list_keywords = ["list", "array", "items", "numbers", "values", "data"]
        if any(word in param_lower for word in list_keywords):
            if "numbers" in param_lower or "values" in param_lower:
                return [random.randint(1, 10) for _ in range(random.randint(2, 5))]
            else:
                return [f"item{i}" for i in range(1, random.randint(3, 6))]

        # Temperature parameters
        if "temp" in param_lower:
            if "celsius" in param_lower:
                return random.randint(-10, 40)
            elif "fahrenheit" in param_lower:
                return random.randint(14, 104)
            else:
                return random.randint(20, 30)

        # Coordinate parameters
        if param_lower in ["x", "y", "z", "lat", "lon", "latitude", "longitude"]:
            if param_lower in ["lat", "latitude"]:
                return round(random.uniform(-90, 90), 6)
            elif param_lower in ["lon", "longitude"]:
                return round(random.uniform(-180, 180), 6)
            else:
                return random.randint(0, 100)

        # Mathematical parameters
        if param_lower in ["a", "b", "c", "n", "m", "k"]:
            return random.randint(1, 10)

        # Analyze docstring for additional context
        if docstring:
            doc_lower = docstring.lower()
            if re.search(r"factorial|fact", doc_lower) and param_lower == "n":
                return random.randint(1, 8)  # Keep factorial small
            if re.search(r"bmi|body.*mass", doc_lower):
                if "weight" in param_lower:
                    return round(random.uniform(50.0, 120.0), 1)
                elif "height" in param_lower:
                    return round(random.uniform(1.5, 2.1), 2)
            if re.search(r"email", doc_lower) and any(word in param_lower for word in ["to", "recipient", "sender"]):
                return "user@example.com"

        # Default fallbacks
        if len(param_name) == 1:  # Single letter parameters
            return random.randint(1, 10)

        # Check if it might be a numeric parameter based on context
        if re.search(r"\d", param_name):  # Contains digits
            return random.randint(1, 100)

        # Default string for unknown parameters
        return f"test_{param_name}"

    def prompt_for_inputs(self, func: Callable, auto_generate: bool = False) -> Dict[str, Any]:
        """Interactively prompt user for function inputs or auto-generate them."""
        if auto_generate:
            return self.generate_intelligent_inputs(func)

        params, defaults, annotations = self.get_function_signature(func)
        inputs = {}

        # Handle class methods
        if isinstance(func, dict) and "method" in func:
            method_info = func
            method_name = method_info["name"]
            class_name = method_info["class"].__name__
            method_type = method_info["type"]

            print(f"\nMethod: {class_name}.{method_name} ({method_type} method)")
            if method_info["method"].__doc__:
                print(f"Description: {method_info['method'].__doc__.strip()}")

            # For instance methods, offer to create or provide instance
            if method_type == "instance":
                print(f"\nThis is an instance method. You can:")
                print("1. Create a new {class_name} instance")
                print("2. Use an existing instance (if you have one)")

                choice = input("Choose option (1/2, default: 1): ").strip()
                if choice == "2":
                    # Let user provide existing instance (advanced feature)
                    print("Note: You'll need to provide the instance as 'self' parameter")
                    # We'll handle this in the parameter loop
                else:
                    # We'll create instance during execution
                    pass
        else:
            print(f"\nFunction: {func.__name__}")
            if func.__doc__:
                print(f"Description: {func.__doc__.strip()}")

        # Offer to auto-generate inputs
        auto_choice = input("\nAuto-generate inputs? (y/n, default: n): ").strip().lower()
        if auto_choice == "y":
            return self.generate_intelligent_inputs(func)

        available_classes = self.discover_available_classes()

        for param in params:
            default_val = defaults.get(param)
            annotation = annotations.get(param)

            # Check if parameter expects a class instance
            if annotation and inspect.isclass(annotation) and annotation in available_classes.values():
                print(f"\nParameter '{param}' expects a {annotation.__name__} instance.")
                class_choice = input(f"Create {annotation.__name__} instance? (y/n, default: y): ").strip().lower()

                if class_choice != "n":
                    inputs[param] = self._create_class_instance(annotation, available_classes)
                    continue

            # Check if parameter name suggests a class (heuristic)
            potential_class = None
            for class_name, class_type in available_classes.items():
                if param.lower().endswith(class_name.lower()) or param.lower().replace("_", "").endswith(class_name.lower()) or class_name.lower() in param.lower():
                    potential_class = class_type
                    break

            if potential_class:
                print(f"\nParameter '{param}' might expect a {potential_class.__name__} instance.")
                class_choice = input(f"Create {potential_class.__name__} instance? (y/n, default: n): ").strip().lower()

                if class_choice == "y":
                    inputs[param] = self._create_class_instance(potential_class, available_classes)
                    continue

            # Regular parameter handling
            suggested_val = self._generate_value_for_parameter(param, func, func.__doc__ or "")

            prompt = f"Enter value for '{param}'"
            if default_val is not None:
                prompt += f" (default: {default_val})"
            prompt += f" (suggested: {suggested_val}): "
            user_input = input(prompt).strip()
            if not user_input and default_val is not None:
                inputs[param] = default_val
            elif not user_input:
                inputs[param] = suggested_val
            else:
                # Try to evaluate as Python literal, fallback to string
                try:
                    inputs[param] = ast.literal_eval(user_input)
                except (ValueError, SyntaxError):
                    inputs[param] = user_input

        return inputs

    def _create_class_instance(self, cls: type, available_classes: Dict[str, type]):
        """Interactively create an instance of a class."""
        print(f"\nCreating {cls.__name__} instance:")

        params, defaults = self.get_class_constructor_info(cls)
        constructor_inputs = {}

        for param in params:
            default_val = defaults.get(param)

            # Check if this parameter also expects a class
            param_annotation = None
            try:
                sig = inspect.signature(cls.__init__)
                for p_name, p_param in sig.parameters.items():
                    if p_name == param and p_param.annotation != inspect.Parameter.empty:
                        param_annotation = p_param.annotation
                        break
            except:
                pass

            if param_annotation and inspect.isclass(param_annotation) and param_annotation in available_classes.values():
                print(f"  Parameter '{param}' expects a {param_annotation.__name__} instance.")
                nested_choice = input(f"  Create {param_annotation.__name__} instance? (y/n, default: y): ").strip().lower()

                if nested_choice != "n":
                    constructor_inputs[param] = self._create_class_instance(param_annotation, available_classes)
                    continue

            # Generate suggested value for class parameter
            suggested_val = self._generate_value_for_parameter(param, cls, cls.__doc__ or "")

            prompt = f"  Enter value for '{param}'"
            if default_val is not None:
                prompt += f" (default: {default_val})"
            prompt += f" (suggested: {suggested_val}): "

            user_input = input(prompt).strip()

            if not user_input and default_val is not None:
                constructor_inputs[param] = default_val
            elif not user_input:
                constructor_inputs[param] = suggested_val
            else:
                # Try to evaluate as Python literal, fallback to string
                try:
                    constructor_inputs[param] = ast.literal_eval(user_input)
                except (ValueError, SyntaxError):
                    constructor_inputs[param] = user_input

        try:
            instance = cls(**constructor_inputs)
            print(f"  Created: {instance}")
            return instance
        except Exception as e:
            print(f"  Error creating {cls.__name__} instance: {e}")
            print(f"  Using None instead.")
            return None

    def _generate_class_instance(self, cls: type, available_classes: Dict[str, type]):
        """Automatically generate an instance of a class with intelligent defaults."""
        params, defaults = self.get_class_constructor_info(cls)
        constructor_inputs = {}

        for param in params:
            if param in defaults:
                constructor_inputs[param] = defaults[param]
            else:
                # Check if this parameter also expects a class
                param_annotation = None
                try:
                    sig = inspect.signature(cls.__init__)
                    for p_name, p_param in sig.parameters.items():
                        if p_name == param and p_param.annotation != inspect.Parameter.empty:
                            param_annotation = p_param.annotation
                            break
                except:
                    pass

                if param_annotation and inspect.isclass(param_annotation) and param_annotation in available_classes.values():
                    constructor_inputs[param] = self._generate_class_instance(param_annotation, available_classes)
                else:
                    # Generate intelligent value for class parameter
                    constructor_inputs[param] = self._generate_value_for_parameter(param, cls, cls.__doc__ or "")

        try:
            instance = cls(**constructor_inputs)
            return instance
        except Exception as e:
            print(f"Warning: Could not create {cls.__name__} instance: {e}")
            return None

    def add_test_result(self, func_name: str, inputs: Dict[str, Any], result: Any, success: bool, verification: Optional[str] = None):
        """Add a test result to the tracking list."""
        test_record = {"function_name": func_name, "inputs": inputs.copy(), "output": result, "success": success, "verification": verification, "timestamp": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  # 'PASSED', 'FAILED', or None
        self.test_results.append(test_record)

    def display_test_summary(self):
        """Display a summary of all test results."""
        if not self.test_results:
            print("\n📊 No tests were executed.")
            return

        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)

        total_tests = len(self.test_results)
        successful_executions = sum(1 for test in self.test_results if test["success"])
        verified_passed = sum(1 for test in self.test_results if test["verification"] == "PASSED")
        verified_failed = sum(1 for test in self.test_results if test["verification"] == "FAILED")
        unverified = sum(1 for test in self.test_results if test["verification"] is None and test["success"])

        print(f"Total Tests: {total_tests}")
        print(f"Successful Executions: {successful_executions}")
        print(f"Execution Errors: {total_tests - successful_executions}")
        print(f"Verified Passed: {verified_passed}")
        print(f"Verified Failed: {verified_failed}")
        print(f"Unverified: {unverified}")
        print("-" * 80)

        for i, test in enumerate(self.test_results, 1):
            status_icon = "✅" if test["success"] else "❌"
            verification_icon = ""
            if test["verification"] == "PASSED":
                verification_icon = " ✅"
            elif test["verification"] == "FAILED":
                verification_icon = " ❌"
            elif test["success"]:
                verification_icon = " ❓"

            print(f"{i:2d}. {status_icon} {test['function_name']}{verification_icon}")
            print(f"    Input:  {test['inputs']}")
            print(f"    Output: {test['output']}")
            print(f"    Time:   {test['timestamp']}")
            if not test["success"]:
                print(f"    Status: EXECUTION ERROR")
            elif test["verification"]:
                print(f"    Status: VERIFICATION {test['verification']}")
            else:
                print(f"    Status: NOT VERIFIED")
            print()

        print("=" * 80)

    def run_test(self, func: Union[Callable, Dict], inputs: Dict[str, Any]) -> Tuple[Any, bool]:
        """Run the function with given inputs and return result and success status."""
        try:
            # Handle class methods
            if isinstance(func, dict) and "method" in func:
                method_info = func
                method = method_info["method"]
                cls = method_info["class"]
                method_type = method_info["type"]

                if method_type == "static":
                    # Static method - call directly
                    result = method(**inputs)
                elif method_type == "class":
                    # Class method - call with class
                    result = method(**inputs)
                else:
                    # Instance method - need to create instance first
                    if "self" in inputs:
                        # Use provided instance
                        instance = inputs.pop("self")
                        result = method(instance, **inputs)
                    else:
                        # Create new instance
                        try:
                            instance = cls()  # Try default constructor
                            result = method(instance, **inputs)
                        except Exception:
                            # If default constructor fails, ask for parameters
                            print(f"Need to create {cls.__name__} instance for method {method_info['name']}")
                            available_classes = self.discover_available_classes()
                            instance = self._create_class_instance(cls, available_classes)
                            if instance is None:
                                return "Could not create class instance", False
                            result = method(instance, **inputs)

                return result, True
            else:
                # Regular function
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
        print("Discovering functions and classes...")
        functions = self.discover_functions()

        if not functions:
            print("No functions found in the current directory.")
            return

        print(f"Found {len(functions)} functions and {len(self.discovered_classes)} classes")
        if self.discovered_classes:
            print("Available classes:", ", ".join(self.discovered_classes.keys()))

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

                    # Ask for testing mode
                    mode = input("\nTesting mode:\n1. Manual input\n2. Auto-generate inputs\n3. Batch test (multiple auto-generated inputs)\nSelect mode (1-3, default: 1): ").strip()

                    if mode == "3":
                        # Batch testing mode
                        num_tests = input("Number of test cases to generate (default: 5): ").strip()
                        try:
                            num_tests = int(num_tests) if num_tests else 5
                        except ValueError:
                            num_tests = 5

                        print(f"\nRunning {num_tests} auto-generated test cases for {selected_func.__name__}:")
                        print("-" * 50)

                        for i in range(num_tests):
                            inputs = self.generate_intelligent_inputs(selected_func)
                            print(f"\nTest {i+1}: {inputs}")
                            result, success = self.run_test(selected_func, inputs)

                            verification = None
                            if success:
                                print(f"Result: {result}")
                                expected = input("Expected? (y/n/s to skip remaining): ").strip().lower()
                                if expected == "y":
                                    print("✓ Test passed!")
                                    verification = "PASSED"
                                elif expected == "s":
                                    # Track this test as unverified before breaking
                                    self.add_test_result(selected_func.__name__, inputs, result, success, None)
                                    break
                                else:
                                    print("✗ Test failed - output not as expected")
                                    verification = "FAILED"
                            else:
                                print(f"✗ Error: {result}")

                            # Track the test result
                            self.add_test_result(selected_func.__name__, inputs, result, success, verification)
                    else:
                        # Single test mode
                        auto_generate = mode == "2"
                        inputs = self.prompt_for_inputs(selected_func, auto_generate)

                        # Run the test
                        if callable(selected_func):
                            funcname = selected_func.__name__
                        else:
                            funcname = selected_func["name"]
                        print(f"\nRunning {funcname} with inputs: {inputs}")
                        result, success = self.run_test(selected_func, inputs)

                        # Display result
                        print(f"\nResult: {result}")
                        verification = None
                        if success:
                            expected = input("Is this the expected output? (y/n): ").strip().lower()
                            if expected == "y":
                                print("✓ Test passed!")
                                verification = "PASSED"
                            else:
                                print("✗ Test failed - output not as expected")
                                verification = "FAILED"
                        else:
                            print("✗ Test failed - function threw an exception")

                        # Track the test result
                        self.add_test_result(funcname, inputs, result, success, verification)

                    input("\nPress Enter to continue...")
                else:
                    print("Invalid selection.")

            except (ValueError, KeyboardInterrupt):
                print("Invalid input or interrupted.")
                break
            except Exception as e:
                print(f"Error: {e}")

        # Display test summary when exiting
        self.display_test_summary()


def main():
    """Entry point for the function tester."""
    import argparse

    parser = argparse.ArgumentParser(description="Interactive Python Function Tester")
    parser.add_argument("--directory", "-d", default=".", help="Directory to search for Python files (default: current directory)")
    parser.add_argument("--api-key", "-k", help="OpenAI API key for intelligent input generation (optional)")
    parser.add_argument("--web", "-w", action="store_true", help="Launch web interface instead of terminal")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Port for web interface (default: 8080)")

    args = parser.parse_args()

    # Check for API key in environment if not provided
    api_key = args.api_key
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")

    if api_key:
        print("🤖 LLM-powered intelligent input generation enabled")
    else:
        print("📝 Using rule-based input generation (use --api-key or set OPENAI_API_KEY for LLM analysis)")

    tester = FunctionTester(args.directory, api_key)

    if args.web:
        # Launch web interface
        from web_interface import start_web_interface

        print("🔍 Discovering functions and classes...")
        tester.discover_functions()

        if not tester.discovered_functions:
            print("❌ No functions found in the specified directory")
            return

        print(f"✅ Found {len(tester.discovered_functions)} functions and {len(tester.discovered_classes)} classes")
        if tester.discovered_classes:
            print("Available classes:", ", ".join(tester.discovered_classes.keys()))
        start_web_interface(tester, args.port)
    else:
        # Launch terminal interface
        tester.interactive_testing_session()


if __name__ == "__main__":
    main()
