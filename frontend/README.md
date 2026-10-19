# NovaShields Frontend

## Common Login

Open:

http://127.0.0.1:5500/login/index.html

The common login supports:
- Rider -> rider-app/home.html
- Guardian -> guardian-dashboard/home.html
- Insurer -> insurer-portal/home.html

Authentication uses the existing shared-api.js and shared-config.js.

## Start frontend

From the `frontend` directory:

python -m http.server 5500

## Backend

The frontend expects:

http://127.0.0.1:8000/api/v1

Start the backend from the NovaShields project root with:

python -m uvicorn backend.main:app --reload
