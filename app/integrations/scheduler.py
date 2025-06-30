from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, select
from datetime import datetime
import asyncio

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

    def run_async_job():
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop in this thread, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        if loop.is_running():
            # If already running (e.g., in uvicorn), create a new task
            asyncio.create_task(fetch_and_save_all_users_wakatime_data())
        else:
            # If not running, start the loop and run the coroutine
            loop.run_until_complete(fetch_and_save_all_users_wakatime_data())

    scheduler.add_job(
        run_async_job,
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
        
def schedule_friday_demo_sessions():
    """
    AUTOMATION: Create demo sessions for upcoming Fridays
    This function can be called by a cron job or startup script
    """
    from datetime import date, timedelta
    from sqlmodel import Session, select
    from app.auth.database import engine
    from app.students.models import DemoSession
    from app.students.crud import create_demo_session, get_demo_session_by_date
    from app.students.schemas import DemoSessionCreate
    
    logger.info("Starting Friday demo session creation...")
    
    with Session(engine) as session:
        try:
            # Calculate next 8 Fridays
            today = date.today()
            days_until_friday = (4 - today.weekday()) % 7  # 4 = Friday (0=Monday)
            if days_until_friday == 0 and today.weekday() == 4:
                # Today is Friday, start from next Friday
                days_until_friday = 7
            
            created_count = 0
            
            for week in range(8):  # Create sessions for next 8 weeks
                friday_date = today + timedelta(days=days_until_friday + (week * 7))
                
                # Check if session already exists
                existing = get_demo_session_by_date(session, friday_date)
                
                if not existing:
                    # Create new demo session
                    session_create = DemoSessionCreate(
                        session_date=friday_date,
                        title=f"Friday Demo Session - {friday_date.strftime('%B %d, %Y')}",
                        description="Weekly demo session for all students",
                        is_active=True,
                        is_cancelled=False,
                        max_scheduled=None  # No limit by default
                    )
                    
                    demo_session = create_demo_session(session, session_create)
                    created_count += 1
                    logger.info(f"Created demo session on {friday_date}")
            
            session.commit()
            logger.info(f"Successfully created {created_count} demo sessions")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating demo sessions: {str(e)}")
            raise


# def check_holiday_cancellations():
#     """
#     AUTOMATION: Check for holidays and mark sessions as cancelled
#     This is a basic implementation - you can enhance with holiday APIs
#     """
#     from datetime import date
#     from sqlmodel import Session, select
#     from app.auth.database import engine
#     from app.students.models import DemoSession
    
#     # Basic holiday list - you can enhance this with external APIs
#     HOLIDAYS_2024 = [
#         date(2024, 1, 1),   # New Year's Day
#         date(2024, 1, 15),  # MLK Day
#         date(2024, 2, 19),  # Presidents Day
#         date(2024, 5, 27),  # Memorial Day
#         date(2024, 7, 4),   # Independence Day
#         date(2024, 9, 2),   # Labor Day
#         date(2024, 10, 14), # Columbus Day
#         date(2024, 11, 11), # Veterans Day
#         date(2024, 11, 28), # Thanksgiving
#         date(2024, 12, 25), # Christmas
#     ]
    
#     with Session(engine) as session:
#         try:
#             # Find sessions that fall on holidays
#             holiday_sessions = session.exec(
#                 select(DemoSession).where(
#                     DemoSession.session_date.in_(HOLIDAYS_2024),
#                     DemoSession.is_cancelled == False
#                 )
#             ).all()
            
#             cancelled_count = 0
#             for demo_session in holiday_sessions:
#                 demo_session.is_cancelled = True
#                 demo_session.is_active = False
#                 demo_session.notes = f"Cancelled due to holiday on {demo_session.session_date}"
#                 session.add(demo_session)
#                 cancelled_count += 1
#                 logger.info(f"Cancelled session on {demo_session.session_date} due to holiday")
            
#             session.commit()
#             logger.info(f"Cancelled {cancelled_count} sessions due to holidays")
            
#         except Exception as e:
#             session.rollback()
#             logger.error(f"Error checking holiday cancellations: {str(e)}")
#             raise


def automated_demo_session_management():
    """
    Main automation function that can be called by cron or at startup
    """
    logger.info("Starting automated demo session management...")
    
    try:
        # Create upcoming Friday sessions
        schedule_friday_demo_sessions()
        
        # Check for holiday cancellations (commented out for now)
        # check_holiday_cancellations()
        
        logger.info("Automated demo session management completed successfully")
        
    except Exception as e:
        logger.error(f"Error in automated demo session management: {str(e)}")
        raise
        

