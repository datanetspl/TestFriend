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
