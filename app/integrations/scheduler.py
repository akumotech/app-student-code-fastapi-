from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, select

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_and_save_all_users_wakatime_data, 'interval', days=1)
    scheduler.start()

def fetch_and_save_all_users_wakatime_data():
    with Session(engine) as session:
        users = session.exec(select(User).where(User.wakatime_access_token_encrypted != None)).all()
        
        for user in users:
            access_token = fernet.decrypt(user.wakatime_access_token_encrypted.encode()).decode()
            
            # Fetch WakaTime API data here
            # Parse it
            # Save into WakaTimeSummary + related tables