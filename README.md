# RHYTHM — Emotion-Aware Personalized Music Recommendation Framework

## Current milestone
Frontend authentication UI based on the approved minimalist RHYTHM design.

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

Frontend routes:
- `/login`
- `/register`

Backend health check:
- `GET /api/health`

## Planned flow
Login/Register → Camera → Emotion Detection → Personalized Recommendations
