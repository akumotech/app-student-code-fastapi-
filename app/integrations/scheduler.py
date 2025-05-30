from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, select
from datetime import datetime

from app.config import settings
from app.auth.database import engine
from app.auth.models import User
from app.integrations.wakatime import fetch_today_data
from app.integrations.model import (
    DailySummary, WakaProject, Language, Dependency,
    Editor, Category, OperatingSystem, Machine
)

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        fetch_and_save_all_users_wakatime_data, 
        trigger='cron', 
        hour=23,
        minute=30
        )
    scheduler.start()
    print("WakaTime data fetching scheduler started. Will run daily at 23:30.")

async def fetch_and_save_all_users_wakatime_data():
    print("Scheduler job: Starting fetch_and_save_all_users_wakatime_data")
    with Session(engine) as session:
        users = session.exec(select(User).where(User.wakatime_access_token_encrypted != None)).all()
        
        processed_users = 0
        failed_users = 0
        for user in users:
            try:
                print(f"Fetching WakaTime data for user: {user.email}")
                user_data_response = await fetch_today_data(user, session)

                if not isinstance(user_data_response, dict) or "data" not in user_data_response:
                    print(f"Unexpected data structure from WakaTime for user {user.email}: Missing 'data' key. Response: {user_data_response}")
                    failed_users += 1
                    continue

                data = user_data_response["data"]
                
                grand_total = data.get("grand_total")
                range_data = data.get("range")
                cached_at_str = user_data_response.get("cached_at")
                has_team_features_val = user_data_response.get("has_team_features", False)

                if not all([grand_total, range_data, cached_at_str]):
                    print(f"Missing critical data fields (grand_total, range, or cached_at) for user {user.email}. Data: {data}")
                    failed_users += 1
                    continue

                summary = DailySummary(
                    user_id=user.id,
                        cached_at=datetime.fromisoformat(cached_at_str.replace("Z", "+00:00")),
                    date=datetime.fromisoformat(range_data["date"]).date(),
                    start=datetime.fromisoformat(range_data["start"].replace("Z", "+00:00")),
                    end=datetime.fromisoformat(range_data["end"].replace("Z", "+00:00")),
                    timezone=range_data["timezone"],
                    total_seconds=grand_total["total_seconds"],
                    hours=grand_total["hours"],
                    minutes=grand_total["minutes"],
                    digital=grand_total["digital"],
                    decimal=grand_total["decimal"],
                    text=grand_total["text"],
                        has_team_features=has_team_features_val,
                )

                for project_data in data.get("projects", []):
                        summary.projects.append(WakaProject(**project_data))
                
                for lang_data in data.get("languages", []):
                    summary.languages.append(Language(**lang_data))
                
                for dep_data in data.get("dependencies", []):
                    summary.dependencies.append(Dependency(**dep_data))
                
                for editor_data in data.get("editors", []):
                    summary.editors.append(Editor(**editor_data))
                
                for cat_data in data.get("categories", []):
                    summary.categories.append(Category(**cat_data))
                
                for os_data in data.get("operating_systems", []):
                    summary.operating_systems.append(OperatingSystem(**os_data))
                
                for machine_data in data.get("machines", []):
                    summary.machines.append(Machine(**machine_data))

                session.add(summary)
                session.commit()
                processed_users += 1
                print(f"Successfully processed and saved WakaTime data for user: {user.email}")

            except HTTPException as he:
                print(f"HTTPException for user {user.email} during WakaTime data fetch: {he.detail}")
                session.rollback()
                failed_users += 1
            except Exception as e:
                print(f"Failed to process WakaTime data for user {user.email}: {e}")
                import traceback
                traceback.print_exc()
                session.rollback()
                failed_users += 1
        
        print(f"Scheduler job finished. Processed users: {processed_users}, Failed users: {failed_users}")

# To run the scheduler, call start_scheduler() when the FastAPI app starts.
# e.g., in main.py: app.on_event("startup")
        

