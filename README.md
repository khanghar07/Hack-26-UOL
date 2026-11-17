# NovaWorks CRM · Hack’26 UOL
A Firebase-authenticated CRM that turns a client meeting into saved projects and assigned developer tasks. React 19 / Vite 8, Python 3.12 / FastAPI, PostgreSQL or SQLite, and OpenRouter structured extraction. The included frontend build targets the local Firebase Auth Emulator and is served directly by FastAPI.

## Run the demo on macOS or Linux
Install Python 3.12 and Node 22.12+ or 24. Extract the ZIP and enter the novaworks directory. Use two terminals in that directory.

Terminal 1:
```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```
Set ADMIN_PASSWORD and OPENROUTER_API_KEY in .env. The admin email defaults to khanghar07@gmail.com. For a fresh local emulator you choose the password. Then run:
```sh
npx --yes firebase-tools@14 emulators:start --only auth --project demo-novaworks
```

Terminal 2:
```sh
source .venv/bin/activate
python seed.py
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```
Open http://127.0.0.1:8000. Rerun the seeder when starting a fresh emulator. The default local SQLite database persists across restarts. On Windows use the virtual environment's Scripts/Activate.ps1 and Copy-Item in PowerShell.

## Aiven PostgreSQL
To use your Aiven service, run `python configure_aiven.py` before seeding. Paste the complete service URI at its hidden prompt. The helper checks TLS and saves DATABASE_URL only after successful connectivity. Run seed.py then restart the API. The same application supports local PostgreSQL. The supplied Aiven hostname could not be resolved from the build workspace; no hosted schema or data write is claimed. Keep emulator and hosted Firebase profiles in separate databases.

## Demo accounts
| Role | Name | Email | Password |
|---|---|---|---|
|Admin|Admin|khanghar07@gmail.com|Private ADMIN_PASSWORD|
|Manager|Ayesha Khan|ayesha@novaworks.example|Demo123!|
|Manager|Bilal Ahmed|bilal@novaworks.example|Demo123!|
|Manager|Hina Malik|hina@novaworks.example|Demo123!|
|Developer|Ali Raza|ali@novaworks.example|Demo123!|
|Developer|Hamza Shah|hamza@novaworks.example|Demo123!|
|Developer|Sara Noor|sara@novaworks.example|Demo123!|
|Developer|Usman Tariq|usman@novaworks.example|Demo123!|
|Developer|Zain Abbas|zain@novaworks.example|Demo123!|
|Developer|Maryam Asif|maryam@novaworks.example|Demo123!|

## Judge walkthrough
1. Sign in as admin. Open Team Directory, then Projects → Create from Transcript. Paste sample_transcript.txt and keep the meeting date 2026-10-07.
2. Click Create. The backend validates the AI output and saves it in one transaction. Success displays actual counts. The supplied meeting produces UrbanCart, QuickServe and HelpDeskPro with four tasks each, totaling 40, 46 and 38 hours. Refresh the page, or resubmit the same text and date to check persistence and replay protection.
3. Ayesha sees only UrbanCart. Ali sees his three UrbanCart tasks. Hamza sees two API tasks across UrbanCart and QuickServe, including only his own task on each detail page.
4. In a fresh demo database change Usman's final agreement and recap from 10 hours / 22 October to 12 hours / 23 October. The QuickServe total becomes 48 hours. The altered meeting is a new import.
5. Missing owners, unclear estimates or invalid dates request correction. The original text stays in the editor. Provider outages can be retried. To clear only generated records in your chosen **demo** database, stop the API and run `python reset_demo.py --delete-generated-projects`. This deletes its projects, tasks and replay history.

## Configuration and hosted mode
The two .env examples document the runtime settings. DATABASE_PATH selects local SQLite; DATABASE_URL selects PostgreSQL. FIREBASE_PROJECT_ID and FIREBASE_AUTH_EMULATOR_HOST select the auth environment. Hosted Firebase uses GOOGLE_APPLICATION_CREDENTIALS pointing to a private project service-account file. AI_PROVIDER, OPENROUTER_MODEL, OPENROUTER_API_KEY and optional AI_FALLBACK_PROVIDER / GEMINI_MODEL / GEMINI_API_KEY configure extraction. OpenRouter free routing was tested; model availability varies. FRONTEND_ORIGIN controls CORS. The frontend normally uses same-origin API requests.

For hosted Firebase, use .env.hosted.example as .env, supply private settings and run python seed.py with the project service account. Build the frontend using `cd frontend && npm ci && npm run build` and restart the backend. To rebuild for the emulator use `VITE_AUTH_EMULATOR=true npm run build`. The Dockerfile builds the hosted frontend and serves both layers together. Production is deployed from GitHub main to Vercel, with Aiven PostgreSQL and hosted Firebase Authentication.

## Verification and submission
See FINAL_CHECKS.md and demo.mp4. Automated tests use isolated databases and Auth Emulator users. With the local .env and a stopped emulator:
```sh
npx --yes firebase-tools@14 emulators:exec --only auth --project demo-novaworks "python check_phase1.py && python check_phase2.py && python check_security.py && python check_phase3.py && python check_providers.py"
```
Run python check_phase3.py --live for original, modified and missing-value AI cases (uses provider quota). Source matching requires the final task title and hours together in the meeting recap. The backend rejects an unsupported estimate. The UI supports desktop and mobile widths.

Production application: https://novaworks-hack26-uol.vercel.app

Source: https://github.com/khanghar07/Hack-26-UOL

Demo recording (fixture AI response): [demo.mp4](./demo.mp4). For a live demo, use the accounts above. The admin password is shared privately.

Team details pending: official team name, four participant names and responsibilities.
