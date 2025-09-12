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
        print("Usage: python gemini_review.py <api_key> <pr_number>")
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

    # Get repo info from env
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

    # Get diff content
    try:
        diff_url_content = pr_data.get('diff_url')
        if not diff_url_content:
            print("No diff URL found in PR data")
            return
            
        diff_response = requests.get(diff_url_content, headers=headers, timeout=30)
        if diff_response.status_code != 200:
            print(f"Failed to fetch diff: {diff_response.status_code}")
            return
        diff = diff_response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching diff: {e}")
        return

    # Get additional context: recent commits and key files
    changed_files = get_changed_files(owner, repo_name, pr_number, headers)
    recent_commits = get_recent_commits()
    key_files_content = get_key_files_content()
    related_files_content = get_related_files_content(changed_files)
    next_version, react_version = get_project_versions()

    # Optimize prompt size for free tier token limits
    context_section = f"""
    **Recent Commits (last 5):**
    {recent_commits[:1000]}  # Limit to 1k chars

    **Key Config Files:**
    """
    # Limit key files to most important ones
    important_files = ['package.json', 'tsconfig.json', 'next.config.js', 'next.config.mjs']
    for file in important_files:
        if file in key_files_content:
            content = key_files_content[file][:800]  # Limit each file to 800 chars
            context_section += f"\n**{file}:**\n```\n{content}\n```\n"

    # Limit related files context
    context_section += "\n**Related Files:**\n"
    for file, content in list(related_files_content.items())[:2]:  # Only 2 files
        context_section += f"\n**{file}:**\n```\n{content[:600]}\n```\n"  # 600 chars max

    # Prepare prompt for Gemini (optimized for free tier token limits)
    prompt = f"""
    Review this Next.js {next_version}/React {react_version} PR. Focus on critical issues only.

    **Context:**
    {context_section[:2000]}  # Limit context to 2k chars

    **Core Review Areas:**
    - Critical bugs & security issues
    - Performance problems
    - React hooks & Next.js best practices
    - TypeScript errors
    - Code quality violations

    **PR Changes:**
    {diff[:6000]}  # Limit diff to 6k chars for free tier

    Provide concise, actionable feedback focusing on the most important issues only.
    """

    # Generate review with improved retry logic for rate limits
    max_retries = 5  # Increase retries for rate limits
    review = None
    base_delay = 5  # Start with 5 second delay
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            if response and response.text:
                review = response.text
                break
            else:
                print(f"Empty response from Gemini (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Waiting {delay} seconds before retry...")
                    time.sleep(delay)
        except Exception as e:
            error_msg = str(e)
            print(f"Error generating review (attempt {attempt + 1}): {error_msg}")
            
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
    
    if not review:
        print("Failed to generate review after multiple attempts")
        return

    # Post comment to PR
    success = post_review_comment(owner, repo_name, pr_number, review, headers)
    if success:
        print("✅ Review comment posted successfully")
    else:
        print("❌ Failed to post review comment")

def get_changed_files(owner, repo_name, pr_number, headers):
    """Get list of changed files in the PR"""
    files_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}/files"
    try:
        files_response = requests.get(files_url, headers=headers, timeout=30)
        if files_response.status_code != 200:
            print(f"Failed to fetch files: {files_response.status_code}")
            return []
        files_data = files_response.json()
        return [f['filename'] for f in files_data if f.get('filename')]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching files: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing files data: {e}")
        return []

def get_recent_commits():
    """Get recent commit history (limited for token optimization)"""
    try:
        result = subprocess.run(['git', 'log', '--oneline', '-5'],  # Reduced to 5 commits
                              capture_output=True, text=True, cwd='.', timeout=30)
        return result.stdout.strip() if result.returncode == 0 else "Unable to fetch recent commits."
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception):
        return "Unable to fetch recent commits."

def get_key_files_content():
    """Get content of key configuration files (optimized for token limits)"""
    key_files_content = {}
    # Prioritize most important config files for Next.js projects
    key_files = ['package.json', 'tsconfig.json', 'next.config.js', 'next.config.mjs']
    
    for file in key_files:
        try:
            if os.path.exists(file):
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()[:1000]  # Reduced to 1k chars per file
                    key_files_content[file] = content
        except (IOError, OSError, UnicodeDecodeError) as e:
            key_files_content[file] = f"File exists but unreadable: {e}"
    
    return key_files_content

def get_related_files_content(changed_files):
    """Get content of files related to changed files (optimized for token limits)"""
    related_files_content = {}
    
    # Simple heuristic: include files in same directories or similar types
    for changed_file in changed_files[:2]:  # Reduced to 2 changed files
        try:
            dir_path = os.path.dirname(changed_file)
            if dir_path and os.path.exists(dir_path):
                files_in_dir = os.listdir(dir_path)
                related = [f for f in files_in_dir if f.endswith(('.ts', '.tsx', '.js', '.jsx'))][:2]  # Only 2 related files
                
                for rel_file in related:
                    rel_path = os.path.join(dir_path, rel_file)
                    if (rel_path not in related_files_content and 
                        rel_path != changed_file and 
                        os.path.exists(rel_path)):
                        try:
                            with open(rel_path, 'r', encoding='utf-8', errors='ignore') as f:
                                related_files_content[rel_path] = f.read()[:800]  # Reduced to 800 chars
                        except (IOError, OSError, UnicodeDecodeError):
                            pass
        except (OSError, Exception):
            continue
    
    return related_files_content

def get_project_versions():
    """Extract Next.js and React versions from package.json"""
    next_version = "15.x"  # Default
    react_version = "19.x"  # Default
    
    try:
        if os.path.exists('package.json'):
            with open('package.json', 'r', encoding='utf-8') as f:
                package_data = json.load(f)
                
                # Check dependencies and devDependencies
                deps = {**package_data.get('dependencies', {}), 
                       **package_data.get('devDependencies', {})}
                
                if 'next' in deps:
                    next_version = deps['next'].replace('^', '').replace('~', '')
                if 'react' in deps:
                    react_version = deps['react'].replace('^', '').replace('~', '')
                    
    except (IOError, OSError, json.JSONDecodeError, Exception):
        pass
    
    return next_version, react_version

def post_review_comment(owner, repo_name, pr_number, review, headers):
    """Post the review comment to the PR"""
    comment_url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{pr_number}/comments"
    comment_data = {
        "body": f"🤖 **Gemini AI Code Review**\n\n{review}"
    }
    
    try:
        comment_response = requests.post(comment_url, json=comment_data, headers=headers, timeout=30)
        return comment_response.status_code == 201
    except requests.exceptions.RequestException as e:
        print(f"Error posting comment: {e}")
        return False

if __name__ == "__main__":
    main()