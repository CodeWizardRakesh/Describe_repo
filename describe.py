import os
import mimetypes
import google.generativeai as genai
import json
from datetime import datetime

# Set your Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")
genai.configure(api_key=GEMINI_API_KEY)

# File to store memory (relative to script location)
MEMORY_FILE = os.path.join(os.path.dirname(__file__), "folder_memory.json")
print(f"Memory file path: {MEMORY_FILE}")

# Function to analyze folder contents
def analyze_folder(folder_path):
    print(f"Analyzing folder: {folder_path}")
    summary = {
        "total_files": 0,
        "total_folders": 0,
        "file_types": {},
        "largest_file": None,
        "largest_size": 0
    }
    details = []

    for root, dirs, files in os.walk(folder_path):
        summary["total_folders"] += len(dirs)
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            file_type, _ = mimetypes.guess_type(file_path)
            summary["total_files"] += 1
            if file_type:
                summary["file_types"][file_type] = summary["file_types"].get(file_type, 0) + 1
            if file_size > summary["largest_size"]:
                summary["largest_size"] = file_size
                summary["largest_file"] = file_path
            details.append(f"{file} ({file_type or 'Unknown'}, {file_size / 1024:.2f} KB)")

    print(f"Analysis complete. Files: {summary['total_files']}, Folders: {summary['total_folders']}")
    return summary, details

# Function to save memory
def save_memory(folder_path, summary, details, description):
    print(f"Saving memory for {folder_path}")
    memory = {
        "folder_path": folder_path,
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "details": details[:10],  # Limit details to first 10 for brevity
        "description": description
    }
    
    existing_memory = {}
    if os.path.exists(MEMORY_FILE):
        print("Loading existing memory file")
        try:
            with open(MEMORY_FILE, 'r') as f:
                existing_memory = json.load(f)
        except Exception as e:
            print(f"Error loading existing memory: {e}")

    existing_memory[folder_path] = memory

    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(existing_memory, f, indent=4)
        print(f"Memory saved to {MEMORY_FILE}")
    except Exception as e:
        print(f"Error saving memory: {e}")

# Function to load memory
def load_memory(folder_path):
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            memory = json.load(f)
            return memory.get(folder_path)
    return None

# Function to generate AI-based description
def describe_folder(folder_path, use_memory=True):
    print(f"Describing folder: {folder_path}")
    if use_memory:
        cached_memory = load_memory(folder_path)
        if cached_memory:
            print(f"Using cached memory from {cached_memory['timestamp']}")
            return cached_memory["description"]

    summary, details = analyze_folder(folder_path)

    prompt = f"""
    The folder contains {summary['total_files']} files and {summary['total_folders']} subfolders.
    The largest file is {summary['largest_file']} ({summary['largest_size'] / 1024:.2f} KB).
    The types of files present include: {summary['file_types']}.

    Here is a list of files:
    {', '.join(details[:10])}...

    Describe this folder's content in a human-like summary.
    """

    print("Generating description with Gemini API")
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    description = response.text

    save_memory(folder_path, summary, details, description)
    return description

# Run the analysis
folder_path = input("Enter folder path: ")
description = describe_folder(folder_path)
print("\nFolder Description:\n", description)