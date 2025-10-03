CRYPTO-FRAUD-DEMO
----------------
A full-stack demo application for reporting, investigating, and managing fraudulent Ethereum wallets.

Features
--------
1. Report Fraud: Users can submit reports of suspicious wallets and fraud types.
2. Admin Dashboard: View, update, and manage fraud reports.
3. Investigator Dashboard: Lookup wallet details, view transactions, and flag suspicious activity.
4. SQLite Database: Stores reports and investigations.
5. Ethereum Integration: Fetches wallet balances and transactions using Alchemy API.

Tech Stack
----------
1. Backend: Python, Flask, SQLAlchemy, SQLite, Alchemy API
2. Frontend: HTML, CSS, JavaScript
3. Environment: .env for secrets and API keys

SETUP
-----
1. Open backend path
2. create virtual environment using:
    python -m venv venv
inside CMD or VS code terminal
3. If using windows use:
    venv\Scripts\activate
4. Install Python dependencies:

    pip install -r backend/requirements.txt

5. Set up .env in backend with your Alchemy API key.
6. Run the backend:
   Python backend/app.py
7. open index.html, admin.html, or investigator.html in your browser

PREREQUISITES
-------------
1. Python 3.11 or 3.12  installed in the system
2. Virtual Studio Code 
3. Live Server(Extension installed on Virtual Studio Code)

#Assumptions
1. Users provide valid Ethereum wallet addresses.
2. The backend has a valid Alchemy API key set in .env.

#Limitations

1. Only supports Ethereum wallets (no other blockchains).
2. No authentication—anyone can submit or view reports.
