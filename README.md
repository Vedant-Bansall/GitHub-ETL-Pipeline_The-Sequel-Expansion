# Overview
This is an expansion to my old ETL Pipeline, it now runs multiple repos. What my somewhat simple code does is it extracts issues and pull requests updated/created after the script last ran (Fallback is at the very start of repo creation) from your chosen repos, flattens it into readable columns of important data like: dates, information and labels then exports it as a columnar-based parquet file and into a permanent database of all times it has ran.
The parquet files will be used for data analysis.

This is useful as you can see historical growth, find bottlenecks, see team efficiency, analyse key metrics and just see overall repository health.

## Setup
To set up this repo correctly, follow these steps:
- In the repo, create and activate a virtual environment so you can run some scripts in it. To create a venv run these commands in the following order:
    1. cd Drive:/Users/User/PathToProjectFolder
    2. python -m venv .venv
    3. .venv/Scripts/activate
    4. pip install -r requirements.txt
- In the .env.example file in the repo, please add your personal access token. Example: GITHUB_TOKEN=MySecretToken and rename the file to .env
- To see how to create a PAT, [click here](https://www.youtube.com/watch?v=0C-B6bFuQYU)
- In config.yaml, in the repos dictionary, add your repos to the format it shows (**NOTE: I DO NOT OWN pallet/flask OR fastapi/fastapi-cli NOR HAVE I HELPED THEM, THEY WERE PURELY USED AS TEST REPOS**):
- In main.py, assign the username variable to your GitHub username
- Run main.py to finish and use the script
- What happens is it extracts your data, flattens it into relevant data, then loads it into a permanent database of every record and a new parquet file (this creates a new file each time so it can see the most recent snapshot of data)
- After this runs, run dashboard.py (optional) to see the dashboard of analytics per repo
- These analytics includes KPI cards and graphs of:
    * Total Issues recorded
    * Amount of different users who have contributed
    * Amount of Stale Items (> 14 days of inactivity)
    * Closed to Open ration Pie Chart
    * Amount of entities (issues/PRs) an author has made
    * A bar chart of amount of each label
    * A Histogram of lead time days to see how long it takes to close an issue
    * Total Issue/PR over time (Records per snapshot)
    * A chart showcasing amount of prs and issues in every repo

### Warning
IF you use this, please make sure you have everything correctly set up (every single file in the repo) and DO NOT TOUCH THEM OR IT BREAKS THE SCRIPT (Esepcially timestamp.txt and data.db)
