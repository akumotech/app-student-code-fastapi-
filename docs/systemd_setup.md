# FastAPI + Uvicorn Deployment with systemd

This guide explains how to run your FastAPI app (with Uvicorn) as a background service using `systemd` on Linux. This is a robust, production-ready way to keep your app running and automatically restart it if it crashes.

---

## 1. Create a systemd Service File

Create a file at `/etc/systemd/system/fastapi.service` (requires sudo):

```ini
[Unit]
Description=FastAPI application with Uvicorn
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/app-student-code-fastapi-
Environment="PATH=/home/ec2-user/app-student-code-fastapi-/venv/bin"
ExecStart=/home/ec2-user/app-student-code-fastapi-/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

- **User/Group:** Set to the user running your app (e.g., `ec2-user`).
- **WorkingDirectory:** Path to your project root.
- **Environment PATH:** Points to your virtualenv's `bin` directory.
- **ExecStart:** Uses the venv's Uvicorn to run your app.

---

## 2. Reload systemd and Start the Service

```bash
sudo systemctl daemon-reload
sudo systemctl start fastapi
sudo systemctl enable fastapi
```

---

## 3. Check Status and Logs

**Check service status:**

```bash
sudo systemctl status fastapi
```

**View logs in real time:**

```bash
sudo journalctl -u fastapi -f
```

**View last 100 log lines:**

```bash
sudo journalctl -u fastapi -n 100
```

---

## 4. (Optional) Log to a File

If you want logs written to a file instead of the system journal, add these lines to the `[Service]` section:

```ini
StandardOutput=append:/home/ec2-user/app-student-code-fastapi-/uvicorn.log
StandardError=append:/home/ec2-user/app-student-code-fastapi-/uvicorn.log
```

**Example:**

```ini
[Service]
...
StandardOutput=append:/home/ec2-user/app-student-code-fastapi-/uvicorn.log
StandardError=append:/home/ec2-user/app-student-code-fastapi-/uvicorn.log
...
```

---

## 5. Managing the Service

- **Start:** `sudo systemctl start fastapi`
- **Stop:** `sudo systemctl stop fastapi`
- **Restart:** `sudo systemctl restart fastapi`
- **Enable on boot:** `sudo systemctl enable fastapi`

---

## 6. Troubleshooting

- If the service fails to start, check logs with:
  ```bash
  sudo journalctl -u fastapi -n 50
  ```
- Make sure all paths and usernames are correct in your service file.
- After editing the service file, always run:
  ```bash
  sudo systemctl daemon-reload
  ```

---

**This setup ensures your FastAPI app is robust, restartable, and easy to manage in production!**
