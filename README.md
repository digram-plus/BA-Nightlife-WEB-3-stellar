# BA Nightlife Web3

BA Nightlife is a live music discovery and tipping app for Buenos Aires. It aggregates underground events and lets fans tip artists with native BNB on BNB Chain.

## Hackathon
- Event: Good Vibes Only Hackathon (BNB Chain)
- Track: Touching Grass (real-world culture + onchain support)

## Core Features
- Event aggregation from multiple sources
- Wallet-based tipping (native BNB)
- Artist support wallets per event

## BNB Chain Proof
- Example transaction: https://bscscan.com/tx/0x2b6b0f7de3531f88f039a0400dc135e911c27a0eb255b92da3277174f2693c94

## Tech Stack
- Backend: FastAPI, SQLAlchemy, Postgres
- Frontend: Next.js, RainbowKit, Wagmi, Tailwind

## Local Setup

### 1) Backend
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` in repo root:
```
POSTGRES_DB=baevents
POSTGRES_USER=ba
POSTGRES_PASSWORD=ba_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

TG_BOT_TOKEN=your_token
TG_API_ID=0
TG_API_HASH=
TG_SESSION=ba_events_session
TG_CHANNELS=AfishaBA,vista_argentina,buenosaires_afisha,TechnoLoversBA,eventosbsas
TG_CHANNEL_ID=

# Protect scraper triggers
SCRAPE_API_KEY=change_me
```

Run API:
```bash
uvicorn app.api:app --reload --port 8000
```

### 2) Frontend
```bash
cd frontend
npm install
```

Create `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID=your_walletconnect_project_id
```

Run dev server:
```bash
npm run dev
```

## Demo
- Demo video: <ADD_X_LINK>
- Project X account: https://x.com/BA_Nightlife
