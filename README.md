# PeakPick Identity Service

Owns demo users, stores, and bearer-token authentication.

Owned database tables:

- `stores`
- `identity_users`

Run locally:

```bash
pip install -r requirements.txt
uvicorn services.identity_service.main:app --reload --port 8008
```
