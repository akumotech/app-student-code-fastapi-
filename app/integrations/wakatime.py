import requests

def get_wakatime_stats(access_token: str):
    url = "https://wakatime.com/api/v1/users/current/stats/last_7_days"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json() 

def get_wakatime_today(access_token: str):
    url = "/api/v1/users/current/status_bar/today"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()