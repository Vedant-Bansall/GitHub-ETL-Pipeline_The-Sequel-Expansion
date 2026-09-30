# Imports
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml
from sqlalchemy import Column, ForeignKey, Table, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

logging.basicConfig(filename="data/logs.log", level=logging.INFO, format="%(asctime)s; %(name)s, %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S", encoding="UTF-8")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LoadError(Exception):
    pass

# Base class
class Base(DeclarativeBase):
    pass

# Association Table
association_table = Table(
    "association_table",
    Base.metadata,
    Column("record_id", ForeignKey("record.composite_key")),
    Column("label_id", ForeignKey("label.id"))
)

# ORM Table
class Record(Base):
    __tablename__ = "record"

    # Columns
    composite_key: Mapped[str] = mapped_column(primary_key=True)
    repo_id: Mapped[int] = mapped_column()
    id: Mapped[int] = mapped_column()
    number: Mapped[int] = mapped_column()
    title: Mapped[str] = mapped_column()
    author: Mapped[str] = mapped_column()
    closed_by: Mapped[str | None] = mapped_column()
    thumbs_up: Mapped[int] = mapped_column()
    state: Mapped[str] = mapped_column()
    body: Mapped[str | None] = mapped_column()
    created_at: Mapped[datetime | None] = mapped_column()
    closed_at: Mapped[datetime | None] = mapped_column()
    updated_at: Mapped[datetime | None] = mapped_column()
    merged_at: Mapped[datetime | None] = mapped_column()
    draft: Mapped[bool] = mapped_column()
    head_branch: Mapped[str | None] = mapped_column()
    base_branch: Mapped[str | None] = mapped_column()
    lead_time_days: Mapped[float | None] = mapped_column()
    is_stale: Mapped[bool] = mapped_column()
    labels: Mapped[list[Label]] = relationship(secondary=association_table)
    entity_type: Mapped[str] = mapped_column()

# Label Table
class Label(Base):
    __tablename__ = "label"

    # Columns
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)

# Load Data
def load_data(dataset: list, owner: str, repo: str):
    # Log Repo Start
    start = datetime.now(timezone.utc)
    logger.info(f"{owner}/{repo} run load started")

    # Create Engine
    engine = create_engine("sqlite:///data/data.db")

    # Create Tables
    Base.metadata.create_all(engine)

    # Create Session
    with Session(engine) as session:
        update_cnt = 0
        insert_cnt = 0
        for item in dataset:
            # Updates if exists
            comp_key = str(item["repo_id"]) + "::" + str(item["id"])
            existing_record = session.get(Record, comp_key)
            if existing_record:
                existing_record.number = item["number"]
                existing_record.title = item["title"]
                existing_record.author = item["author"]
                existing_record.closed_by = item["closed_by"]
                existing_record.thumbs_up = item["thumbs_up"]
                existing_record.state = item["state"]
                existing_record.body = item["body"]
                existing_record.created_at = item["created_at"]
                existing_record.closed_at = item["closed_at"]
                existing_record.updated_at = item["updated_at"]
                existing_record.merged_at = item["merged_at"]
                existing_record.draft = item["draft"]
                existing_record.head_branch = item["head_branch"]
                existing_record.base_branch = item["base_branch"]
                existing_record.lead_time_days = item["lead_time_days"]
                existing_record.is_stale = item["is_stale"]
                existing_record.entity_type = item["entity_type"]

                update_cnt += 1 # Updates Update Counter

            # Inserts if new
            else:
                add_issue = Record(
                    composite_key=comp_key,
                    repo_id=item["repo_id"],
                    id=item["id"],
                    number=item["number"],
                    title=item["title"],
                    author=item["author"],
                    closed_by=item["closed_by"],
                    thumbs_up=item["thumbs_up"],
                    state=item["state"],
                    body=item["body"],
                    created_at=item["created_at"],
                    closed_at=item["closed_at"],
                    updated_at=item["updated_at"],
                    merged_at=item["merged_at"],
                    draft=item["draft"],
                    head_branch=item["head_branch"],
                    base_branch=item["base_branch"],
                    lead_time_days=item["lead_time_days"],
                    is_stale=item["is_stale"],
                    entity_type=item["entity_type"]
                )

                session.add(add_issue)
                existing_record = add_issue

                insert_cnt += 1

            # Add Labels
            for l in item["labels"]:
                stmt = select(Label).where(Label.name == l)
                label = session.scalars(stmt).first()

                if label is None:
                    label_obj = Label(name=l)
                    existing_record.labels.append(label_obj)

                else:
                    existing_record.labels.append(label)

        logger.debug(f"Inserted {insert_cnt} items and Updated {update_cnt} items")

        try:
            # Commit session
            session.commit()
            logger.info(f"Loaded Contents of {owner}/{repo} Successfully")

        except Exception as e:  # noqa: BLE001
            logger.error(f"An ERROR occured while Loading: {e!s}")
            raise LoadError("Unable to Load:", str(e))

    # Log repo end
    end = datetime.now(timezone.utc)
    logger.info(f"{owner}/{repo} run load ended")
    logger.info(f"Load elapse time took {(end - start).total_seconds()} seconds")

    # Make most recent run time
    with open("timestamp.txt", "w") as tstxt:
        ts = datetime.now(timezone.utc)
        tstxt.write(ts.isoformat())
    logger.debug(f"Run From timestamp updated to {ts}")

def load_yaml_data():
    with open("config.yaml") as config:
        names_list = [] # List of tuples containing owner, repo pair
        data = yaml.load(config, Loader=yaml.FullLoader) # Load YAML file
        repos = data["repositories"] # Get dictionary of repos in YAML

        for repo in repos: # Iterate through returne list
            enabled = repo["enabled"] # See if enabled
            if enabled: # Only add if enabled
                owner, repo_name = repo["name"].split("/") # Parse Owner Repo pair
                names_list.append((owner, repo_name)) # Add it to the list

        return names_list # Return list once complete for data_to_parquet to use

# Load data as parquet file
def data_to_parquet(dataset: list, owner: str, repo: str):
    # Log Repo Start
    start = datetime.now(timezone.utc)
    logger.info(f"{owner}/{repo} run load started")
    
    # DataFrame
    df = pd.DataFrame(dataset)

    # Getting Timestamp as format
    ts = datetime.now(timezone.utc)
    tsft = ts.strftime("%Y-%m-%d_%H.%M.%S")

    # Making subdirectory name
    subdir_name = f"{owner}.{repo}"

    # Making path
    pq_dir_path = "data/parquet"
    pq_dir = Path(pq_dir_path)
    pq_subdir = pq_dir.joinpath(subdir_name) 

    filename = f"github_data_{tsft}.parquet"
    combined_path = os.path.join(str(pq_subdir), filename)

    # Export to parquet
    pq_subdir.mkdir(exist_ok=True)
    df.to_parquet(combined_path)
    logger.info(f"{filename} containing most recent information about {owner}/{repo} exported to {pq_subdir!s}")

    # Log Repo end
    end = datetime.now(timezone.utc)
    logger.info(f"{owner}/{repo} run load ended")
    logger.info(f"Load elapse time took {(end - start).total_seconds()} seconds")