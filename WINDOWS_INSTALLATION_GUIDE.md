# Complete ISMAP Installation & Startup Guide for Windows

This guide will walk you through the entire process of installing and running the ISMAP Subdomain Scanner application on your Windows machine from scratch. 

To run this full-stack application successfully, you will need to open **TWO separate terminal windows** (Command Prompt or PowerShell) — one for the backend server and one for the frontend server.

---

## Part 1: Prerequisites Check

Before you begin, ensure you have the following installed on your Windows system:
1. **Python 3.10 or newer**: Download from [python.org](https://www.python.org/downloads/).
   - *Crucial Step*: During the Python installer, ensure you check the box that says **"Add python.exe to PATH"** before clicking Install.
2. **Node.js**: Download the LTS version from [nodejs.org](https://nodejs.org/).
3. **Git** (Optional but recommended): Download from [git-scm.com](https://git-scm.com/).

---

## Part 2: Installing the Backend (Python)

Let's begin by setting up the Python backend server.

### 1. Open Terminal 1 (The Backend Terminal)
1. Press the `Windows Key`, type `cmd`, and press Enter to open the Command Prompt.
2. Navigate to the folder where you saved the ISMAP project:
   ```cmd
   cd path\to\your\ismap\folder
   ```

### 2. Create and Activate a Virtual Environment
A virtual environment keeps the application's dependencies separate from your main system.
1. Create the environment by running:
   ```cmd
   python -m venv venv
   ```
2. Activate the environment:
   ```cmd
   venv\Scripts\activate
   ```
   *(You should now see `(venv)` appear at the beginning of your terminal prompt line.)*

### 3. Install Backend Dependencies
With the environment activated, install the required packages:
```cmd
pip install -r requirements.txt
```

### 4. Setup the Database
Initialize the database file by simply triggering the included `models.py` configuration or running the Flask app once.
*Note: The script creates the `ismap.db` SQLite database automatically on first startup.*

### 5. Start the Backend Server
Start the core application:
```cmd
python app.py
```
**Success Indicator:** You should see console output saying `* Running on http://127.0.0.1:5000`. 
**DO NOT close this terminal window.** Leave it running in the background.

---

## Part 3: Installing the Frontend (React/Vite)

Now we will build the user interface so you can access the dashboard in your web browser.

### 1. Open Terminal 2 (The Frontend Terminal)
1. Leave Terminal 1 running. 
2. Press the `Windows Key`, type `cmd`, and press Enter to open a *brand new, second* Command Prompt window.
3. Navigate to the ISMAP project folder, and then specifically dive into the `frontend` folder:
   ```cmd
   cd path\to\your\ismap\folder\frontend
   ```

### 2. Install Frontend Dependencies
Download all the required Node modules by running:
```cmd
npm install
```
*(This may take a minute depending on your internet connection.)*

### 3. Start the Frontend Server
Once the installation finishes, start the development server:
```cmd
npm run dev
```
**Success Indicator:** You should see green text stating `VITE vX.X.X  ready in X ms` along with a local network address showing `http://localhost:5173/`. 
**DO NOT close this terminal window.**

---

## Part 4: Accessing the Application

With both terminals successfully running in the background:

1. Open your favorite web browser (Chrome, Edge, Firefox, etc.).
2. Navigate to the frontend UI address:
   👉 **http://localhost:5173**
3. **Register Your Admin Account:**
   - Since this is the first time running the app, go to the **Register** page.
   - The very first user account created automatically becomes the system Administrator.
   - Enter your desired Username, Email, and Password to create the account.
4. **Log In:**
   - Use the credentials you just created to log in.
5. **Start Scanning!** 
   - You can now navigate to the **Discover Subdomains** tab to manually scan a domain, or configure your background scheduled workers in the **Admin Dashboard**!

---

## Summary of Daily Usage
Going forward, whenever you restart your computer and want to use ISMAP, you will always need those two terminals:

**Terminal 1 (Backend):**
```cmd
cd path\to\ismap
venv\Scripts\activate
python app.py
```

**Terminal 2 (Frontend):**
```cmd
cd path\to\ismap\frontend
npm run dev
```
