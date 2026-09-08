# Kaleido

Kaleido is a creator-membership platform. Django owns the domain logic, database, media storage, Stripe integration and REST API; React/Vite provides the user-facing application.

## Local development

1. Create a Python virtual environment in `backend/venv` and install `backend/requirements/dev.txt`.
2. Copy `backend/.env.example` to `backend/.env`, then provide valid database, Django, Stripe and email values.
3. Run migrations from `backend`: `python manage.py migrate`.
4. Start Django: `python manage.py runserver`.
5. In `frontend`, run `npm ci` and then `npm run dev`.

The Vite proxy forwards `/api` and `/media` to Django at `127.0.0.1:8000`.

## React routes

- `/`: public feed with search and category filtering
- `/content/:id`, `/collections/:id`, `/profile/:id`: public content and creator pages
- `/subscriptions`, `/history`, `/saved`, `/settings`: authenticated user features
- `/creator`: creator tools for content, tiers and collections

## API principles

All state-changing API endpoints require JWT authentication. Creator-specific endpoints additionally check `is_creator` on the server; user/creator ownership is always taken from the token, never from request payloads. Stripe webhooks continue to be signature-verified by Django.

## Before deployment

Deployment is deliberately out of scope for this stage. Configure production hosts, HTTPS, durable media storage, database backups, Stripe webhook endpoint and appropriate secrets before enabling production settings.
