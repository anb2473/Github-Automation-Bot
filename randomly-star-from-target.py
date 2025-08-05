import os
import requests
import time
import random
from dotenv import load_dotenv

# Load environment variable
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise ValueError("Missing GITHUB_TOKEN in .env file")

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
                wait = reset_time - int(time.time()) + 5
                print(f"Rate limit hit. Sleeping for {wait} seconds.")
                time.sleep(wait)
                continue
        if response.status_code in [200, 204]:
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
    username = input("Enter the GitHub username: ").strip()
    percent_input = input("Enter percent of repos to star (0-100): ").strip()

    try:
        percent = float(percent_input)
        if not (0 <= percent <= 100):
            raise ValueError()
    except ValueError:
        print("❌ Invalid percentage.")
        return

    repos = get_all_user_repos(username)
    total = len(repos)

    if total == 0:
        print("❌ No repos found.")
        return

    num_to_star = max(1, int((percent / 100.0) * total))
    print(f"📦 Found {total} repos. Randomly selecting {num_to_star} to star...")

    selected_repos = random.sample(repos, num_to_star)

    for repo in selected_repos:
        full_name = repo["full_name"]
        star_repo(full_name)
        time.sleep(random.uniform(1.5, 3.5))  # polite delay

    print("✅ Done.")

if __name__ == "__main__":
    main()
