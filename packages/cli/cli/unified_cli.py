#!/usr/bin/env python3
"""
Unified AI Project CLI - 连接到统一AI后端的命令行界面
"""
import argparse
import requests
import json
import sys
import os

# Using the refactored client
from .client import UnifiedAIClient

class LegacyClientShim:
    pass  # kept for backward-compat if referenced elsewhere

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_version = "v1"
    
    def _make_request(self, method, endpoint, data=None):
        url = f"{self.base_url}/api/{self.api_version}/{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(url)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API Error: {e}")
            return None
    
    def health_check(self):
        return self._make_request("GET", "health")
    
    def chat(self, message, user_id="cli_user", session_id="cli_session"):
        data = {
            "text": message,
            "user_id": user_id,
            "session_id": session_id
        }
        return self._make_request("POST", "chat", data)
    
    def analyze_code(self, code, language="auto"):
        data = {
            "code": code,
            "language": language
        }
        return self._make_request("POST", "code", data)
    
    def search(self, query):
        data = {"query": query}
        return self._make_request("POST", "search", data)
    
    def generate_image(self, prompt, style="realistic"):
        data = {
            "prompt": prompt,
            "style": style
        }
        return self._make_request("POST", "image", data)
    
    def get_atlassian_status(self):
        return self._make_request("GET", "atlassian/status")
    
    def get_jira_projects(self):
        return self._make_request("GET", "atlassian/jira/projects")
    
    def get_jira_issues(self, jql="", limit=50):
        params = f"?jql={jql}&limit={limit}" if jql else f"?limit={limit}"
        return self._make_request("GET", f"atlassian/jira/issues{params}")
    
    def create_jira_issue(self, project_key, summary, description="", issue_type="Task"):
        data = {
            "project_key": project_key,
            "summary": summary,
            "description": description,
            "issue_type": issue_type
        }
        return self._make_request("POST", "atlassian/jira/issue", data)
    
    def get_confluence_spaces(self):
        return self._make_request("GET", "atlassian/confluence/spaces")
    
    def search_confluence(self, query, limit=25):
        params = f"?query={query}&limit={limit}"
        return self._make_request("GET", f"atlassian/confluence/search{params}")

def main():
    parser = argparse.ArgumentParser(description="Unified AI Project CLI")
    parser.add_argument("--url", default=os.environ.get("CLI_BASE_URL", "http://localhost:8000"), help="Backend API URL (or set CLI_BASE_URL)")
    parser.add_argument("--token", default=os.environ.get("CLI_TOKEN"), help="Auth token (or set CLI_TOKEN)")
    parser.add_argument("--timeout", type=int, default=int(os.environ.get("CLI_TIMEOUT", "10")), help="Request timeout in seconds (or set CLI_TIMEOUT)")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Health check command
    health_parser = subparsers.add_parser("health", help="Check system health")
    
    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Chat with AI")
    chat_parser.add_argument("message", help="Message to send to AI")
    chat_parser.add_argument("--user-id", default="cli_user", help="User ID")
    chat_parser.add_argument("--session-id", default="cli_session", help="Session ID")
    
    # Code analysis command
    code_parser = subparsers.add_parser("analyze", help="Analyze code")
    code_parser.add_argument("--code", help="Code to analyze")
    code_parser.add_argument("--file", help="File containing code to analyze")
    code_parser.add_argument("--language", default="auto", help="Programming language")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for information")
    search_parser.add_argument("query", help="Search query")
    
    # Image generation command
    image_parser = subparsers.add_parser("image", help="Generate image")
    image_parser.add_argument("prompt", help="Image generation prompt")
    image_parser.add_argument("--style", default="realistic", help="Image style")
    
    # Atlassian commands
    atlassian_parser = subparsers.add_parser("atlassian", help="Atlassian integration")
    atlassian_subparsers = atlassian_parser.add_subparsers(dest="atlassian_command", help="Atlassian commands")
    
    # Atlassian status
    atlassian_status_parser = atlassian_subparsers.add_parser("status", help="Check Atlassian CLI status")
    
    # Jira commands
    jira_parser = atlassian_subparsers.add_parser("jira", help="Jira operations")
    jira_subparsers = jira_parser.add_subparsers(dest="jira_command", help="Jira commands")
    
    jira_projects_parser = jira_subparsers.add_parser("projects", help="List Jira projects")
    
    jira_issues_parser = jira_subparsers.add_parser("issues", help="List Jira issues")
    jira_issues_parser.add_argument("--jql", default="", help="JQL query")
    jira_issues_parser.add_argument("--limit", type=int, default=10, help="Number of issues to return")
    
    jira_create_parser = jira_subparsers.add_parser("create", help="Create Jira issue")
    jira_create_parser.add_argument("project", help="Project key")
    jira_create_parser.add_argument("summary", help="Issue summary")
    jira_create_parser.add_argument("--description", default="", help="Issue description")
    jira_create_parser.add_argument("--type", default="Task", help="Issue type")
    
    # Confluence commands
    confluence_parser = atlassian_subparsers.add_parser("confluence", help="Confluence operations")
    confluence_subparsers = confluence_parser.add_subparsers(dest="confluence_command", help="Confluence commands")
    
    confluence_spaces_parser = confluence_subparsers.add_parser("spaces", help="List Confluence spaces")
    
    confluence_search_parser = confluence_subparsers.add_parser("search", help="Search Confluence content")
    confluence_search_parser.add_argument("query", help="Search query")
    confluence_search_parser.add_argument("--limit", type=int, default=10, help="Number of results to return")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize client
    client = UnifiedAIClient(base_url=args.url, token=args.token, timeout=args.timeout)
    
    if args.command == "health":
        print("🔍 Checking system health...")
        result = client.health_check()
        if args.json:
            print(json.dumps(result or {}, ensure_ascii=False, indent=2))
        else:
            if result:
                print(f"✅ System Status: {result.get('status', 'unknown')}")
                print(f"📅 Timestamp: {result.get('timestamp', 'unknown')}")
                if 'services' in result:
                    print("🔧 Services:")
                    for service in result['services']:
                        print(f"  - {service.get('name', 'Unknown')}: {service.get('status', 'unknown')}")
        
    elif args.command == "chat":
        print(f"💬 Sending message: {args.message}")
        result = client.chat(args.message, args.user_id, args.session_id)
        if args.json:
            print(json.dumps(result or {}, ensure_ascii=False, indent=2))
        else:
            if result:
                print(f"🤖 AI Response: {result.get('response_text', 'No response')}")
        
    elif args.command == "analyze":
        code_content = ""
        if args.file:
            try:
                with open(args.file, 'r', encoding='utf-8') as f:
                    code_content = f.read()
                print(f"📁 Analyzing file: {args.file}")
            except FileNotFoundError:
                print(f"❌ File not found: {args.file}")
                return
        elif args.code:
            code_content = args.code
            print("🔍 Analyzing provided code...")
        else:
            print("❌ Please provide either --code or --file")
            return
        
        result = client.analyze_code(code_content, args.language)
        if args.json:
            print(json.dumps(result or {}, ensure_ascii=False, indent=2))
        else:
            if result:
                print(f"📊 Analysis Result:")
                print(f"  Language: {result.get('language', 'unknown')}")
                if 'analysis' in result:
                    analysis = result['analysis']
                    if isinstance(analysis, dict) and 'result' in analysis:
                        print(f"  Result: {analysis['result']}")
                    else:
                        print(f"  Analysis: {analysis}")
        
    elif args.command == "search":
        print(f"🔎 Searching for: {args.query}")
        result = client.search(args.query)
        if args.json:
            print(json.dumps(result or {}, ensure_ascii=False, indent=2))
        else:
            if result:
                print(f"📋 Found {result.get('total', 0)} results:")
                for i, item in enumerate(result.get('results', []), 1):
                    print(f"  {i}. {item.get('title', 'No title')}")
                    print(f"     {item.get('snippet', 'No description')}")
                    print(f"     URL: {item.get('url', 'No URL')}")
                    print()
        
    elif args.command == "image":
        print(f"🎨 Generating image: {args.prompt}")
        result = client.generate_image(args.prompt, args.style)
        if args.json:
            print(json.dumps(result or {}, ensure_ascii=False, indent=2))
        else:
            if result:
                print(f"✅ Image generated successfully!")
                print(f"  Prompt: {result.get('prompt', 'unknown')}")
                print(f"  Style: {result.get('style', 'unknown')}")
                if 'image_url' in result:
                    print(f"  URL: {result['image_url']}")
                if 'result' in result:
                    print(f"  Result: {result['result']}")
        
    elif args.command == "atlassian":
        if not args.atlassian_command:
            print("❌ Please specify an Atlassian command")
            return
        
        if args.atlassian_command == "status":
            print("🔍 Checking Atlassian CLI status...")
            result = client.get_atlassian_status()
            if args.json:
                print(json.dumps(result or {}, ensure_ascii=False, indent=2))
            else:
                if result:
                    print(f"✅ ACLI Available: {result.get('acli_available', False)}")
                    print(f"📋 Version: {result.get('version', 'unknown')}")
                    print(f"📁 Path: {result.get('path', 'unknown')}")
        
        elif args.atlassian_command == "jira":
            if args.jira_command == "projects":
                print("📋 Getting Jira projects...")
                result = client.get_jira_projects()
                if result and result.get('success'):
                    projects = result.get('projects', [])
                    print(f"✅ Found {len(projects)} projects:")
                    for project in projects[:10]:  # Show first 10
                        if isinstance(project, dict):
                            print(f"  - {project.get('key', 'N/A')}: {project.get('name', 'N/A')}")
                        else:
                            print(f"  - {project}")
                else:
                    print(f"❌ Failed to get projects: {result.get('error', 'Unknown error') if result else 'No response'}")
            
            elif args.jira_command == "issues":
                print(f"🎫 Getting Jira issues (limit: {args.limit})...")
                if args.jql:
                    print(f"   JQL: {args.jql}")
                result = client.get_jira_issues(args.jql, args.limit)
                if result and result.get('success'):
                    issues = result.get('issues', [])
                    print(f"✅ Found {len(issues)} issues:")
                    for issue in issues:
                        if isinstance(issue, dict):
                            print(f"  - {issue.get('key', 'N/A')}: {issue.get('summary', 'N/A')}")
                        else:
                            print(f"  - {issue}")
                else:
                    print(f"❌ Failed to get issues: {result.get('error', 'Unknown error') if result else 'No response'}")
            
            elif args.jira_command == "create":
                print(f"🆕 Creating Jira issue in {args.project}...")
                result = client.create_jira_issue(args.project, args.summary, args.description, args.type)
                if result and result.get('success'):
                    issue_key = result.get('key', 'Unknown')
                    print(f"✅ Issue created: {issue_key}")
                else:
                    print(f"❌ Failed to create issue: {result.get('error', 'Unknown error') if result else 'No response'}")
        
        elif args.atlassian_command == "confluence":
            if args.confluence_command == "spaces":
                print("📚 Getting Confluence spaces...")
                result = client.get_confluence_spaces()
                if result and result.get('success'):
                    spaces = result.get('spaces', [])
                    print(f"✅ Found {len(spaces)} spaces:")
                    for space in spaces[:10]:  # Show first 10
                        if isinstance(space, dict):
                            print(f"  - {space.get('key', 'N/A')}: {space.get('name', 'N/A')}")
                        else:
                            print(f"  - {space}")
                else:
                    print(f"❌ Failed to get spaces: {result.get('error', 'Unknown error') if result else 'No response'}")
            
            elif args.confluence_command == "search":
                print(f"🔍 Searching Confluence for: {args.query}")
                result = client.search_confluence(args.query, args.limit)
                if result and result.get('success'):
                    content = result.get('content', [])
                    print(f"✅ Found {len(content)} results:")
                    for item in content:
                        if isinstance(item, dict):
                            print(f"  - {item.get('title', 'N/A')}")
                            print(f"    Type: {item.get('type', 'N/A')}")
                            if 'url' in item:
                                print(f"    URL: {item['url']}")
                        else:
                            print(f"  - {item}")
                        print()
                else:
                    print(f"❌ Failed to search: {result.get('error', 'Unknown error') if result else 'No response'}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()