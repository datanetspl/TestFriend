#!/usr/bin/env python3
"""
Web interface for Python Function Testing Tool
Provides an HTML-based interface for testing functions.
"""

import json
import threading
import webbrowser
import inspect
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from function_tester import FunctionTester


class WebTestingHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, tester=None, **kwargs):
        self.tester = tester
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/":
            self.serve_main_page()
        elif parsed_path.path == "/api/functions":
            self.serve_functions_list()
        elif parsed_path.path == "/api/function-info":
            query = parse_qs(parsed_path.query)
            func_key = query.get("key", [""])[0]
            self.serve_function_info(func_key)
        elif parsed_path.path == "/api/test-summary":
            self.serve_test_summary()
        else:
            self.send_error(404)

    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/api/test-function":
            self.handle_test_function()
        elif parsed_path.path == "/api/generate-inputs":
            self.handle_generate_inputs()
        elif parsed_path.path == "/api/verify-result":
            self.handle_verify_result()
        else:
            self.send_error(404)

    def serve_main_page(self):
        """Serve the main HTML page."""
        html_content = self.get_html_template()

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html_content.encode())

    def serve_functions_list(self):
        """Serve the list of discovered functions."""
        functions = list(self.tester.discovered_functions.keys())

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(functions).encode())

    def serve_function_info(self, func_key):
        """Serve information about a specific function."""
        if func_key not in self.tester.discovered_functions:
            self.send_error(404)
            return

        func = self.tester.discovered_functions[func_key]
        params, defaults, annotations = self.tester.get_function_signature(func)

        # Get available classes
        available_classes = self.tester.discover_available_classes()

        # Handle class methods
        if isinstance(func, dict) and "method" in func:
            method_info = func
            method_name = method_info["name"]
            class_name = method_info["class"].__name__
            method_type = method_info["type"]

            func_name = f"{class_name}.{method_name}"
            docstring = method_info["method"].__doc__ or "No description available"
            is_method = True
            method_details = {"class_name": class_name, "method_name": method_name, "method_type": method_type}
        else:
            func_name = func.__name__
            docstring = func.__doc__ or "No description available"
            is_method = False
            method_details = None

        # Check for class parameters
        class_info = {}
        for param in params:
            annotation = annotations.get(param)
            if annotation and inspect.isclass(annotation) and annotation in available_classes.values():
                class_params, class_defaults = self.tester.get_class_constructor_info(annotation)
                class_info[param] = {"class_name": annotation.__name__, "parameters": class_params, "defaults": class_defaults}
            else:
                # Check heuristically for class parameters
                for class_name, class_type in available_classes.items():
                    if param.lower().endswith(class_name.lower()) or param.lower().replace("_", "").endswith(class_name.lower()) or class_name.lower() in param.lower():
                        class_params, class_defaults = self.tester.get_class_constructor_info(class_type)
                        class_info[param] = {"class_name": class_name, "parameters": class_params, "defaults": class_defaults, "suggested": True}  # Mark as suggested, not definite
                        break

        info = {"name": func_name, "docstring": docstring, "parameters": params, "defaults": defaults, "class_info": class_info, "available_classes": list(available_classes.keys()), "is_method": is_method, "method_details": method_details}

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(info).encode())

    def handle_generate_inputs(self):
        """Generate intelligent inputs for a function."""
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode())

        func_key = data.get("function_key")
        if func_key not in self.tester.discovered_functions:
            self.send_error(404)
            return

        func = self.tester.discovered_functions[func_key]
        inputs = self.tester.generate_intelligent_inputs(func)

        # Convert any non-serializable values to strings
        serializable_inputs = {}
        for key, value in inputs.items():
            try:
                json.dumps(value)
                serializable_inputs[key] = value
            except (TypeError, ValueError):
                serializable_inputs[key] = str(value)

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(serializable_inputs).encode())

    def handle_test_function(self):
        """Execute a function with provided inputs."""
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode())

        func_key = data.get("function_key")
        inputs = data.get("inputs", {})

        if func_key not in self.tester.discovered_functions:
            self.send_error(404)
            return

        # Process class inputs
        available_classes = self.tester.discover_available_classes()
        processed_inputs = {}

        for param, value in inputs.items():
            if isinstance(value, dict) and "__class__" in value and "__params__" in value:
                # This is a class input
                class_name = value["__class__"]
                class_params = value["__params__"]

                if class_name in available_classes:
                    try:
                        cls = available_classes[class_name]
                        instance = cls(**class_params)
                        processed_inputs[param] = instance
                    except Exception as e:
                        print(f"Error creating {class_name} instance: {e}")
                        processed_inputs[param] = None
                else:
                    processed_inputs[param] = None
            else:
                processed_inputs[param] = value

        func = self.tester.discovered_functions[func_key]
        result, success = self.tester.run_test(func, processed_inputs)

        # Track the test result
        func_name = func_key.split("::")[-1] if "::" in func_key else func_key
        self.tester.add_test_result(func_name, processed_inputs, result, success, None)

        # Convert result to serializable format
        try:
            json.dumps(result)
            serializable_result = result
        except (TypeError, ValueError):
            serializable_result = str(result)

        # Convert processed inputs to serializable format for response
        serializable_inputs = {}
        for key, value in processed_inputs.items():
            try:
                json.dumps(value)
                serializable_inputs[key] = value
            except (TypeError, ValueError):
                serializable_inputs[key] = str(value)

        response = {"success": success, "result": serializable_result, "inputs_used": serializable_inputs}

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def handle_verify_result(self):
        """Handle verification of test results."""
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode())

        func_key = data.get("function_key")
        is_correct = data.get("is_correct")
        test_inputs = data.get("inputs", {})
        test_result = data.get("result")

        # Update the test result with verification
        func_name = func_key.split("::")[-1] if "::" in func_key else func_key

        # Find and update the most recent test result for this function
        for test in reversed(self.tester.test_results):
            if test["function_name"] == func_name and test["inputs"] == test_inputs and test["verification"] is None:
                test["verification"] = "PASSED" if is_correct else "FAILED"
                break

        # Log the verification (could be extended to save to file/database)
        verification_log = {
            "function": func_key,
            "inputs": test_inputs,
            "result": test_result,
            "verification": "PASSED" if is_correct else "FAILED",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }

        print(f"📝 Test Verification: {func_key} - {'PASSED' if is_correct else 'FAILED'}")

        response = {"success": True, "verification": verification_log}

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def serve_test_summary(self):
        """Serve the test summary data."""
        summary_data = {"total_tests": len(self.tester.test_results), "successful_executions": sum(1 for test in self.tester.test_results if test["success"]), "verified_passed": sum(1 for test in self.tester.test_results if test["verification"] == "PASSED"), "verified_failed": sum(1 for test in self.tester.test_results if test["verification"] == "FAILED"), "unverified": sum(1 for test in self.tester.test_results if test["verification"] is None and test["success"]), "test_results": []}

        # Convert test results to serializable format
        for test in self.tester.test_results:
            serializable_test = {"function_name": test["function_name"], "inputs": test["inputs"], "success": test["success"], "verification": test["verification"], "timestamp": test["timestamp"]}

            # Convert output to serializable format
            try:
                json.dumps(test["output"])
                serializable_test["output"] = test["output"]
            except (TypeError, ValueError):
                serializable_test["output"] = str(test["output"])

            summary_data["test_results"].append(serializable_test)

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(summary_data).encode())

    def get_html_template(self):
        """Return the HTML template for the web interface."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python Function Tester</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: Consolas, 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 30px;
            padding: 30px;
        }
        
        .sidebar {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
        }
        
        .function-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .function-item {
            padding: 12px;
            margin: 8px 0;
            background: white;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }
        
        .function-item:hover {
            background: #e3f2fd;
            transform: translateY(-2px);
        }
        
        .function-item.selected {
            background: #2196f3;
            color: white;
            border-color: #1976d2;
        }
        
        .method-item {
            border-left: 4px solid #ff9800;
            background: #fff8e1;
        }
        
        .method-item:hover {
            background: #ffecb3;
        }
        
        .method-item.selected {
            background: #ff9800;
            color: white;
            border-color: #f57c00;
        }
        
        .function-name {
            font-weight: bold;
            font-size: 1.1em;
        }
        
        .function-path {
            font-size: 0.9em;
            opacity: 0.7;
            margin-top: 4px;
        }
        
        .test-area {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
        }
        
        .function-info {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #4caf50;
        }
        
        .function-title {
            font-size: 1.5em;
            color: #333;
            margin-bottom: 10px;
        }
        
        .function-description {
            color: #666;
            line-height: 1.6;
            margin-bottom: 15px;
        }
        
        .parameters-section {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .section-title {
            font-size: 1.3em;
            color: #333;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .parameter-input {
            margin-bottom: 15px;
        }
        
        .parameter-label {
            display: block;
            font-weight: bold;
            color: #555;
            margin-bottom: 5px;
        }
        
        .parameter-field {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 1em;
            transition: border-color 0.3s ease;
        }
        
        .parameter-field:focus {
            outline: none;
            border-color: #2196f3;
        }
        
        .class-input-container {
            background: #f0f8ff;
            border: 1px solid #87ceeb;
            border-radius: 6px;
            padding: 15px;
            margin-top: 5px;
        }
        
        .class-inputs {
            margin-top: 15px;
            padding: 10px;
            background: white;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        
        .class-parameter {
            margin-bottom: 10px;
        }
        
        .class-parameter-label {
            display: block;
            font-weight: normal;
            color: #666;
            margin-bottom: 3px;
            font-size: 0.9em;
        }
        
        .class-parameter input {
            width: 100%;
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 0.9em;
        }
        
        .button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: all 0.3s ease;
            margin-right: 10px;
            margin-bottom: 10px;
        }
        
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .button.secondary {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        .button.success {
            background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
        }
        
        .button.error {
            background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
        }
        
        .results-section {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .result-success {
            background: #e8f5e8;
            border: 1px solid #4caf50;
            color: #2e7d32;
            padding: 15px;
            border-radius: 6px;
            margin-top: 10px;
        }
        
        .result-error {
            background: #ffebee;
            border: 1px solid #f44336;
            color: #c62828;
            padding: 15px;
            border-radius: 6px;
            margin-top: 10px;
        }
        
        .verification-section {
            background: linear-gradient(135deg, #fff3e0 0%, #f3e5f5 100%);
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
            border: 2px solid #ff9800;
            box-shadow: 0 4px 8px rgba(255, 152, 0, 0.1);
        }
        
        .verification-section h4 {
            color: #e65100;
            margin-bottom: 10px;
        }
        
        .verification-section p {
            color: #bf360c;
            font-weight: 500;
            margin-bottom: 15px;
        }
        
        .verification-buttons {
            display: flex;
            gap: 15px;
            margin: 15px 0;
        }
        
        .verification-result {
            padding: 15px;
            border-radius: 6px;
            margin-top: 15px;
            font-weight: bold;
        }
        
        .verification-correct {
            background: #e8f5e8;
            border: 2px solid #4caf50;
            color: #2e7d32;
        }
        
        .verification-incorrect {
            background: #ffebee;
            border: 2px solid #f44336;
            color: #c62828;
        }
        
        .summary-section {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .summary-container {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-top: 15px;
            border: 1px solid #ddd;
        }
        
        .summary-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #2196f3;
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #1976d2;
        }
        
        .stat-label {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        
        .test-item {
            background: #f8f9fa;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid #ddd;
        }
        
        .test-item.success {
            border-left-color: #4caf50;
        }
        
        .test-item.error {
            border-left-color: #f44336;
        }
        
        .test-item.passed {
            background: #e8f5e8;
        }
        
        .test-item.failed {
            background: #ffebee;
        }
        
        .test-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .test-name {
            font-weight: bold;
            font-size: 1.1em;
        }
        
        .test-status {
            font-size: 0.9em;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        .status-passed {
            background: #4caf50;
            color: white;
        }
        
        .status-failed {
            background: #f44336;
            color: white;
        }
        
        .status-unverified {
            background: #ff9800;
            color: white;
        }
        
        .status-error {
            background: #9e9e9e;
            color: white;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .hidden {
            display: none;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-llm {
            background: #4caf50;
        }
        
        .status-rules {
            background: #ff9800;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Python Function Tester</h1>
            <p>Interactive web interface for testing Python functions</p>
            <div id="llm-status" class="hidden">
                <span class="status-indicator status-llm"></span>
                LLM-powered generation enabled
            </div>
        </div>
        
        <div class="main-content">
            <div class="sidebar">
                <h3>📋 Available Functions</h3>
                <div id="function-list" class="function-list">
                    <div class="loading"></div>
                    Loading functions...
                </div>
            </div>
            
            <div class="test-area">
                <div id="no-selection" class="function-info">
                    <h3>👈 Select a function to start testing</h3>
                    <p>Choose a function from the list on the left to see its details and start testing.</p>
                </div>
                
                <div id="function-details" class="hidden">
                    <div class="function-info">
                        <h3 id="function-title" class="function-title"></h3>
                        <p id="function-description" class="function-description"></p>
                    </div>
                    
                    <div class="parameters-section">
                        <h4 class="section-title">⚙️ Parameters</h4>
                        <div id="parameters-container"></div>
                        
                        <button class="button secondary" onclick="generateInputs()">
                            🤖 Auto-Generate Inputs
                        </button>
                        <button class="button success" onclick="runTest()">
                            ▶️ Run Test
                        </button>
                    </div>
                    
                    <div id="results-section" class="results-section hidden">
                        <h4 class="section-title">📊 Results</h4>
                        <div id="results-container"></div>
                        <div id="verification-section" class="verification-section hidden">
                            <h4 class="section-title">✅ Verification</h4>
                            <p>Is this the expected output?</p>
                            <div class="verification-buttons">
                                <button class="button success" onclick="markResult(true)">
                                    ✅ Correct
                                </button>
                                <button class="button error" onclick="markResult(false)">
                                    ❌ Incorrect
                                </button>
                            </div>
                            <div id="verification-result" class="verification-result hidden"></div>
                        </div>
                    </div>
                    
                    <div class="summary-section">
                        <h4 class="section-title">📈 Test Summary</h4>
                        <button class="button secondary" onclick="showTestSummary()">
                            📊 View Test Summary
                        </button>
                        <div id="summary-container" class="summary-container hidden"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let selectedFunction = null;
        let functionInfo = null;

        // Load functions on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadFunctions();
        });

        async function loadFunctions() {
            try {
                const response = await fetch('/api/functions');
                const functions = await response.json();
                
                const listContainer = document.getElementById('function-list');
                listContainer.innerHTML = '';
                
                functions.forEach(funcKey => {
                    const [path, name] = funcKey.split('::');
                    const item = document.createElement('div');
                    item.className = 'function-item';
                    item.onclick = () => selectFunction(funcKey);
                    
                    // Check if this is a method (contains a dot)
                    let displayName = name;
                    let itemClass = 'function-item';
                    
                    if (name.includes('.')) {
                        // This is a method
                        itemClass += ' method-item';
                        const [className, methodName] = name.split('.');
                        displayName = `${className}.${methodName}`;
                    }
                    
                    item.className = itemClass;
                    item.innerHTML = `
                        <div class="function-name">${displayName}</div>
                        <div class="function-path">${path}</div>
                    `;
                    listContainer.appendChild(item);
                });
            } catch (error) {
                console.error('Error loading functions:', error);
                document.getElementById('function-list').innerHTML = 
                    '<div style="color: red;">Error loading functions</div>';
            }
        }

        async function selectFunction(funcKey) {
            // Update UI selection
            document.querySelectorAll('.function-item').forEach(item => {
                item.classList.remove('selected');
            });
            event.target.closest('.function-item').classList.add('selected');
            
            selectedFunction = funcKey;
            
            try {
                const response = await fetch(`/api/function-info?key=${encodeURIComponent(funcKey)}`);
                functionInfo = await response.json();
                
                displayFunctionDetails();
            } catch (error) {
                console.error('Error loading function info:', error);
            }
        }

        function displayFunctionDetails() {
            document.getElementById('no-selection').classList.add('hidden');
            document.getElementById('function-details').classList.remove('hidden');
            
            // Display function/method name with appropriate styling
            let title = functionInfo.name;
            if (functionInfo.is_method) {
                const methodType = functionInfo.method_details.method_type;
                const typeLabel = methodType === 'static' ? ' (static)' : 
                                methodType === 'class' ? ' (class method)' : ' (instance method)';
                title += typeLabel;
            }
            
            document.getElementById('function-title').textContent = title;
            document.getElementById('function-description').textContent = 
                functionInfo.docstring || 'No description available';
            
            const container = document.getElementById('parameters-container');
            container.innerHTML = '';
            
            functionInfo.parameters.forEach(param => {
                const defaultValue = functionInfo.defaults[param];
                const classInfo = functionInfo.class_info[param];
                const inputDiv = document.createElement('div');
                inputDiv.className = 'parameter-input';
                
                if (classInfo) {
                    // Parameter expects a class instance
                    const suggestedText = classInfo.suggested ? ' (suggested)' : '';
                    inputDiv.innerHTML = `
                        <label class="parameter-label" for="param-${param}">
                            ${param} - ${classInfo.class_name} instance${suggestedText}
                        </label>
                        <div class="class-input-container">
                            <button type="button" class="button secondary" onclick="toggleClassInput('${param}')">
                                🏗️ Create ${classInfo.class_name}
                            </button>
                            <div id="class-inputs-${param}" class="class-inputs hidden">
                                ${classInfo.parameters.map(classParam => {
                                    const classDefault = classInfo.defaults[classParam];
                                    return `
                                        <div class="class-parameter">
                                            <label class="class-parameter-label">${classParam}${classDefault !== undefined ? ` (default: ${classDefault})` : ''}</label>
                                            <input type="text" id="class-${param}-${classParam}" class="parameter-field" 
                                                   placeholder="Enter ${classParam}">
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                            <input type="hidden" id="param-${param}" class="parameter-field">
                        </div>
                    `;
                } else {
                    // Regular parameter
                    inputDiv.innerHTML = `
                        <label class="parameter-label" for="param-${param}">
                            ${param}${defaultValue !== undefined ? ` (default: ${defaultValue})` : ''}
                        </label>
                        <input type="text" id="param-${param}" class="parameter-field" 
                               placeholder="Enter value for ${param}">
                    `;
                }
                container.appendChild(inputDiv);
            });
            
            // Hide results section
            document.getElementById('results-section').classList.add('hidden');
        }

        async function generateInputs() {
            if (!selectedFunction) return;
            
            try {
                const response = await fetch('/api/generate-inputs', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        function_key: selectedFunction
                    })
                });
                
                const inputs = await response.json();
                
                // Fill in the generated values
                Object.entries(inputs).forEach(([param, value]) => {
                    const input = document.getElementById(`param-${param}`);
                    if (input) {
                        input.value = typeof value === 'string' ? value : JSON.stringify(value);
                    }
                });
                
            } catch (error) {
                console.error('Error generating inputs:', error);
            }
        }

        async function runTest() {
            if (!selectedFunction) return;
            
            // Collect input values
            const inputs = {};
            functionInfo.parameters.forEach(param => {
                const classInfo = functionInfo.class_info[param];
                
                if (classInfo) {
                    // Handle class parameter
                    const classInputs = collectClassInputs(param, classInfo);
                    inputs[param] = classInputs;
                } else {
                    // Handle regular parameter
                    const input = document.getElementById(`param-${param}`);
                    let value = input.value.trim();
                    
                    if (!value && functionInfo.defaults[param] !== undefined) {
                        value = functionInfo.defaults[param];
                    } else if (value) {
                        // Try to parse as JSON, fallback to string
                        try {
                            value = JSON.parse(value);
                        } catch {
                            // Keep as string
                        }
                    } else {
                        value = null;
                    }
                    
                    inputs[param] = value;
                }
            });
            
            try {
                const response = await fetch('/api/test-function', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        function_key: selectedFunction,
                        inputs: inputs
                    })
                });
                
                const result = await response.json();
                displayResults(result);
                
            } catch (error) {
                console.error('Error running test:', error);
                displayResults({
                    success: false,
                    result: 'Network error occurred',
                    inputs_used: inputs
                });
            }
        }

        function displayResults(result) {
            const resultsSection = document.getElementById('results-section');
            const container = document.getElementById('results-container');
            const verificationSection = document.getElementById('verification-section');
            const verificationResult = document.getElementById('verification-result');
            
            // Store the result for verification
            lastTestResult = result;
            
            const resultClass = result.success ? 'result-success' : 'result-error';
            const icon = result.success ? '✅' : '❌';
            
            container.innerHTML = `
                <div class="${resultClass}">
                    <strong>${icon} ${result.success ? 'Success' : 'Error'}</strong>
                    <div style="margin-top: 10px;">
                        <strong>Inputs:</strong> ${JSON.stringify(result.inputs_used, null, 2)}
                    </div>
                    <div style="margin-top: 10px;">
                        <strong>Result:</strong> ${JSON.stringify(result.result, null, 2)}
                    </div>
                </div>
            `;
            
            // Show verification section only for successful results
            if (result.success) {
                verificationSection.classList.remove('hidden');
                verificationResult.classList.add('hidden');
                verificationResult.className = 'verification-result hidden';
            } else {
                verificationSection.classList.add('hidden');
            }
            
            resultsSection.classList.remove('hidden');
        }

        let lastTestResult = null;

        function toggleClassInput(paramName) {
            const classInputs = document.getElementById(`class-inputs-${paramName}`);
            const button = event.target;
            
            if (classInputs.classList.contains('hidden')) {
                classInputs.classList.remove('hidden');
                button.textContent = `🔽 Hide ${button.textContent.split(' ')[1]}`;
            } else {
                classInputs.classList.add('hidden');
                button.textContent = `🏗️ Create ${button.textContent.split(' ')[1]}`;
            }
        }

        function collectClassInputs(paramName, classInfo) {
            const classInputs = {};
            let hasValues = false;
            
            classInfo.parameters.forEach(classParam => {
                const input = document.getElementById(`class-${paramName}-${classParam}`);
                let value = input.value.trim();
                
                if (!value && classInfo.defaults[classParam] !== undefined) {
                    value = classInfo.defaults[classParam];
                } else if (value) {
                    // Try to parse as JSON, fallback to string
                    try {
                        value = JSON.parse(value);
                    } catch {
                        // Keep as string
                    }
                    hasValues = true;
                } else {
                    value = null;
                }
                
                classInputs[classParam] = value;
            });
            
            return hasValues ? { __class__: classInfo.class_name, __params__: classInputs } : null;
        }

        function markResult(isCorrect) {
            const verificationResult = document.getElementById('verification-result');
            
            if (isCorrect) {
                verificationResult.className = 'verification-result verification-correct';
                verificationResult.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.5em;">✅</span>
                        <div>
                            <strong>Test Passed!</strong>
                            <div style="font-weight: normal; margin-top: 5px;">
                                The function output matches the expected result.
                            </div>
                        </div>
                    </div>
                `;
            } else {
                verificationResult.className = 'verification-result verification-incorrect';
                verificationResult.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.5em;">❌</span>
                        <div>
                            <strong>Test Failed!</strong>
                            <div style="font-weight: normal; margin-top: 5px;">
                                The function output does not match the expected result.
                            </div>
                        </div>
                    </div>
                `;
            }
            
            verificationResult.classList.remove('hidden');
            
            // Send verification to backend
            if (lastTestResult && selectedFunction) {
                sendVerification(isCorrect);
            }
        }

        async function sendVerification(isCorrect) {
            try {
                const response = await fetch('/api/verify-result', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        function_key: selectedFunction,
                        is_correct: isCorrect,
                        inputs: lastTestResult.inputs_used,
                        result: lastTestResult.result
                    })
                });
                
                const result = await response.json();
                console.log('Verification logged:', result);
                
            } catch (error) {
                console.error('Error logging verification:', error);
            }
        }

        async function showTestSummary() {
            try {
                const response = await fetch('/api/test-summary');
                const summary = await response.json();
                
                const container = document.getElementById('summary-container');
                
                if (summary.total_tests === 0) {
                    container.innerHTML = '<p>No tests have been executed yet.</p>';
                } else {
                    container.innerHTML = `
                        <div class="summary-stats">
                            <div class="stat-card">
                                <div class="stat-number">${summary.total_tests}</div>
                                <div class="stat-label">Total Tests</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${summary.successful_executions}</div>
                                <div class="stat-label">Successful</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${summary.verified_passed}</div>
                                <div class="stat-label">Verified Passed</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${summary.verified_failed}</div>
                                <div class="stat-label">Verified Failed</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${summary.unverified}</div>
                                <div class="stat-label">Unverified</div>
                            </div>
                        </div>
                        
                        <h5>Test Details:</h5>
                        <div class="test-list">
                            ${summary.test_results.map((test, index) => {
                                let statusClass = 'error';
                                let statusText = 'ERROR';
                                let itemClass = 'error';
                                
                                if (test.success) {
                                    statusClass = 'success';
                                    itemClass = 'success';
                                    if (test.verification === 'PASSED') {
                                        statusText = 'PASSED';
                                        statusClass = 'passed';
                                        itemClass = 'passed';
                                    } else if (test.verification === 'FAILED') {
                                        statusText = 'FAILED';
                                        statusClass = 'failed';
                                        itemClass = 'failed';
                                    } else {
                                        statusText = 'UNVERIFIED';
                                        statusClass = 'unverified';
                                    }
                                }
                                
                                return `
                                    <div class="test-item ${itemClass}">
                                        <div class="test-header">
                                            <span class="test-name">${index + 1}. ${test.function_name}</span>
                                            <span class="test-status status-${statusClass}">${statusText}</span>
                                        </div>
                                        <div><strong>Input:</strong> ${JSON.stringify(test.inputs)}</div>
                                        <div><strong>Output:</strong> ${JSON.stringify(test.output)}</div>
                                        <div><strong>Time:</strong> ${test.timestamp}</div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    `;
                }
                
                container.classList.remove('hidden');
                
            } catch (error) {
                console.error('Error loading test summary:', error);
                document.getElementById('summary-container').innerHTML = 
                    '<div style="color: red;">Error loading test summary</div>';
            }
        }
    </script>
</body>
</html>
        """

    def log_message(self, format, *args):
        """Override to suppress default logging."""
        pass


def create_handler_class(tester):
    """Create a handler class with the tester instance."""

    def handler(*args, **kwargs):
        WebTestingHandler(*args, tester=tester, **kwargs)

    return handler


def start_web_interface(tester, port=8080):
    """Start the web interface server."""
    handler_class = create_handler_class(tester)

    try:
        server = HTTPServer(("localhost", port), handler_class)
        print(f"🌐 Web interface starting at http://localhost:{port}")
        print("Press Ctrl+C to stop the server")

        # Open browser automatically
        threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}")).start()

        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use. Try a different port with --port option")
        else:
            print(f"❌ Error starting server: {e}")


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Web Interface for Python Function Tester")
    parser.add_argument("--directory", "-d", default=".", help="Directory to search for Python files")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Port for web server (default: 8080)")
    parser.add_argument("--api-key", "-k", help="OpenAI API key for intelligent input generation")

    args = parser.parse_args()

    # Check for API key in environment
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")

    # Create tester instance and discover functions
    tester = FunctionTester(args.directory, api_key)
    print("🔍 Discovering functions and classes...")
    tester.discover_functions()

    if not tester.discovered_functions:
        print("❌ No functions found in the specified directory")
        exit(1)

    print(f"✅ Found {len(tester.discovered_functions)} functions and {len(tester.discovered_classes)} classes")
    if tester.discovered_classes:
        print("Available classes:", ", ".join(tester.discovered_classes.keys()))

    # Start web interface
    start_web_interface(tester, args.port)
