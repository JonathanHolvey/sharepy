import os


def load(filename):
    """Load and return the specified template file"""
    with open(os.path.join(os.path.dirname(__file__), filename), 'r') as file:
        return file.read()
