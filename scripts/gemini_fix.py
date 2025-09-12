#!/usr/bin/env python3
import os
import sys
import requests
import json
import subprocess
import google.generativeai as genai
import time

def main():
    if len(sys.argv) < 3:
        print("Usage: python gemini_fix.py <api_key> <pr_number>")
        sys.exit(1)

    api_key = sys.argv[1]
    pr_number = sys.argv[2]

    if not api_key or api_key == "":
        print("Error: GEMINI_API_KEY is required")
        sys.exit(1)

    # Configure Gemini
    try:
        genai.configure(api_key=api_key)
        # Use Gemini 2.5 Flash for better free tier limits (10 RPM vs 5 RPM for Pro)
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        print(f"Error configuring Gemini: {e}")
        sys.exit(1)

    # Get repo info
    repo = os.environ.get('GITHUB_REPOSITORY', 'jehanzaib084/nextjs-payload-pipeline-v1')
    github_token = os.environ.get('GITHUB_TOKEN', '')
    
    if not github_token:
        print("Error: GITHUB_TOKEN is required")
        sys.exit(1)
    
    try:
        owner, repo_name = repo.split('/')
    except ValueError:
        print(f"Error: Invalid repository format: {repo}")
        sys.exit(1)

    # Get PR diff
    diff_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}"
    headers = {'Authorization': f'token {github_token}', 'Accept': 'application/vnd.github.v3+json'}
    
    try:
        pr_response = requests.get(diff_url, headers=headers, timeout=30)
        if pr_response.status_code != 200:
            print(f"Failed to fetch PR: {pr_response.status_code} - {pr_response.text}")
            return
        pr_data = pr_response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching PR data: {e}")
        return
    except json.JSONDecodeError as e:
        print(f"Error parsing PR data: {e}")
        return

    pr_data = pr_response.json()

    # Get changed files list
    files_url = f"{diff_url}/files"
    try:
        files_response = requests.get(files_url, headers=headers, timeout=30)
        if files_response.status_code != 200:
            print(f"Failed to fetch files: {files_response.status_code}")
            changed_files = []
        else:
            files_data = files_response.json()
            changed_files = [f['filename'] for f in files_data if f.get('filename')]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching files: {e}")
        changed_files = []
    except json.JSONDecodeError as e:
        print(f"Error parsing files data: {e}")
        changed_files = []

    if not changed_files:
        print("No changed files found or unable to fetch files")
        return

    # Get changed file contents (optimized for free tier)
    files_content = {}
    for file in changed_files[:3]:  # Reduced to 3 files to stay within token limits
        try:
            if os.path.exists(file):
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()[:2000]  # Reduced to 2k chars per file
                    files_content[file] = content
        except (IOError, OSError, UnicodeDecodeError) as e:
            print(f"Warning: Could not read file {file}: {e}")
            continue

    if not files_content:
        print("No readable files found in the changeset")
        return

    # Prepare prompt for Gemini (optimized for free tier token limits)
    prompt = f"""
    Fix code quality issues in these files. Focus on critical fixes only.

    Files with issues:
    """
    for file, content in files_content.items():
        prompt += f"\n**{file}:**\n```\n{content}\n```\n"

    prompt += """
    Fix only these issues:
    - Syntax errors
    - Unused variables
    - TypeScript errors
    - Critical formatting issues

    Output format:
    **File: filename**
    ```typescript
    fixed code here
    ```
    
    Provide complete, working file contents only.
    """

    # Generate fixes with improved retry logic for rate limits
    max_retries = 5  # Increase retries for rate limits
    base_delay = 5  # Start with 5 second delay
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            if response and response.text:
                fixes = response.text
                break
            else:
                print(f"Empty response from Gemini (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                else:
                    print("Failed to get valid response from Gemini")
                    return
        except Exception as e:
            error_msg = str(e)
            print(f"Error generating fixes (attempt {attempt + 1}): {error_msg}")
            
            # Handle rate limit errors specifically
            if "429" in error_msg or "quota" in error_msg.lower():
                if attempt < max_retries - 1:
                    # Extract retry delay from error if available
                    retry_delay = 60  # Default 60 seconds for rate limits
                    if "retry_delay" in error_msg:
                        try:
                            import re
                            delay_match = re.search(r'seconds: (\d+)', error_msg)
                            if delay_match:
                                retry_delay = int(delay_match.group(1)) + 5  # Add 5 sec buffer
                        except:
                            pass
                    
                    print(f"Rate limit hit. Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                else:
                    print("Rate limit exceeded. Consider using paid tier for higher limits.")
                    return
            else:
                # Non-rate-limit errors: use exponential backoff
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                else:
                    print("Failed to generate fixes after multiple attempts")
                    return

    # Parse and apply fixes (improved parsing)
    if not parse_and_apply_fixes(fixes):
        print("Failed to parse or apply fixes")
        return

    # Commit fixes with proper error handling
    commit_fixes()

def parse_and_apply_fixes(fixes):
    """Parse AI response and apply fixes to files"""
    lines = fixes.split('\n')
    current_file = None
    code_lines = []
    in_code_block = False
    fixes_applied = 0
    
    for line in lines:
        if line.startswith('**File: ') and '**' in line[8:]:
            # Save previous file if exists
            if current_file and code_lines:
                if apply_fix(current_file, '\n'.join(code_lines)):
                    fixes_applied += 1
            
            # Extract filename
            try:
                current_file = line.split('**File: ')[1].split('**')[0].strip()
                code_lines = []
                in_code_block = False
            except IndexError:
                print(f"Warning: Could not parse filename from: {line}")
                current_file = None
                
        elif line.startswith('```') and current_file:
            in_code_block = not in_code_block
            if not in_code_block and code_lines:
                # End of code block - apply fix
                if apply_fix(current_file, '\n'.join(code_lines)):
                    fixes_applied += 1
                code_lines = []
                current_file = None
                
        elif in_code_block and current_file:
            code_lines.append(line)
    
    # Handle last file if no closing ```
    if current_file and code_lines:
        if apply_fix(current_file, '\n'.join(code_lines)):
            fixes_applied += 1
    
    print(f"Applied fixes to {fixes_applied} files")
    return fixes_applied > 0

def apply_fix(file_path, fixed_code):
    """Apply fix to a specific file"""
    try:
        # Validate file path
        if not file_path or '..' in file_path or file_path.startswith('/'):
            print(f"Warning: Skipping potentially unsafe file path: {file_path}")
            return False
            
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Warning: File does not exist: {file_path}")
            return False
            
        # Backup original file
        backup_path = f"{file_path}.backup"
        try:
            with open(file_path, 'r', encoding='utf-8') as original:
                with open(backup_path, 'w', encoding='utf-8') as backup:
                    backup.write(original.read())
        except Exception as e:
            print(f"Warning: Could not create backup for {file_path}: {e}")
        
        # Apply fix
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_code)
        
        print(f"✅ Fixed {file_path}")
        return True
        
    except (IOError, OSError, UnicodeDecodeError) as e:
        print(f"❌ Failed to fix {file_path}: {e}")
        # Restore backup if it exists
        backup_path = f"{file_path}.backup"
        if os.path.exists(backup_path):
            try:
                with open(backup_path, 'r', encoding='utf-8') as backup:
                    with open(file_path, 'w', encoding='utf-8') as original:
                        original.write(backup.read())
                print(f"Restored backup for {file_path}")
            except Exception as restore_e:
                print(f"Failed to restore backup for {file_path}: {restore_e}")
        return False

def commit_fixes():
    """Commit and push fixes with proper error handling"""
    try:
        # Check if there are any changes
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd='.', timeout=30)
        if not result.stdout.strip():
            print("No changes to commit")
            return
            
        # Configure git user if not set
        try:
            subprocess.run(['git', 'config', 'user.email', 'github-actions@github.com'], 
                         check=True, cwd='.', timeout=10)
            subprocess.run(['git', 'config', 'user.name', 'GitHub Actions'], 
                         check=True, cwd='.', timeout=10)
        except subprocess.CalledProcessError:
            pass  # User might already be configured
            
        # Add, commit and push
        subprocess.run(['git', 'add', '.'], check=True, cwd='.', timeout=30)
        
        commit_result = subprocess.run(['git', 'commit', '-m', 'chore: auto-fix code quality issues'], 
                                     cwd='.', timeout=30, capture_output=True, text=True)
        if commit_result.returncode != 0:
            print(f"Commit failed: {commit_result.stderr}")
            return
            
        push_result = subprocess.run(['git', 'push'], cwd='.', timeout=60, 
                                   capture_output=True, text=True)
        if push_result.returncode == 0:
            print("✅ Fixes committed and pushed successfully")
        else:
            print(f"❌ Push failed: {push_result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ Git operation timed out")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error during commit: {e}")

if __name__ == "__main__":
    main()
