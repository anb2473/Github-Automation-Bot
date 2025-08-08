# 🤖 GitHub Automation Bot

The **GitHub Automation CLI** uses the GitHub API to supercharge your workflow by automating repetitive tasks! 🚀

With this CLI, you can:

- 📬 Get a **daily digest** of your repositories  
- 📄 Check if your repos have proper **README** and **LICENSE** files  
- 🔒 Identify **private** and **archived** repositories  
- 🗃️ Efficiently **archive** repos that you no longer maintain  

All these tasks that usually take hours can be done in minutes, letting you focus on what you do best — **writing awesome code!** 💻✨

---

## 🛠️ How to Use

### 1. Create a `.env` file

Inside your project folder, create a `.env` file and add your credentials like this (replace with your info):

```env
USER_NAME=YOUR_USERNAME  
NUM_OF_PAGES=1  
GITHUB_TOKEN=YOUR_GITHUB_TOKEN  
EMAIL=YOUR_EMAIL  
LOAD_REPO_DELAY=0.25  
```

- **`LOAD_REPO_DELAY`** controls how long the program pauses before showing the next repo.  
- Set it to `0` if you want it to run without delay.

---

### 2. Generate a GitHub Token 🔑

To get your GitHub personal access token:

1. Go to [github.com](https://github.com) and log in  
2. Click your profile icon (top-right) → **Settings** ⚙️  
3. Scroll down to **Developer settings**  
4. Click **Personal access tokens** → **Tokens (classic)**  
5. Click **Generate new token** → Select **classic token**  
6. Under scopes, make sure to check **repo** permissions  
7. Generate and copy your token safely!

---

### 3. Install Dependencies

Make sure you're in the project directory, then run:

```bash
pip install -r requirements.txt  
```

---

### 4. Run the Bot

Start the CLI with:

```bash
python request-automation-bot.py  
```

Type `help` anytime to see the full list of commands available.
