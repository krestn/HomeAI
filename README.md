# HomeAI
An AI-powered personal assistant for all things homeownership.

## Backend requirements
pip install -r requirements.txt

## Useful Backend Commands
pip freeze > requirements.txt
python -m test.test_zillow

## Start Backend
cd backend
uvicorn app.main:app

## Frontend (Next.js)
```
cd frontend
npm install
npm run dev
```
- Runs on http://localhost:3000 and points to the FastAPI backend by default.
- Provides login, chat experience backed by `/agent/chat`, and logout handling.

## Database Migrations with Alembic (Frequently used commands below)
alembic revision --autogenerate -m "name"
alembic upgrade head
alembic downgrade -1
