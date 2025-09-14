"""
Sample functions for testing the function tester tool.
"""

import torch
import torch.nn as nn
import torch.optim as optim


def reverse_string(text):
    """Reverse a string."""
    return text[::-1]


def factorial(n):
    """Calculate factorial of a number."""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)


def calculate_bmi(weight, height):
    """Calculate Body Mass Index given weight in kg and height in meters."""
    return weight / (height**2)


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


# Sample classes for testing class-based inputs
class Person:
    def __init__(self, name, age, email=None):
        self.name = name
        self.age = age
        self.email = email

    def __str__(self):
        return f"Person(name='{self.name}', age={self.age}, email='{self.email}')"

    def __repr__(self):
        return self.__str__()


def introduce(person: Person):
    """
    A method to introduce the person.
    """
    print(f"Hi, my name is {person.name} and I am {person.age} years old.")


class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def __str__(self):
        return f"Rectangle(width={self.width}, height={self.height})"

    def __repr__(self):
        return self.__str__()


class BankAccount:
    def __init__(self, account_number, balance=0.0, account_type="checking"):
        self.account_number = account_number
        self.balance = balance
        self.account_type = account_type

    def __str__(self):
        return f"BankAccount(number='{self.account_number}', balance={self.balance}, type='{self.account_type}')"

    def __repr__(self):
        return self.__str__()


# Functions that use class instances
def get_person_info(person):
    """Get formatted information about a person."""
    return f"{person.name} is {person.age} years old" + (f" (email: {person.email})" if person.email else "")


def calculate_rectangle_area(rect):
    """Calculate the area of a rectangle object."""
    return rect.width * rect.height


def compare_people_ages(person1, person2):
    """Compare the ages of two people."""
    if person1.age > person2.age:
        return f"{person1.name} is older than {person2.name}"
    elif person1.age < person2.age:
        return f"{person2.name} is older than {person1.name}"
    else:
        return f"{person1.name} and {person2.name} are the same age"


def create_in_out_sequences(data, seq_length):
    in_seq = []
    out_seq = []
    for i in range(len(data) - seq_length):
        in_seq.append(data[i : i + seq_length])
        out_seq.append(data[i + seq_length])
    return torch.stack(in_seq), torch.stack(out_seq)


# Classes with methods for testing
class Calculator:
    def __init__(self, precision=2):
        self.precision = precision
        self.history = []

    def add(self, a, b):
        """Add two numbers."""
        result = round(a + b, self.precision)
        self.history.append(f"{a} + {b} = {result}")
        return result

    def multiply(self, a, b):
        """Multiply two numbers."""
        result = round(a * b, self.precision)
        self.history.append(f"{a} * {b} = {result}")
        return result

    def get_history(self):
        """Get calculation history."""
        return self.history.copy()

    def clear_history(self):
        """Clear calculation history."""
        self.history.clear()
        return "History cleared"

    @staticmethod
    def is_even(number):
        """Check if a number is even (static method)."""
        return number % 2 == 0

    @classmethod
    def create_scientific(cls):
        """Create a scientific calculator with high precision (class method)."""
        return cls(precision=10)


class StringProcessor:
    def __init__(self, case_sensitive=True):
        self.case_sensitive = case_sensitive

    def process_text(self, text):
        """Process text based on case sensitivity setting."""
        if self.case_sensitive:
            return text
        else:
            return text.lower()

    def count_words(self, text):
        """Count words in text."""
        processed = self.process_text(text)
        return len(processed.split())

    def reverse_words(self, text):
        """Reverse the order of words in text."""
        words = text.split()
        return " ".join(reversed(words))

    @staticmethod
    def remove_punctuation(text):
        """Remove punctuation from text (static method)."""
        import string

        return text.translate(str.maketrans("", "", string.punctuation))


class BankAccountAdvanced:
    def __init__(self, account_number, initial_balance=0.0):
        self.account_number = account_number
        self.balance = initial_balance
        self.transaction_history = []

    def deposit(self, amount):
        """Deposit money into the account."""
        if amount <= 0:
            return "Invalid deposit amount"

        self.balance += amount
        self.transaction_history.append(f"Deposit: +${amount}")
        return f"Deposited ${amount}. New balance: ${self.balance}"

    def withdraw(self, amount):
        """Withdraw money from the account."""
        if amount <= 0:
            return "Invalid withdrawal amount"

        if amount > self.balance:
            return "Insufficient funds"

        self.balance -= amount
        self.transaction_history.append(f"Withdrawal: -${amount}")
        return f"Withdrew ${amount}. New balance: ${self.balance}"

    def get_balance(self):
        """Get current account balance."""
        return self.balance

    def get_transaction_history(self):
        """Get transaction history."""
        return self.transaction_history.copy()

    @staticmethod
    def validate_account_number(account_number):
        """Validate account number format (static method)."""
        return isinstance(account_number, str) and len(account_number) >= 8

    @classmethod
    def create_savings_account(cls, account_number):
        """Create a savings account with minimum balance (class method)."""
        return cls(account_number, initial_balance=100.0)
