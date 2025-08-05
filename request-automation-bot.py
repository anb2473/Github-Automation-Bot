import requests
from datetime import date, timedelta, datetime
import time
from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env

token = os.getenv("GITHUB_TOKEN")
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github+json"
}

USERNAME = os.getenv("USERNAME")

REPOS_PER_PAGE = int(os.getenv("REPOS_PER_PAGE", "100"))
NUM_OF_PAGES = int(os.getenv("NUM_OF_PAGES", "1"))

check_following_list = []

def wait_until_next_1150pm():
    now = datetime.now()

    # Calculate 11:50 PM the next day
    next_day = now + timedelta(days=1)
    target_time = datetime(
        year=next_day.year,
        month=next_day.month,
        day=next_day.day,
        hour=23,
        minute=50,
        second=0
    )

    sleep_seconds = (target_time - now).total_seconds()
    print(f"Sleeping until {target_time} ({sleep_seconds / 3600:.2f} hours)")
    time.sleep(sleep_seconds)

while True:
    today = date.today().strftime("%Y-%m-%d")
    query = f"stars:<5 pushed:{today}"
   
    url = f"https://api.github.com/search/repositories?q={query}&sort=updated&order=desc&per_page={REPOS_PER_PAGE}&page={NUM_OF_PAGES}"

    response = requests.get(url, headers=headers)
    data = response.json()

    if 'items' not in data:
        print("No repos found or API error:", data)
        wait_until_next_1150pm()
        continue

    for repo in data['items']:
        url = f"https://api.github.com/user/starred/{repo['full_name']}"
        response = requests.put(url, headers=headers)
        if response.status_code != 204:
            print(f"Error sending request to https://api.github.com/user/starred/{repo['full_name']}, {response.status_code}")
        owner = repo['owner']['login']
        check_following_list.append([owner, date.today(), repo['full_name']])

    for potential_follower, starred_date, starred_repo in check_following_list[:]: 
        # iterate on copy of check_following_list to avoid issues editing acual list
        url = f"https://api.github.com/users/{potential_follower}/following/{USERNAME}"
        response = requests.get(url, headers=headers)

        if response.status_code == 204: # User has followed
            url = f"https://api.github.com/user/following/{potential_follower}"
            response = requests.put(url, headers=headers)
        else:   # User has not followed
            if date.today() > starred_date + timedelta(days=3): # More than 3 days have passed since starring
                url = f"https://api.github.com/user/starred/{starred_repo}"
                requests.delete(url, headers=headers)

                url = f"https://api.github.com/user/following/{potential_follower}"
                requests.delete(url, headers=headers)

                check_following_list.remove([potential_follower, starred_date, starred_repo])

    wait_until_next_1150pm()
