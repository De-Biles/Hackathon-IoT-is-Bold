University of Galway hackathon project.

Theme: IoT is bold.
Members: Illia Uriupin (@DreamyLunatic ), Maksym Potushynskyi (@Borov4308 ).

# Open Your Window – Raspberry Pi Setup Guide

## 1. **Prepare Your Raspberry Pi**

1. Install **Raspberry Pi OS (64-bit recommended)**.
2. Connect your Raspberry Pi to the network (Wi-Fi or Ethernet).
3. Update the system:

   ```bash
   sudo apt update
   sudo apt upgrade -y
   sudo apt install python3-pip python3-venv git -y
   ```

---

## 2. **Install Required Hardware and Libraries**

1. Attach the **Sense HAT** to the GPIO pins.
2. Install Sense HAT Python library:

   ```bash
   sudo apt install sense-hat -y
   sudo pip3 install --upgrade pip
   pip3 install sense-hat flask flask-cors requests filelock gunicorn
   ```
3. Test the Sense HAT:

   ```python
   from sense_hat import SenseHat
   sense = SenseHat()
   sense.show_message("Hello!")
   ```

---

## 3. **Clone Your Project**

```bash
mkdir ~/open-your-window
cd ~/open-your-window
git clone <your-repo-url> .
```

Ensure your project directory contains:

* `app.py` (your Flask app)
* `style.css` and `script.js` (frontend)
* `userData/` (folder for settings/history)

---

## 4. **Set Up a Python Virtual Environment**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> If you don’t have `requirements.txt`, run:

```bash
pip install flask flask-cors requests filelock gunicorn sense-hat
```

---

## 5. **Test Your Flask App**

```bash
python app.py
```

* Open a browser and navigate to `http://<raspberry-pi-ip>:5000`.
* You should see the dashboard.

---

## 6. **Run the App with Gunicorn**

```bash
gunicorn --workers 4 --bind 0.0.0.0:8000 app:app
```

* This starts the Flask app with Gunicorn on port 8000.
* Test by visiting `http://<raspberry-pi-ip>:8000`.

---

## 7. **Install and Configure Nginx**

```bash
sudo apt install nginx -y
sudo systemctl enable nginx
sudo systemctl start nginx
```

Create an nginx config for the project:

```bash
sudo nano /etc/nginx/sites-available/open-your-window
```

Add:

```nginx
server {
    listen 80;
    server_name <your-pi-hostname-or-ip>;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/open-your-window /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

* Now your app should be accessible on port 80 (default HTTP).

---

## 8. **Set Up Gunicorn as a Systemd Service**

Create a service file:

```bash
sudo nano /etc/systemd/system/open-your-window.service
```

Add:

```ini
[Unit]
Description=Open Your Window Flask App
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/open-your-window
Environment="PATH=/home/pi/open-your-window/venv/bin"
ExecStart=/home/pi/open-your-window/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 app:app

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable open-your-window
sudo systemctl start open-your-window
sudo systemctl status open-your-window
```

---

## 9. **Install Tailscale for Remote Access**

1. Install Tailscale:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

2. Copy your Tailscale IP (`tailscale ip -4`) and access the app remotely:

```text
http://<tailscale-ip>
```

---

## 10. **Additional Notes**

* `userData/` stores your JSON settings and history. Make sure it exists:

```bash
mkdir -p ~/open-your-window/userData
touch ~/open-your-window/userData/history.json
touch ~/open-your-window/userData/settings.json
```

* Logs can be monitored:

```bash
journalctl -u open-your-window -f
```

* Update your coordinates in `userData/coords.json` to get accurate weather data.
