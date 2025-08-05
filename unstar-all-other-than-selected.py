import requests
import os
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env

GITHUB_USERNAME = os.getenv("USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    'Accept': 'application/vnd.github+json',
    'Authorization': f'token {GITHUB_TOKEN}'
}

def clear_terminal():
    # For Windows
    if os.name == 'nt':
        os.system('cls')
    # For Linux and macOS
    else:
        os.system('clear')

clear_terminal()

def get_starred_repos():
    repos = []
    page = 1
    while True:
        url = 'https://api.github.com/user/starred'
        r = requests.get(url, headers=HEADERS, params={'per_page': 100, 'page': page})
        if r.status_code != 200 or not r.json():
            break
        repos += r.json()
        page += 1
    return repos

def unstar_repo(full_name):
    url = f'https://api.github.com/user/starred/{full_name}'
    r = requests.delete(url, headers=HEADERS)
    if r.status_code == 204:
        print(f'✅ Unstarred {full_name}')
    else:
        print(f'❌ Failed to unstar {full_name}: {r.status_code}')

def main():
    print("Loading repository data...\n")
    whitelist = set()
    starred_repos = get_starred_repos()
    clear_terminal()
    print("🎯 Enter GitHub usernames to keep. Type 'done' when finished.\n")
    owners_in_stars = {repo['owner']['login'] for repo in starred_repos}

    while True:
        username = input("Enter username to keep: ").strip()
        if username.lower() == 'done':
            break
        if username in owners_in_stars:
            print(f"✅ You have at least one repo starred by {username}. Added to whitelist.")
            whitelist.add(username)
        else:
            response = input(f"⚠️ You have no starred repos from {username}. Add anyway? (y/n): ").strip().lower()
            if response == 'y':
                whitelist.add(username)
                print(f"✅ Added {username} to whitelist.")
            else:
                print(f"⏭️ Skipping {username}.")

    confirm = input("\nType 'go' to begin unstarring all other repos: ").strip().lower()
    if confirm != 'go':
        print("❌ Cancelled.")
        return

    print("\n🚀 Starting unstar process...\n")
    for repo in starred_repos:
        owner = repo['owner']['login']
        full_name = repo['full_name']
        if owner not in whitelist:
            unstar_repo(full_name)

    print("\n✅ Finished unstar process.")

if __name__ == '__main__':
    main()
