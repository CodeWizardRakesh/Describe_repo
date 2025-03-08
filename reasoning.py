import os
import mimetypes
import google.generativeai as genai
import json
from datetime import datetime
import PyPDF2
import docx

# Set your Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"API Key: {GEMINI_API_KEY}")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")
genai.configure(api_key=GEMINI_API_KEY)

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "folder_memory.json")
print(f"Memory file path: {MEMORY_FILE}")

def read_file_content(file_path):
    file_type, _ = mimetypes.guess_type(file_path)
    content = ""
    try:
        if file_type == "text/plain":
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()[:1000]
        elif file_type == "application/pdf":
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                content = "".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())[:1000]
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(file_path)
            content = " ".join(p.text for p in doc.paragraphs)[:1000]
        else:
            content = "Content reading not supported for this file type."
    except Exception as e:
        content = f"Error reading file: {e}"
    return content

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
    file_contents = {}

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
            file_info = f"{file} ({file_type or 'Unknown'}, {file_size / 1024:.2f} KB)"
            details.append(file_info)
            file_contents[file_path] = read_file_content(file_path)

    print(f"Analysis complete. Files: {summary['total_files']}, Folders: {summary['total_folders']}")
    return summary, details, file_contents

def save_memory(folder_path, summary, details, file_contents, description):
    print(f"Saving memory for {folder_path}")
    memory = {
        "folder_path": folder_path,
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "details": details[:10],
        "file_contents": {k: v for k, v in list(file_contents.items())[:10]},
        "description": description  # Only description, no reasoning
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

def load_memory(folder_path):
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            memory = json.load(f)
            return memory.get(folder_path)
    return None

def describe_folder(folder_path, use_memory=True):
    folder_path = folder_path.strip('"')
    print(f"Describing folder: {folder_path}")
    
    # Check for cached memory
    if use_memory:
        cached_memory = load_memory(folder_path)
        if cached_memory:
            print(f"Using cached description from {cached_memory['timestamp']}")
            return cached_memory["description"], cached_memory["summary"], cached_memory["details"], cached_memory["file_contents"]

    # If no cached memory, analyze and generate description
    summary, details, file_contents = analyze_folder(folder_path)

    prompt = f"""
    Provide a concise summary of the following folder's contents based on this data:
    - Contains {summary['total_files']} files and {summary['total_folders']} subfolders.
    - Largest file: {summary['largest_file']} ({summary['largest_size'] / 1024:.2f} KB).
    - File types: {summary['file_types']}.
    - Files and snippets: {', '.join([f"{detail} - Content: '{file_contents.get(os.path.join(folder_path, detail.split(' ')[0]), 'N/A')}'" for detail in details[:10]])}.

    Response format:
    Summary: [Your summary here]
    """

    print("Generating description with Gemini API")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        description = response.text.replace("Summary:", "").strip()
    except Exception as e:
        print(f"API error: {e}")
        description = "Failed to generate description due to API issue. Folder analysis completed."

    save_memory(folder_path, summary, details, file_contents, description)
    return description, summary, details, file_contents

def reason_folder(folder_path, description, summary, details, file_contents):
    print(f"Reasoning about folder: {folder_path}")
    
    prompt = f"""
    You are an advanced reasoning AI. Based on the following folder data and its summary, provide step-by-step reasoning about:
    1. What this folder might represent and its purpose.
    2. Any patterns or insights you can infer.
    3. Suggestions for actions (e.g., organizing files, further analysis).

    Folder data:
    - Contains {summary['total_files']} files and {summary['total_folders']} subfolders.
    - Largest file: {summary['largest_file']} ({summary['largest_size'] / 1024:.2f} KB).
    - File types: {summary['file_types']}.
    - Files and snippets: {', '.join([f"{detail} - Content: '{file_contents.get(os.path.join(folder_path, detail.split(' ')[0]), 'N/A')}'" for detail in details[:10]])}.
    - Summary: {description}

    Response format:
    Reasoning: [Your step-by-step reasoning and suggestions here]
    """

    print("Generating reasoning with Gemini API")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        reasoning = response.text.replace("Reasoning:", "").strip()
    except Exception as e:
        print(f"API error: {e}")
        reasoning = f"Reasoning failed due to API issue: {e}"
    
    return reasoning

# Run the analysis and reasoning
folder_path = input("Enter folder path: ")
description, summary, details, file_contents = describe_folder(folder_path)
reasoning = reason_folder(folder_path, description, summary, details, file_contents)
print("\nFolder Description:\n", description)
print("\nReasoning:\n", reasoning)