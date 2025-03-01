import os
import mimetypes
import google.generativeai as genai

# Set your Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Replace with your actual key
genai.configure(api_key=GEMINI_API_KEY)

# Function to analyze folder contents
def analyze_folder(folder_path):
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

            # Update summary
            summary["total_files"] += 1
            if file_type:
                summary["file_types"][file_type] = summary["file_types"].get(file_type, 0) + 1
            if file_size > summary["largest_size"]:
                summary["largest_size"] = file_size
                summary["largest_file"] = file_path

            details.append(f"{file} ({file_type or 'Unknown'}, {file_size / 1024:.2f} KB)")

    return summary, details

# Function to generate AI-based description
def describe_folder(folder_path):
    summary, details = analyze_folder(folder_path)

    # Create a prompt for AI
    prompt = f"""
    The folder contains {summary['total_files']} files and {summary['total_folders']} subfolders.
    The largest file is {summary['largest_file']} ({summary['largest_size'] / 1024:.2f} KB).
    The types of files present include: {summary['file_types']}.

    Here is a list of files:
    {', '.join(details[:10])}...

    Describe this folder's content in a human-like summary.
    """

    # Generate response using Gemini API
    model = genai.GenerativeModel('gemini-1.5-flash')  # Updated model name"D:\projects\RAG\Retrieval-Augmented-Generation\Knowledge_Base"
    response = model.generate_content(prompt)

    return response.text

# Run the analysis
folder_path = input("Enter folder path: ")
description = describe_folder(folder_path)
print("\nFolder Description:\n", description)