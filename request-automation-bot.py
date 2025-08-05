import requests
from datetime import date, timedelta, datetime
import time
from dotenv import load_dotenv
import os
import random
import math
import json
from colorama import init, Fore, Style
import sys

init(autoreset=True)  # automatically reset colors after each print

load_dotenv()  # take environment variables from .env

def clear_terminal():
    # For Windows
    if os.name == 'nt':
        os.system('cls')
    # For Linux and macOS
    else:
        os.system('clear')

clear_terminal()

token = os.getenv("GITHUB_TOKEN")
USERNAME = os.getenv("USERNAME")
CHECK_FILE = os.getenv("CHECK_FILE")
MAX_STARS = os.getenv("MAX_STARS")

# Rainbow colors cycle (some bright colors)
RAINBOW_COLORS = [
    Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.MAGENTA,
]

if not token or not USERNAME or not CHECK_FILE:
    raise ValueError("GITHUB_TOKEN and USERNAME must be set in the .env file")

def load_check_list():
    if os.path.exists(CHECK_FILE):
        with open(CHECK_FILE, "r") as f:
            raw = json.load(f)
            return [[entry[0], datetime.strptime(entry[1], "%Y-%m-%d").date(), entry[2]] for entry in raw]
    return []

check_following_list = load_check_list()

def save_check_list():
    with open(CHECK_FILE, "w") as f:
        serializable = [[entry[0], entry[1].strftime("%Y-%m-%d"), entry[2]] for entry in check_following_list]
        json.dump(serializable, f)

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github+json"
}

REPOS_PER_PAGE = int(os.getenv("REPOS_PER_PAGE", "100"))
NUM_OF_PAGES = int(os.getenv("NUM_OF_PAGES", "1"))

printed_once = False

def print_rainbow_box(text, color_index):
    global printed_once
    color = RAINBOW_COLORS[int(color_index % len(RAINBOW_COLORS))]
    length = len(text) + 4
    top_bottom = color + "+" + "-" * (length - 2) + "+"
    middle = color + "| " + Style.BRIGHT + text + Style.NORMAL + color + " |"
    
    if printed_once:
        # Move cursor up 3 lines to overwrite previous box
        sys.stdout.write('\033[F' * 3)
    else:
        printed_once = True

    print(top_bottom)
    print(middle)
    print(top_bottom)
    sys.stdout.flush()

def wait_until_tmrw(offset):
    now = datetime.now()

    # Calculate 11:50 PM the next day
    next_day = now + timedelta(days=1)
    target_time = datetime(
        year=next_day.year,
        month=next_day.month,
        day=next_day.day,
        hour=22 + random.randint(-1, 1),
        minute=0 + random.randint(0, 30),
        second=random.randint(10, 50)
    )

    sleep_seconds = (target_time - now).total_seconds() + offset
    print(f"Sleeping until {target_time} ({sleep_seconds / 3600:.2f} hours)")
    try:
        while sleep_seconds > 0:
            print_rainbow_box(f"Sleeping... {int(sleep_seconds)} seconds left", sleep_seconds)
            now = datetime.now()
            sleep_seconds = (target_time - now).total_seconds() + offset
            time.sleep(1)
    except KeyboardInterrupt:  # discard error and exit program 
        exit()
    clear_terminal()

def github_request(method, url, **kwargs):
    try:
        response = requests.request(method, url, headers=headers, **kwargs)
        if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers:
            remaining = int(response.headers['X-RateLimit-Remaining'])
            if remaining == 0:
                reset_time = int(response.headers['X-RateLimit-Reset'])
                sleep_sec = reset_time - int(time.time()) + 5
                print(f"Rate limit exceeded, sleeping for {sleep_sec} seconds")
                time.sleep(sleep_sec)
                return github_request(method, url, **kwargs)  # Retry after sleep
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"Request error for {url}: {e}")
        return None

wait_until_tmrw(offset=-24*60*60)    # Do not wait 2 days before starting, only wait until this night

while True:
    print("Beginning starring process")

    today = date.today().strftime("%Y-%m-%d")
    query = f"stars:<{MAX_STARS} pushed:{today}"
   
    url = f"https://api.github.com/search/repositories?q={query}&sort=updated&order=desc&per_page={
        min(REPOS_PER_PAGE + 
                random.randint(REPOS_PER_PAGE - math.ceil(REPOS_PER_PAGE / 10), 
                REPOS_PER_PAGE + math.ceil(REPOS_PER_PAGE / 10)),
            100)
        }&page={NUM_OF_PAGES}"

    response = github_request("GET", url)
    if response is None:
        print("Failed request, skipping...")
        wait_until_tmrw()
        continue

    data = response.json()

    if 'items' not in data:
        print("No repos found or API error:", data)
        wait_until_tmrw()
        continue

    repos = data['items']
    random.shuffle(repos)

    for repo in repos:
        url = f"https://api.github.com/user/starred/{repo['full_name']}"
        response = github_request("PUT", url)
        if response is None:
            print("Failed request, skipping...")
            wait_until_tmrw()
            continue
        if response.status_code != 204:
            print(f"Error sending request to https://api.github.com/user/starred/{repo['full_name']}, {response.status_code}")
        owner = repo['owner']['login']
        check_following_list.append([owner, date.today(), repo['full_name']])

        time.sleep(random.uniform(5, 15))

    print("Checking followers")

    for potential_follower, starred_date, starred_repo in check_following_list[:]: 
        # iterate on copy of check_following_list to avoid issues editing acual list
        url = f"https://api.github.com/users/{potential_follower}/following/{USERNAME}"
        response = github_request("GET", url)
        if response is None:
            print("Failed request, skipping...")
            continue

        if response.status_code == 204: # User has followed
            print("Successful follow")
            url = f"https://api.github.com/user/following/{potential_follower}"
            github_request("PUT", url)
        else:   # User has not followed
            if (datetime.today().date() - starred_date).days > 3:  # More than 3 days have passed since starring
                url = f"https://api.github.com/user/starred/{starred_repo}"
                github_request("DELETE", url)

                url = f"https://api.github.com/user/following/{potential_follower}"
                github_request("DELETE", url)

                check_following_list.remove([potential_follower, starred_date, starred_repo])

    save_check_list()

    wait_until_tmrw()
