from apscheduler.schedulers.background import BackgroundScheduler
from app.integrations.wakatime import get_wakatime_today
from sqlmodel import Session, select

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        fetch_and_save_all_users_wakatime_data, 
        trigger='cron', 
        hours=23,
        minute=30
        )
    scheduler.start()

def fetch_and_save_all_users_wakatime_data():
    with Session(engine) as session:
        users = session.exec(select(User).where(User.wakatime_access_token_encrypted != None)).all()
        
        for user in users:
            access_token = fernet.decrypt(user.wakatime_access_token_encrypted.encode()).decode()
            user_data = get_wakatime_today(access_token)

            data = user_data["data"]
            grand_total = data["grand_total"]
            range_data = data["range"]

            summary = DailySummary(
                user_id=user.id,
                cached_at=datetime.fromisoformat(user_data["cached_at"].replace("Z", "+00:00")),
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
                has_team_features=user_data["has_team_features"],
            )

            # add nested objects
            for project_data in data.get("projects", []):
                summary.projects.append(Project(**project_data))
            
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
                machine_data["machine_name_id"] = machine_data.get("machine_name_id")
                summary.machines.append(Machine(**machine_data))

            session.add(summary)

        session.commit()
        

