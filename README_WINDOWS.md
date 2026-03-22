# ISMAP — Windows Setup Guide

Hello! This guide will help you run ISMAP (Subdomain & Vulnerability Scanner) on your Windows machine.

## Prerequisites

1. **Python 3.9 or higher**: Download from [python.org](https://www.python.org/downloads/windows/).
    - *Note: Make sure to check the box 'Add Python to PATH' during installation.*
2. **Node.js**: (Optional) Download from [nodejs.org](https://nodejs.org/) if you want to build the frontend yourself.

## Quick Start (One-Click)

1. **Setup**: Double-click `install_windows.bat`. This will create a virtual environment, install all dependencies, and build the user interface.
2. **Run**: Double-click `run_windows.bat`. This will start the scanner.

Once the background server is running, you can access the tool in your browser at:
👉 **[http://localhost:5000](http://localhost:5000)**

## Configuration

The application settings (like Slack Alerts) can be configured directly inside the tool once you log in.

### Default Admin Account
- **Username**: (The admin account created during setup)
- **Password**: (The admin password set during signup)

### Production Notes
If you are deploying this for a team, edit the `run_windows.bat` file and change the `JWT_SECRET_KEY` to a long random secret string to keep user sessions secure.

---
*Powered by ISMAP*
