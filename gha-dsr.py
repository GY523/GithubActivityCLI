'''
Github User Activity CLI
Fetches and displays recent activity for a Github user.
'''

import sys
import json
import urllib.request
import urllib.error
from datetime import datetime

def fetch_user_events(username):
    """Fetch recent events for a Github user from the public API."""
    url = f"https://api.github.com/users/{username}/events"

    try:
        # Add user-agent header as required by by Github API
        request = urllib.request.Request(url)
        request.add_header('User-Agent', 'github-activity-cli')
        request.add_header('Accept', 'application/vnd.github.v3+json')

        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status == 200:
                data = response.read().decode('utf-8')
                return json.loads(data)
            else:
                print(f'Error: Received status code {response.status}')
                return None
            
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Error: User '{username}' not found")
        elif e.code == 403:
            print('Error: API rate limit exceeded. Try again later.')
        else:
            print(f"Error {e.code}: {e.reason}")
        return None

    except urllib.error.URLError as e:
        print(f"Error: Could not connect to GitHub API - {e.reason}")
        return None
    except json.JSONDecodeError:
        print("Error: Invalid response from Github API")
        return None


def format_event(event, repo_events: dict):
    """Format a single event into a human-readable string"""
    event_type = event.get('type', 'UnknownEvent')
    repo_name = event.get('repo', {}).get('name', 'unknown-repo')
    created_at = event.get('created_at', '')

    # Count the number of each event types based on the repository
    # Set the key as repository name first if not exist.
    repo_events.setdefault(repo_name, {})
    # repo_event = {roadmap: {}}
    repo_events[repo_name].setdefault(event_type, 0)
    # repo_event = {roadmap: {pushEvent: 0}}
    repo_events[repo_name][event_type] += 1
    # repo_event = {roadmap: {pushEvent: 1}}

    # {roadmap: {event_type: 0 }}

    # Format the timestamp
    try: 
        timestamp = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ')
        time_ago = format_time_ago(timestamp)
    except (ValueError, TypeError):
        time_ago = 'unknown time'

    # Format based on event type
    if event_type == 'PushEvent':
        # Add one event into the list value of a repo
        return f"- Committed to {repo_name} {time_ago}"

    elif event_type == "IssuesEvent":
        action = event.get('payload', {}).get('action', 'opened')
        return f"- {action.capitalize()} an issue in {repo_name} {time_ago}"
    
    elif event_type == 'WatchEvent':
        return f"- Starred {repo_name} {time_ago}"
    
    elif event_type == "ForkEvent":
        action = event.get('payload', {}).get('action', 'forked')
        forkee = event.get('payload', {}).get('forkee', {}).get('name', 'unknown-repo')
        return f"- {action} {repo_name} to {forkee} {time_ago}"
    
    elif event_type == "CreateEvent":
        ref_type = event.get('payload', {}).get('ref_type', 'repository')
        ref = event.get('payload', {}).get('ref', '')
        if ref:
            return f"- Created {ref_type} {ref} in {repo_name} {time_ago}"
        return f"- Created {ref_type} in {repo_name} {time_ago}"
    
    elif event_type == 'PullRequestEvent':
        action = event.get('payload', {}).get('action', 'opened')
        pr_title = event.get('payload', {}).get('pull_request', {}).get('title', '')
        return f"- {action.capitalize()} a pull request in {repo_name}: \"{pr_title}\" {time_ago}"
    
    elif event_type == 'DeleteEvent':
        ref_type = event.get('payload', {}).get('ref_type', 'branch')
        ref = event.get('payload', {}).get('ref', '')
        return f"- Deleted {ref_type} {ref} in {repo_name} {time_ago}"
    
    elif event_type == "MemberEvent":
        action = event.get('payload', {}).get('action', 'added')
        member = event.get('payload', {}).get('member', {}).get('login', 'someone')
        return f"- {action.capitalize()} {member} as collaborator to {repo_name} {time_ago}"

    else:
        return f"- {event_type} in {repo_name} {time_ago}"
        
def format_time_ago(timestamp):
    """Convert timestamp to a relatvie time string"""
    now = datetime.now()
    diff = now - timestamp

    seconds = int(diff.total_seconds())

    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        minutes = seconds //60
        return f"{minutes} minute(s) ago"
    elif seconds < 86400:
        hours = seconds //3600
        return f"{hours} hour(s) ago"
    elif seconds < 604800:
        days = seconds // 86400
        return f"{days} days(s) ago"
    else: 
        return timestamp.strftime('%Y-%m-%d')

def main():
    repo_events = {}
    # Check command line arguments
    if len(sys.argv) != 2:
        print('Usage: gha-dsr.py <username>')
        print('Example: gha-dsr.py azaharizaman')
        sys.exit(1)

    username = sys.argv[1].strip()

    if not username:
        print("Error: Username cannot be empty")
        sys.exit(1)

    print(f'Recent Github activity for {username}:')
    print("-" * 50)

    events = fetch_user_events(username)

    if events is None:
        sys.exit(1)

    if not events:
        print('No recent activity found.')
        return
    
    # Display the most recent events (limit to 10 for readability)
    for i, event in enumerate(events):
        formatted = format_event(event, repo_events)
        if i < 10:
            print(formatted)

    if len(events) > 10:
        print(f"\n... and {len(events) - 10 } more events")

    # For lazy debugging: print(repo_events)
    print('-' * 50)
    print("Summary")
    print('-' * 50)

    # Learn lesson: if there is other part that needs the same response and decision making, OOP can be reduce the redundancy
    for repo, events  in repo_events.items():
        for event, count in events.items():
            if event=="PushEvent":
                print(f"- Pushed {count} commit(s) to {repo}.")
            elif event == "IssuesEvent":
                print(f"- Opened {count} issue(s) in {repo}.")
            elif event == "WatchEvent":
                print(f"- Starred {count} repositories.")
            elif event == "ForkEvent":
                print(f"- Forked {count} repositories.")
            elif event == "CreateEvent":
                print(f"- Created {count} branch, tag or repository.")
            elif event == "PullRequestEvent":
                print(f"- Opened or act {count} times on a pull request in {repo}.")
            elif event == "DeleteEvent":
                print(f"- Deleted {count} repositories.")
            elif event == "MemberEvent":
                print(f"- Act on member {count} times.")
            else:
                print(f"- {count} unspecified events")

if __name__ == "__main__":
    main()