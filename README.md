# Mini Amazon

A Python e-commerce portfolio project with a command-line interface and a FastAPI backend. SQLite stores users, products, carts and orders.

## Features

- Registration and login with Argon2 password hashing and legacy SHA-256 migration.
- Product browsing, search and stock management.
- Per-user shopping carts.
- Transactional checkout: save the order, reduce stock and clear the cart together.
- JWT-protected cart and order routes, with ownership checks for individual orders.
- Automated tests using isolated temporary SQLite databases.

## Setup (PowerShell)

Run these commands from the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python seed_data.py
```

The seed command creates missing tables and adds missing demo products. It preserves existing products.

### API authentication

Create a local `.env` file containing `JWT_SECRET=<your-random-secret>`.
Generate a secret using:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the generated value into `.env`. That file is excluded from Git.

### Start the API

```powershell
python -m uvicorn api:app --reload
```

Open [interactive API documentation](http://127.0.0.1:8000/docs).

1. Register with `POST /auth/register`. Passwords require at least eight characters and one digit.
2. Log in with `POST /auth/login`.
3. Copy the returned access token into Swagger's **Authorize** dialog.
4. Add products using `POST /cart/items`.
5. Check out with `POST /orders`.
6. Read your history with `GET /orders`.

The authenticated username comes from the token. An order belonging to another user returns the same `404` response as a missing order. Empty carts and insufficient stock return `400`.

Use `api:app` as the server entry point. The separate `app.py` is an earlier prototype.

### Command-line interface

```powershell
python main.py
```

## API routes

| Area | Routes |
| --- | --- |
| General | `GET /`, `GET /health` |
| Products | `GET /products`, `GET /products/search`, `GET /products/{product_id}` |
| Authentication | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| Cart (authenticated) | `GET /cart`, `POST /cart/items`, `PATCH /cart/items/{product_id}`, `DELETE /cart/items/{product_id}`, `DELETE /cart` |
| Orders (authenticated) | `POST /orders`, `GET /orders`, `GET /orders/{order_id}` |

## Tests

```powershell
python -m pytest -q
```

Each test uses its own temporary database. API tests supply a test-only signing secret and exercise the real login, cart and order routes without starting a server or requiring a local `.env`.

Coverage includes checkout totals, stock changes, cart clearing, private order history, invalid/expired tokens, insufficient stock and rollback after a simulated database failure.

## Automatic tests on GitHub

The workflow in `.github/workflows/tests.yml` runs on every push and pull request using Python 3.13 on Ubuntu. It installs the project dependencies, checks their compatibility, and runs `python -m pytest -q`.

Commit the workflow together with your current application files, tests and requirements, then push your branch. On GitHub, open the repository's **Actions** tab and select **Python tests** to see the result. Expand a failed step to read the error.

The API tests configure their own test secret and temporary databases; no GitHub secrets or development database are needed. The workflow also supports manual runs once it is on the default branch.

## Project structure

- `api.py`: authenticated REST API and request validation.
- `auth.py`: JWT creation and validation.
- `database.py`: SQLite connections and schema.
- `users.py`, `products.py`, `cart.py`, `orders.py`: business logic.
- `main.py`: command-line interface.
- `seed_data.py`: demo products.
- `tests/`: business-logic and HTTP API tests.

## Next improvements

- More consistent error handling.
- Integer cents or Decimal for money calculations.
- Docker.
- PostgreSQL and deployment.
