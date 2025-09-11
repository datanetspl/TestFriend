"""
Sample functions for testing the function tester tool.
"""


def add_numbers(a, b):
    """Add two numbers together."""
    return a + b


def multiply(x, y=1):
    """Multiply two numbers, with y defaulting to 1."""
    return x * y


def reverse_string(text):
    """Reverse a string."""
    return text[::-1]


def calculate_area(length, width):
    """Calculate the area of a rectangle."""
    return length * width


def greet(name, greeting="Hello"):
    """Generate a greeting message."""
    return f"{greeting}, {name}!"


def factorial(n):
    """Calculate factorial of a number."""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)


def is_even(number):
    """Check if a number is even."""
    return number % 2 == 0


def calculate_bmi(weight, height):
    """Calculate Body Mass Index given weight in kg and height in meters."""
    return weight / (height**2)


def send_email(recipient_email, subject, message):
    """Simulate sending an email (returns confirmation message)."""
    return f"Email sent to {recipient_email} with subject '{subject}'"


def process_user_data(name, age, is_active=True):
    """Process user data and return a summary."""
    status = "active" if is_active else "inactive"
    return f"User {name} (age {age}) is {status}"


def calculate_distance(x1, y1, x2, y2):
    """Calculate Euclidean distance between two points."""
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def format_temperature(temp_celsius):
    """Convert temperature from Celsius to Fahrenheit and format."""
    fahrenheit = (temp_celsius * 9 / 5) + 32
    return f"{temp_celsius}°C = {fahrenheit}°F"


def validate_percentage(percentage):
    """Check if a percentage value is valid (0-100)."""
    return 0 <= percentage <= 100


def process_numbers_list(numbers):
    """Calculate sum and average of a list of numbers."""
    if not numbers:
        return {"sum": 0, "average": 0}
    total = sum(numbers)
    return {"sum": total, "average": total / len(numbers)}
