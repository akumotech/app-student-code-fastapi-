import httpx
import json
from datetime import datetime, date
from typing import Optional, Dict, Any
from fastapi import HTTPException
from app.config import settings


async def send_slack_notification(
    message: str,
    channel: Optional[str] = None,
    blocks: Optional[list] = None
) -> bool:
    """Send a notification to Slack channel"""
    
    if not settings.SLACK_BOT_TOKEN:
        print("Slack bot token not configured, skipping notification")
        return False
    
    target_channel = channel or settings.SLACK_CHANNEL
    if not target_channel:
        print("Slack channel not configured, skipping notification")
        return False
    
    headers = {
        "Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "channel": target_channel,
        "text": message
    }
    
    # Add blocks if provided for rich formatting
    if blocks:
        payload["blocks"] = blocks
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            if not result.get("ok"):
                print(f"Slack API error: {result.get('error')}")
                return False
                
            return True
        except httpx.HTTPStatusError as e:
            print(f"Slack notification failed: {e.response.status_code} - {e.response.text}")
            return False
        except httpx.RequestError as e:
            print(f"Slack notification error: {e}")
            return False


async def send_demo_session_notification(
    session_date: date,
    session_title: str,
    meeting_link: Optional[str] = None,
    description: Optional[str] = None,
    session_time: Optional[str] = None
) -> bool:
    """Send a notification about a new demo session"""
    
    # Format the date for display
    formatted_date = session_date.strftime("%A, %B %d, %Y")
    if session_time:
        formatted_date += f" at {session_time} Central Time"
    
    # Create the message
    message = f"🎉 New Friday Demo Session Available!\n\n📅 Date: {formatted_date}\n📝 Title: {session_title}"
    
    if description:
        message += f"\n📋 Description: {description}"
    
    if meeting_link:
        message += f"\n🔗 Meeting Link: {meeting_link}"
    
    message += "\n\n📌 Don't forget to register your demo topics! Sign up now to secure your spot."
    
    # Create rich blocks for better formatting
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🎉 *New Friday Demo Session Available!*"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Date:*\n{formatted_date}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Title:*\n{session_title}"
                }
            ]
        }
    ]
    
    if description:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Description:*\n{description}"
            }
        })
    
    if meeting_link:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Meeting Link:*\n<{meeting_link}|Join Meeting>"
            }
        })
    
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "📌 *Don't forget to register your demo topics!* Sign up now to secure your spot."
        }
    })
    
    blocks.append({
        "type": "divider"
    })
    
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "💡 Pro tip: Prepare your demo in advance and practice your presentation!"
            }
        ]
    })
    
    return await send_slack_notification(
        message=message,
        blocks=blocks
    )


async def send_demo_reminder_notification(
    session_date: date,
    session_title: str,
    registered_count: int,
    meeting_link: Optional[str] = None,
    session_time: Optional[str] = None
) -> bool:
    """Send a reminder notification about an upcoming demo session"""
    
    formatted_date = session_date.strftime("%A, %B %d, %Y")
    if session_time:
        formatted_date += f" at {session_time} Central Time"
    
    message = f"🔔 Reminder: Friday Demo Session Tomorrow!\n\n📅 Date: {formatted_date}\n📝 Title: {session_title}\n👥 Registered: {registered_count} students"
    
    if meeting_link:
        message += f"\n🔗 Meeting Link: {meeting_link}"
    
    message += "\n\n⏰ Get ready to showcase your work!"
    
    # Create rich blocks for reminder
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🔔 *Reminder: Friday Demo Session Tomorrow!*"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Date:*\n{formatted_date}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Registered:*\n{registered_count} students"
                }
            ]
        }
    ]
    
    if meeting_link:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Meeting Link:*\n<{meeting_link}|Join Meeting>"
            }
        })
    
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "⏰ *Get ready to showcase your work!*\n\n🎯 Last chance to register if you haven't already!"
        }
    })
    
    return await send_slack_notification(
        message=message,
        blocks=blocks
    ) 