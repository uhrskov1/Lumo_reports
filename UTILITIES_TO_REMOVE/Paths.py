import os

# Define MAIN_ROOT as the root directory of the project
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory of the current file
MAIN_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))  # Adjust based on your structure


# Function for joining the main root with relative path
def getPathFromMainRoot(*path):
    return os.path.join(MAIN_ROOT, *path)
