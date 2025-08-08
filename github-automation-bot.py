# Analyze account to provide details on how to make your account more proffesional

import requests
import os
from dotenv import load_dotenv
import pyfiglet
from rich.console import Console
from rich.text import Text
from datetime import datetime, timezone
import base64
import time

pastel_rainbow = ["#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9", "#BAE1FF", "#D1BAFF", "#FFBAF2"]

load_dotenv()

console = Console()

def clear_terminal():
    # For Windows
    if os.name == 'nt':
        os.system('cls')
    # For Linux and macOS
    else:
        os.system('clear')

clear_terminal()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
USER_NAME = os.getenv("USER_NAME")
EMAIL = os.getenv("EMAIL")
LOAD_REPO_DELAY = float(os.getenv("LOAD_REPO_DELAY"))
NUM_OF_PAGES = int(os.getenv("NUM_OF_PAGES"))

if not GITHUB_TOKEN or not USER_NAME or not EMAIL or not LOAD_REPO_DELAY or not NUM_OF_PAGES:
    raise ValueError("GITHUB_TOKEN, USER_NAME, EMAIL, NUM_OF_PAGES, and LOAD_REPO_DELAY must be set in the .env file")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def github_request(method, url, **kwargs):
    while True:
        response = requests.request(method, url, headers=HEADERS, **kwargs)

        # Handle rate limiting
        if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers:
            remaining = int(response.headers.get('X-RateLimit-Remaining', 1))
            reset = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
            if remaining == 0:
                wait_time = reset - int(time.time()) + 1
                print(f"⏳ Rate limit exceeded. Waiting {wait_time} seconds to retry...")
                time.sleep(wait_time)
                continue

        # Handle unexpected rate-limit blocks without headers
        if response.status_code == 403 and "rate limit" in response.text.lower():
            print("⛔️ Rate limit hit but no headers found. Waiting 60 seconds...")
            time.sleep(60)
            continue

        # Retry on transient errors (e.g., 502, 503)
        if response.status_code in (502, 503):
            print(f"⚠️ GitHub temporarily unavailable (status {response.status_code}). Retrying in 10 seconds...")
            time.sleep(10)
            continue

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"❌ Error fetching {url}: {err}")
            return None

        return response

def check_repo_files(repo_full_name):
    readme_url = f"https://api.github.com/repos/{repo_full_name}/readme"
    license_url = f"https://api.github.com/repos/{repo_full_name}/license"

    has_readme = github_request("GET", readme_url, push_err=False) is not None
    has_license = github_request("GET", license_url, push_err=False) is not None

    return has_readme, has_license

def get_user_repos():
    all_repos = []
    page = 1
    while page <= NUM_OF_PAGES:
        url = f"https://api.github.com/user/repos?per_page=100&page={page}"
        response = github_request("GET", url)
        if not response:
            break
        repos = response.json()
        if not repos:
            break
        all_repos.extend(repos)
        if len(repos) < 100:
            break
        page += 1
    return all_repos


def check_repo_readme_license(repos):
    for repo in repos:
            full_name = repo["full_name"]
            has_readme, has_license = check_repo_files(full_name)

            print(f"\n📦 Repo: {full_name}")
            print(f"   📄 README: {'✅ Present' if has_readme else '❌ Missing'}")
            print(f"   📝 LICENSE: {'✅ Present' if has_license else '❌ Missing'}")

def archive_repo(repo_name):
    # Rename repo with _ prefix if not already
    if not repo_name.startswith("_"):
        new_name = f"_{repo_name}"
        url = f"https://api.github.com/repos/{USER_NAME}/{repo_name}"
        rename_payload = {"name": new_name}
        response = github_request("PATCH", url, json=rename_payload)
        if response is None or response.status_code != 200:
            print(f"❌ Failed to rename repo {repo_name}")
            return
        print(f"✅ Renamed repo {repo_name} to {new_name}")
        repo_name = new_name

    # Check if README exists
    readme_url = f"https://api.github.com/repos/{USER_NAME}/{repo_name}/contents/README.md"
    response = github_request("GET", readme_url)

    update_message = "This project is no longer being maintained\n\n"
    now_iso = datetime.utcnow().isoformat() + "Z"

    if response and response.status_code == 200:
        # README exists — get current content & sha for update
        readme_data = response.json()
        sha = readme_data["sha"]
        content = base64.b64decode(readme_data["content"]).decode("utf-8")

        # Prepend the message if not already present
        if not content.startswith(update_message):
            new_content = update_message + content
            encoded_content = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
            update_payload = {
                "message": "Prepend maintenance notice to README",
                "content": encoded_content,
                "sha": sha,
                "committer": {"name": USER_NAME, "email": EMAIL},
                "branch": "main"
            }
            update_resp = github_request("PUT", readme_url, json=update_payload)
            if update_resp and update_resp.status_code == 200:
                print("✅ Updated README with maintenance notice.")
            else:
                print("❌ Failed to update README.")
        else:
            print("ℹ️ README already contains maintenance notice.")
    else:
        # README missing — create new one
        encoded_content = base64.b64encode(update_message.encode("utf-8")).decode("utf-8")
        create_payload = {
            "message": "Create README with maintenance notice",
            "content": encoded_content,
            "committer": {"name": USER_NAME, "email": f"{USER_NAME}@users.noreply.github.com"},
            "branch": "main"
        }
        create_resp = github_request("PUT", readme_url, json=create_payload)
        if create_resp and create_resp.status_code == 201:
            print("✅ Created new README with maintenance notice.")
        else:
            print("❌ Failed to create README.")

    # Archive the repo
    repo_url = f"https://api.github.com/repos/{USER_NAME}/{repo_name}"
    archive_payload = {"archived": True}
    archive_resp = github_request("PATCH", repo_url, json=archive_payload)
    if archive_resp and archive_resp.status_code == 200:
        print(f"✅ Archived repo {repo_name}.")
    else:
        print(f"❌ Failed to archive repo {repo_name}.")

def print_repo_summary(repos):
    for repo in repos:
        name = repo.get("name", "N/A")
        created_at = repo.get("created_at", "N/A")
        archived = repo.get("archived", False)
        public = not repo.get("private", True)

        visibility = "🌐 Public" if public else "🔒 Private"
        archive_status = "📦 Archived" if archived else "📂 Active"

        print(f"📁 {name} | Created: {created_at} | {archive_status} | {visibility}")
        time.sleep(LOAD_REPO_DELAY)

def find_private_repos(repos):
    private_repos = [repo for repo in repos if repo.get("private", False)]
    if not private_repos:
        print("🔒 No private repositories found.")
        return
    
    for repo in private_repos:
        name = repo.get("name", "N/A")
        created_at = repo.get("created_at", "N/A")
        archived = repo.get("archived", False)

        archive_status = "📦 Archived" if archived else "📂 Active"
        print(f"🔒 {name} | Created: {created_at} | {archive_status}")
        time.sleep(LOAD_REPO_DELAY)

def find_public_repos(repos):
    public_repos = [repo for repo in repos if not repo.get("private", True)]
    if not public_repos:
        print("🌐 No public repositories found.")
        return
    
    for repo in public_repos:
        name = repo.get("name", "N/A")
        created_at = repo.get("created_at", "N/A")
        archived = repo.get("archived", False)

        archive_status = "📦 Archived" if archived else "📂 Active"
        print(f"🌐 {name} | Created: {created_at} | {archive_status}")
        time.sleep(LOAD_REPO_DELAY)

def make_repo_public(repo_name):
    url = f"https://api.github.com/repos/{USER_NAME}/{repo_name}"
    payload = {"private": False}
    
    response = github_request("PATCH", url, json=payload)
    if response and response.status_code == 200:
        print(f"🌐 Repo '{repo_name}' is now **public** ✅")
    else:
        print(f"❌ Failed to make '{repo_name}' public.")

def make_repo_private(repo_name):
    url = f"https://api.github.com/repos/{USER_NAME}/{repo_name}"
    payload = {"private": True}
    
    response = github_request("PATCH", url, json=payload)
    if response and response.status_code == 200:
        print(f"🔒 Repo '{repo_name}' is now **private** ✅")
    else:
        print(f"❌ Failed to make '{repo_name}' private.")

def find_unarchived_repos(repos):
    unarchived = [repo for repo in repos if not repo.get("archived", False)]

    print("\n📂 Unarchived Repositories")
    print("────────────────────────────")
    if not unarchived:
        print("🟨 No unarchived repositories found.")
        return

    for repo in unarchived:
        visibility = "🔒 Private" if repo.get("private") else "🌐 Public"
        print(f"📁 {repo['name']} | {visibility} | Created: {repo['created_at']}")
        time.sleep(LOAD_REPO_DELAY)

def find_archived_repos(repos):
    archived = [repo for repo in repos if repo.get("archived", False)]

    print("\n📦 Archived Repositories")
    print("─────────────────────────")
    if not archived:
        print("🟨 No archived repositories found.")
        return

    for repo in archived:
        visibility = "🔒 Private" if repo.get("private") else "🌐 Public"
        print(f"📁 {repo['name']} | {visibility} | Archived on: {repo['updated_at']}")
        time.sleep(LOAD_REPO_DELAY)

def github_get_user_info(username):
    url = f"https://api.github.com/users/{username}"
    response = github_request("GET", url)
    if not response:
        return None
    return response.json()

def time_since(date_str):
    # date_str example: "2025-08-08T12:34:56Z"
    dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    now = datetime.now(timezone.utc)
    diff = now - dt.replace(tzinfo=timezone.utc)

    days = diff.days
    seconds = diff.seconds
    if days > 0:
        return f"{days} day{'s' if days != 1 else ''} ago"
    hours = seconds // 3600
    if hours > 0:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    minutes = (seconds % 3600) // 60
    if minutes > 0:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    return "just now"

def daily_digest(args=None):
    # Default query if none provided
    today = datetime.now().strftime("%Y-%m-%d")
    if args:
        query = " ".join(args) + f" pushed:{today}"
    else:
        query = f"stars:<2 pushed:{today}"

    print("\n📬 Daily Digest Report")
    print("──────────────────────")
    print(f"🔍 Searching repos with query: '{query}' (max 100 results)\n")

    search_url = "https://api.github.com/search/repositories"
    params = {"q": query, "per_page": 100}

    response = github_request("GET", search_url, params=params)
    if not response:
        print("❌ Failed to fetch search results.")
        return

    data = response.json()
    repos = data.get("items", [])

    if not repos:
        print("🟨 No repositories matched your criteria.")
        return

    for repo in repos:
        name = repo.get("name", "N/A")
        stars = repo.get("stargazers_count", 0)
        pushed_at = repo.get("pushed_at", "")
        owner = repo.get("owner", {})
        owner_login = owner.get("login", "N/A")

        pushed_ago = time_since(pushed_at) if pushed_at else "N/A"

        # Fetch owner details (followers, following)
        owner_info = github_get_user_info(owner_login)
        if owner_info:
            followers = owner_info.get("followers", "N/A")
            following = owner_info.get("following", "N/A")
        else:
            followers = "N/A"
            following = "N/A"

        print(f"📦 {name} | ⭐ {stars} | Pushed: {pushed_ago} | Owner: {owner_login} | Followers: {followers} | Following: {following}")

def has_readme(owner, repo, headers=None):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    response = requests.get(url, headers=headers)
    return response.status_code == 200

def extended_digest(args=None):
    # Default query if none provided
    today = datetime.now().strftime("%Y-%m-%d")
    if args:
        query = " ".join(args) + f" pushed:{today}"
    else:
        query = f"stars:<2 pushed:{today}"

    print("\n📬 Daily Digest Report")
    print("──────────────────────")
    print(f"🔍 Searching repos with query: '{query}' (max 200 results)\n")

    search_url = "https://api.github.com/search/repositories"
    params = {"q": query, "per_page": 100, "page": 2}

    response = github_request("GET", search_url, params=params)
    if not response:
        print("❌ Failed to fetch search results.")
        return

    data = response.json()
    repos = data.get("items", [])

    if not repos:
        print("🟨 No repositories matched your criteria.")
        return

    for repo in repos:
        name = repo.get("name", "N/A")
        stars = repo.get("stargazers_count", 0)
        pushed_at = repo.get("pushed_at", "")
        owner = repo.get("owner", {})
        owner_login = owner.get("login", "N/A")

        pushed_ago = time_since(pushed_at) if pushed_at else "N/A"

        # Fetch owner details (followers, following)
        owner_info = github_get_user_info(owner_login)
        if owner_info:
            followers = owner_info.get("followers", "N/A")
            following = owner_info.get("following", "N/A")
        else:
            followers = "N/A"
            following = "N/A"
        
        if int(following) < int(followers):
            continue;
        if not has_readme(owner_login, name):
            continue;

        print(f"📦 {name} | ⭐ {stars} | Pushed: {pushed_ago} | Owner: {owner_login} | Followers: {followers} | Following: {following}")

def star_repo(repo_full_name):
    url = f"https://api.github.com/user/starred/{repo_full_name}"

    response = github_request("PUT", url)

    if response and response.status_code in (204, 304):
        print(f"⭐️ Successfully starred '{repo_full_name}'!")
    else:
        print(f"❌ Failed to star '{repo_full_name}'. Check if it exists or if you have permission.")

def cmd(cmd_str, args, repos):
    print("\n")

    match cmd_str:
        case "help":
            print(
                "The GitHub Automation CLI is designed to provide a command line interface \n" \
                "to quickly analyze your repos to maximize retention and code standards. \n\n" \
                "   'check-docs'   : Check all repositories for README and LICENSE files.\n" \
                "   'archive'      : Archive a repository, rename it, and add no longer \n" \
                "                    being maintained to its README\n" \
                "   'get-repos'    : Get a list of all your repos\n"
                "   'find-private' : Get a list of all your private repos\n" \
                "   'find-public' : Get a list of all your private repos\n" \
                "   'make-public'  : Make a repository public\n" \
                "   'make-private' : Make a repository private\n" \
                "   'find-unarchived' : Find all unarchived repositories\n" \
                "   'find-archived'   : Find all archived repositories\n" \
                "   'daily-digest'    : Get a daily digest of repositories\n" \
                "                       **note:** by default this will search\n" \
                "                       for repos with less than two stars pushed today\n" \
                "   'extended-digest' : Get a daily digest of repositories\n" \
                "                       and filter by owner and README\n" \
                "   'star'            : Star a repository", 
                flush=True)
        case "check-docs":
            check_repo_readme_license(repos)
        case "archive":
            if len(args) == 0:
                print("🚫 No repository name provided\n")
                return
            repo_name = args[0]
            archive_repo(repo_name)
        case "get-repos":
            print_repo_summary(repos)
        case "find-private":
            find_private_repos(repos)
        case "find-public":
            find_public_repos(repos)
        case "make-public":
            if len(args) == 0:
                print("🚫 No repository name provided\n")
                return
            repo_name = args[0]
            make_repo_public(repo_name)
        case "make-private":
            if len(args) == 0:
                print("🚫 No repository name provided\n")
                return
            repo_name = args[0]
            make_repo_private(repo_name)
        case "find-unarchived":
            find_unarchived_repos(repos)
        case "find-archived":
            find_archived_repos(repos)
        case "daily-digest":
            if len(args) == 0:
                print("⚠️ No search query provided\n")
                daily_digest(args)
                return
            daily_digest(args[0])
        case "extended-digest":
            if len(args) == 0:
                print("⚠️ No search query provided\n")
                extended_digest(args)
                return
            extended_digest()
        case "star":
            if len(args) == 0:
                print("⚠️ No search query provided\n")
                return
            star_repo(args[0])

    print("\n")

def run_cli(repos):
    ascii_art = pyfiglet.figlet_format("GitHub Automation CLI")
    lines = ascii_art.splitlines()

    for i, line in enumerate(lines):
        # Cycle through pastel colors for each line
        color = pastel_rainbow[i % len(pastel_rainbow)]
        text = Text(line, style=color)
        console.print(text)

    print("🤖 Need a hand? Type 'help' to explore the features of the GitHub Automation CLI! 🚀\n")
     
    while True:
        comb_cmd = input(f"@{USER_NAME} > ").split(" ")

        cmd_str = comb_cmd[0]
        args = comb_cmd[1:]

        cmd(cmd_str, args, repos)

def main():
    try:
        print(f"🔍 Checking repositories for user: {USER_NAME}")
        repos = get_user_repos()

        if not repos:
            print("No repositories found.")
            return
        
        clear_terminal()
        
        run_cli(repos)
    except KeyboardInterrupt:   # Discard KeyboardInterrupt error
        pass

if __name__ == "__main__":
    main()

