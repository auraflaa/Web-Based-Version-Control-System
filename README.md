# Web-Based-Version-Control-System

## Database Schema Migrations

This project uses **Alembic** to manage database schema changes and ensure alignment between your models and the database.

### Common Alembic Commands
- **Create a new migration after changing models:**
  ```
  alembic revision --autogenerate -m "Describe your change"
  ```
- **Apply migrations to the database:**
  ```
  alembic upgrade head
  ```
- **Stamp the current DB state (if already aligned):**
  ```
  alembic stamp head
  ```

See `server/alembic/` for migration scripts.

## Atomic Database Operations

For multi-step operations, use database transactions to ensure atomicity. See `server/utils.py` for a utility function:

```
from server.utils import run_atomic_transaction

def ops():
    db.session.add(obj1)
    db.session.add(obj2)
run_atomic_transaction(ops)
```

If any operation fails, all changes are rolled back.
