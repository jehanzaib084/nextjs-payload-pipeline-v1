#!/usr/bin/env python3
import os
import sys
import requests
import json
import subprocess
import google.generativeai as genai

def main():
    if len(sys.argv) < 3:
        print("Usage: python gemini_fix.py <api_key> <pr_number>")
        sys.exit(1)

    api_key = sys.argv[1]
    pr_number = sys.argv[2]

    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')

    # Get repo info
    repo = os.environ.get('GITHUB_REPOSITORY', 'jehanzaib084/nextjs-payload-pipeline-v1')
    owner, repo_name = repo.split('/')

    # Get PR diff
    diff_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}"
    headers = {'Authorization': f'token {os.environ.get("GITHUB_TOKEN", "")}'}
    pr_response = requests.get(diff_url, headers=headers)
    if pr_response.status_code != 200:
        print("Failed to fetch PR")
        return

    pr_data = pr_response.json()

    # Get changed files list
    files_url = f"{pr_url}/files"
    files_response = requests.get(files_url, headers=headers)
    if files_response.status_code != 200:
        print("Failed to fetch files")
        changed_files = []
    else:
        files_data = files_response.json()
        changed_files = [f['filename'] for f in files_data]

    # Get changed file contents
    files_content = {}
    for file in changed_files[:5]:  # Limit
        try:
            with open(file, 'r') as f:
                content = f.read()[:3000]  # Limit
                files_content[file] = content
        except:
            pass

    # Prepare prompt for Gemini
    prompt = f"""
    The following files have code quality issues (linting, formatting, TypeScript errors). Please fix them according to best practices.

    Changed Files:
    """
    for file, content in files_content.items():
        prompt += f"\n**{file}:**\n```\n{content}\n```\n"

    prompt += """
    Provide the fixed code for each file. Focus on:
    - Fixing syntax errors
    - Removing unused variables
    - Fixing formatting issues
    - Ensuring TypeScript compliance
    - Following React/Next.js best practices

    Output the fixes in the format:
    **File: filename**
    ```code
    fixed code
    ```
    """

    # Generate fixes
    response = model.generate_content(prompt)
    fixes = response.text

    # Parse and apply fixes (simple parsing)
    lines = fixes.split('\n')
    current_file = None
    code = []
    for line in lines:
        if line.startswith('**File: '):
            if current_file and code:
                apply_fix(current_file, '\n'.join(code))
            current_file = line.split('**File: ')[1].split('**')[0]
            code = []
        elif line.startswith('```') and code:
            # End of code block
            pass
        elif current_file and line.strip():
            code.append(line)

    if current_file and code:
        apply_fix(current_file, '\n'.join(code))

    # Commit fixes
    try:
        subprocess.run(['git', 'add', '.'], check=True, cwd='.')
        subprocess.run(['git', 'commit', '-m', 'Auto-fix code quality issues'], check=True, cwd='.')
        subprocess.run(['git', 'push'], check=True, cwd='.')
        print("Fixes committed and pushed")
    except:
        print("Failed to commit")

def apply_fix(file_path, fixed_code):
    try:
        with open(file_path, 'w') as f:
            f.write(fixed_code)
        print(f"Fixed {file_path}")
    except:
        print(f"Failed to fix {file_path}")

if __name__ == "__main__":
    main()