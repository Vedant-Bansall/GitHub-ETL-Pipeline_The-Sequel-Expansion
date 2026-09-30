import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv

from extract import extract_data
from load import data_to_parquet, load_data, load_yaml_data
from transform import transform_data

# Load values
load_dotenv()

# Create logger
logging.basicConfig(filename="data/logs.log", level=logging.INFO, format="%(asctime)s; %(name)s, %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S", encoding="UTF-8")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Get params, Not permanent
pat_key = os.getenv("GITHUB_TOKEN")
username = "Vedant-Bansall"
if os.path.getsize("timestamp.txt") == 0:
    target_date_str = "2008-01-01T00:00:00Z" # If you wouild like to configure initial run date yourself, the format is YYYY-MM-DDTHH:MM:SSZ and do not remove the T and Z, they must be there
else:
    with open("timestamp.txt") as tstxt:
        target_date_str = tstxt.read()
    
target_dt = datetime.fromisoformat(target_date_str.replace("Z", "+00:00"))

# Script Start Log
main_start = datetime.now(timezone.utc)
logger.info("Started Script")

repos = [owner + '/' + repo for owner, repo in load_yaml_data()]
logger.info(f"Loading Repos: {repos}")

for owner, repo in load_yaml_data():
    # Log Repo start
    start = datetime.now(timezone.utc)
    logger.info(f"{owner}/{repo} started")
    standard_issues, pull_requests, repo_id = extract_data(pat_key, owner, repo, username, target_date_str, target_dt)
    if standard_issues or pull_requests:
        transformed_dataset = transform_data(standard_issues, pull_requests, repo_id, owner, repo)
        load_data(transformed_dataset, owner, repo)
        data_to_parquet(transformed_dataset, owner, repo)
        print(f"Fetched:\n• {len(standard_issues)} Issues\n• {len(pull_requests)} Pull Requests")
        logger.info(f"Fetched {len(standard_issues)} Issues and {len(pull_requests)} Pull Requests from {owner}/{repo}")
        end = datetime.now(timezone.utc)
        logger.info(f"{owner}/{repo} ended")
        logger.info(f"Total elapse time on {owner}/{repo} is {(end - start).total_seconds()} seconds")
    else:
        print("Extraction completed, but 0 issues/PRs matched the filter criteria.")
        logger.info(f"Extraction on {owner}/{repo} completed, but 0 issues/PRs matched the filter criteria.")

# Script End Log
main_end = datetime.now(timezone.utc)
logger.info("Script Completed.")
logger.info(f"Total Elapse Time is {(main_end - main_start).total_seconds()} seconds")