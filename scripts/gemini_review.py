#!/usr/bin/env python3
import os
import sys
import requests
import json
import subprocess
import google.generativeai as genai

def main():
    if len(sys.argv) < 3:
        print("Usage: python gemini_review.py <api_key> <pr_number>")
        sys.exit(1)

    api_key = sys.argv[1]
    pr_number = sys.argv[2]

    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')

    # Get repo info from env (assuming GITHUB_REPOSITORY is set)
    repo = os.environ.get('GITHUB_REPOSITORY', 'geoff-wp/designerv3')
    owner, repo_name = repo.split('/')

    # Get PR diff
    diff_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}"
    headers = {'Authorization': f'token {os.environ.get("GITHUB_TOKEN", "")}'}
    pr_response = requests.get(diff_url, headers=headers)
    if pr_response.status_code != 200:
        print("Failed to fetch PR")
        return

    pr_data = pr_response.json()
    diff_url = pr_data['diff_url']
    diff_response = requests.get(diff_url, headers=headers)
    if diff_response.status_code != 200:
        print("Failed to fetch diff")
        return

    diff = diff_response.text

    # Get additional context: recent commits and key files
    recent_commits = ""
    try:
        result = subprocess.run(['git', 'log', '--oneline', '-10'], capture_output=True, text=True, cwd='.')
        recent_commits = result.stdout.strip()
    except:
        recent_commits = "Unable to fetch recent commits."

    key_files_content = {}
    key_files = ['package.json', 'tsconfig.json', 'next.config.js', 'tailwind.config.mjs', 'eslint.config.mjs']
    for file in key_files:
        try:
            with open(file, 'r') as f:
                content = f.read()[:2000]  # Limit to 2k chars per file
                key_files_content[file] = content
        except:
            key_files_content[file] = "File not found or unreadable."

    # Get related files based on changed files in PR
    changed_files = pr_data.get('changed_files', [])
    related_files_content = {}
    # Simple heuristic: include files in same directories or similar types
    import os
    for changed_file in changed_files[:5]:  # Limit to 5 changed files
        dir_path = os.path.dirname(changed_file)
        if dir_path:
            try:
                files_in_dir = os.listdir(dir_path)
                related = [f for f in files_in_dir if f.endswith(('.ts', '.tsx', '.js', '.jsx'))][:3]  # Top 3 similar files
                for rel_file in related:
                    rel_path = os.path.join(dir_path, rel_file)
                    if rel_path not in related_files_content and rel_path != changed_file:
                        try:
                            with open(rel_path, 'r') as f:
                                related_files_content[rel_path] = f.read()[:1500]  # Limit
                        except:
                            pass
            except:
                pass

    # Prepare prompt for Gemini
    context_section = f"""
    **Recent Commit History (last 10 commits):**
    {recent_commits}

    **Key Configuration Files:**
    """
    for file, content in key_files_content.items():
        context_section += f"\n**{file}:**\n```\n{content}\n```\n"

    context_section += "\n**Related Files (top similar files to changed ones):**\n"
    for file, content in list(related_files_content.items())[:5]:  # Limit to 5
        context_section += f"\n**{file}:**\n```\n{content}\n```\n"

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

    # Generate review
    response = model.generate_content(prompt)
    review = response.text

    # Post comment to PR
    comment_url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{pr_number}/comments"
    comment_data = {
        "body": f"🤖 **Gemini AI Code Review**\n\n{review}"
    }
    comment_response = requests.post(comment_url, json=comment_data, headers=headers)
    if comment_response.status_code == 201:
        print("Review comment posted")
    else:
        print("Failed to post comment")

if __name__ == "__main__":
    main()