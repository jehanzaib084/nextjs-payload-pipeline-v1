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
        model = genai.GenerativeModel('gemini-1.5-pro')
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
    recent_commits = get_recent_commits()
    key_files_content = get_key_files_content()
    related_files_content = get_related_files_content(pr_data)
    next_version, react_version = get_project_versions()

    # Prepare context section
    context_section = f"""
    **Recent Commit History (last 10 commits):**
    {recent_commits}

    **Key Configuration Files:**
    """
    for file, content in key_files_content.items():
        context_section += f"\n**{file}:**\n```\n{content}\n```\n"

    context_section += "\n**Related Files (similar to changed ones):**\n"
    for file, content in list(related_files_content.items())[:5]:  # Limit to 5
        context_section += f"\n**{file}:**\n```\n{content}\n```\n"

    # Prepare prompt for Gemini
    prompt = f"""
    Review the following code changes from a GitHub PR for a Next.js project. The project uses Next.js version {next_version} and React version {react_version}.

    Refer to the official Next.js documentation for version {next_version} best practices: https://nextjs.org/docs
    Refer to React documentation for version {react_version}: https://react.dev

    **Additional Context from Codebase:**
    {context_section}

    Identify any issues, bugs, security vulnerabilities, or improvements.
    Focus on:
    - Code quality and adherence to SDLC (Software Development Life Cycle) principles
    - DRY (Don't Repeat Yourself) - avoid code duplication
    - Use of latest React hooks and features where appropriate
    - Next.js best practices (e.g., proper use of SSR, ISR, API routes)
    - Potential bugs and security issues
    - Performance optimizations
    - TypeScript usage (if applicable)
    - Accessibility and maintainability

    For minor issues, suggest specific fixes. For major issues, flag them as critical.
    Encourage modern React patterns like hooks over class components, and Next.js 13+ app directory features if applicable.

    PR Diff:
    {diff[:10000]}  # Limit to 10k chars for diff
    """

    # Generate review with retry logic
    max_retries = 3
    review = None
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            if response and response.text:
                review = response.text
                break
            else:
                print(f"Empty response from Gemini (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(2)
        except Exception as e:
            print(f"Error generating review (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    if not review:
        print("Failed to generate review after multiple attempts")
        return

    # Post comment to PR
    success = post_review_comment(owner, repo_name, pr_number, review, headers)
    if success:
        print("✅ Review comment posted successfully")
    else:
        print("❌ Failed to post review comment")

def get_recent_commits():
    """Get recent commit history"""
    try:
        result = subprocess.run(['git', 'log', '--oneline', '-10'], 
                              capture_output=True, text=True, cwd='.', timeout=30)
        return result.stdout.strip() if result.returncode == 0 else "Unable to fetch recent commits."
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception):
        return "Unable to fetch recent commits."

def get_key_files_content():
    """Get content of key configuration files"""
    key_files_content = {}
    key_files = ['package.json', 'tsconfig.json', 'next.config.js', 'next.config.mjs', 
                 'tailwind.config.js', 'tailwind.config.mjs', 'eslint.config.js', 'eslint.config.mjs']
    
    for file in key_files:
        try:
            if os.path.exists(file):
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()[:2000]  # Limit to 2k chars per file
                    key_files_content[file] = content
        except (IOError, OSError, UnicodeDecodeError) as e:
            key_files_content[file] = f"File exists but unreadable: {e}"
    
    return key_files_content

def get_related_files_content(pr_data):
    """Get content of files related to changed files"""
    related_files_content = {}
    changed_files = pr_data.get('changed_files', [])
    
    # Simple heuristic: include files in same directories or similar types
    for changed_file in changed_files[:5]:  # Limit to 5 changed files
        try:
            dir_path = os.path.dirname(changed_file)
            if dir_path and os.path.exists(dir_path):
                files_in_dir = os.listdir(dir_path)
                related = [f for f in files_in_dir if f.endswith(('.ts', '.tsx', '.js', '.jsx'))][:3]
                
                for rel_file in related:
                    rel_path = os.path.join(dir_path, rel_file)
                    if (rel_path not in related_files_content and 
                        rel_path != changed_file and 
                        os.path.exists(rel_path)):
                        try:
                            with open(rel_path, 'r', encoding='utf-8', errors='ignore') as f:
                                related_files_content[rel_path] = f.read()[:1500]  # Limit
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