import os
import requests
from dotenv import load_dotenv
import time

# Load GitHub token from .env
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN must be set in .env file")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def github_request(method, url, **kwargs):
    while True:
        response = requests.request(method, url, headers=HEADERS, **kwargs)
        if response.status_code == 403 and "X-RateLimit-Remaining" in response.headers:
            remaining = int(response.headers["X-RateLimit-Remaining"])
            if remaining == 0:
                reset_time = int(response.headers["X-RateLimit-Reset"])
                sleep_time = reset_time - int(time.time()) + 5
                print(f"Rate limit hit. Sleeping for {sleep_time} seconds...")
                time.sleep(sleep_time)
                continue
        if response.status_code in [200, 201, 204]:
            return response
        else:
            print(f"❌ Error: {response.status_code} -> {response.text}")
            return None

def get_all_user_repos(username):
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/repos"
        params = {"per_page": 100, "page": page}
        response = github_request("GET", url, params=params)
        if response is None:
            break
        data = response.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def star_repo(full_name):
    url = f"https://api.github.com/user/starred/{full_name}"
    response = github_request("PUT", url)
    if response and response.status_code == 204:
        print(f"⭐ Starred {full_name}")
    else:
        print(f"❌ Failed to star {full_name}")

def main():
    username = input("Enter the GitHub username to star all their repos: ").strip()
    if not username:
        print("❌ No username entered.")
        return

    print(f"🔍 Fetching repos from {username}...")
    repos = get_all_user_repos(username)
    print(f"📦 Found {len(repos)} repos.")

    for repo in repos:
        full_name = repo["full_name"]
        star_repo(full_name)
        time.sleep(1.5)  # Be nice to the API

    print("✅ Done!")

if __name__ == "__main__":
    main()
