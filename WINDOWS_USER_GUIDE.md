# ISMAP — Step-by-Step Windows Guide for Novices

This guide is designed for anyone who wants to run ISMAP on their Windows computer, even if you have never used a scanner or a terminal before.

---

## 🟢 Step 1: Install Python (The Engine)
ISMAP needs Python to run. If you don't have it yet:
1. Go to [python.org/downloads](https://www.python.org/downloads/windows/).
2. Click the yellow button: **Download Python 3.12.x** (or the latest version).
3. **CRITICAL**: When the installer starts, you MUST check the box that says:
   > **[X] Add Python.exe to PATH**
4. Click **Install Now** and wait for it to finish.

---

## 🟢 Step 2: Get the ISMAP Folder
1. Download the ISMAP project (either as a `.zip` from your provider or via Git).
2. **Extract the Folder**: If you downloaded a `.zip`, right-click it and select "Extract All...".
3. Open the newly extracted folder. You should see files like `install_windows.bat` and `run_windows.bat`.

---

## 🟢 Step 3: One-Click Setup
We have made scientists easy for you!
1. Find the file named **`install_windows.bat`**.
2. **Double-click it**.
3. A black window (Terminal) will appear. It will automatically download the necessary libraries and build the User Interface.
4. **Wait**: This might take 2-5 minutes depending on your internet. 
5. When it says "Setup Complete!", press any key to close the window.

---

## 🟢 Step 4: Start the Scanner
1. Find the file named **`run_windows.bat`**.
2. **Double-click it**.
3. The terminal will open and say "Starting ISMAP Backend...".
4. **Keep this window open!** If you close it, the scanner will stop.

---

## 🟢 Step 5: Open the Dashboard
1. Open your web browser (Chrome, Edge, or Firefox).
2. In the address bar at the top, type:
   > **http://localhost:5000**
3. Press **Enter**.
4. You will see the ISMAP Login screen!

---

## 🟢 Step 6: Using the Tool
1. **Login**: Use the admin credentials provided to you.
2. **First Scan**:
   - Go to "Discover Subdomains".
   - Type a domain (e.g., `google.com`) and click **Start Scan**.
   - You will see the results appearing in real-time.
3. **History**:
   - Click **Refresh** on the "Global Scan History" at the top to see your completed scans.
   - Click the **TXT** button to download a clean text report for your records.

---

## ❓ Troubleshooting
- **"Python not found"**: You forgot to check the "Add to PATH" box in Step 1. Re-run the Python installer and choose "Modify".
- **"Network Error"**: Make sure the black `run_windows.bat` window is still open.

---
*Powered by ISMAP*
