# URL Shortener (Case Study 01)

A Bitly-style URL shortener built to learn system design. FastAPI, PostgreSQL, Redis, Nginx and Docker Compose.

This is a learning project. It is not production-ready.

## What it does

- Turns a long URL into a short code.
- Redirects short codes to the original URL.
- Caches links in Redis for one hour.
- Counts clicks in the background and saves them to Postgres.
- Runs two app copies behind Nginx.

## Architecture

```
                         ┌──► api1 ──┐
Browser ──► Nginx :8000 ─┤           ├──► Redis (cache + click tallies)
                         └──► api2 ──┘──► PostgreSQL (links + saved totals)
```

## Run it

You need Docker with the Compose plugin.

```
docker compose up --build
```

Everything is available at `http://localhost:8000`.

## Try it

Create a short link:

```
curl -X POST http://localhost:8000/shorten -H "Content-Type: application/json" -d '{"url": "https://example.com"}'
```

Open it (replace `1` with your code):

```
curl -i http://localhost:8000/1
```

See the stats:

```
curl http://localhost:8000/stats/1
```

## API

| Method and path | What it does |
|-----------------|--------------|
| `GET /health` | Health check |
| `POST /shorten` | Create a short link |
| `GET /stats/{short_code}` | Click count for a link |
| `GET /{short_code}` | Redirect to the original URL |

## Settings

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | Postgres connection | set in `docker-compose.yml` |
| `REDIS_URL` | Redis connection | set in `docker-compose.yml` |
| `CACHE_TTL_SECONDS` | How long a link stays cached | `3600` |
| `CLICK_FLUSH_SECONDS` | How often clicks are saved to Postgres | `10` |

## How it works

- **Short codes** are the base62 form of the database ID.
- **Redirects** use `302`, so every visit reaches the app and can be counted.
- **Cache-aside:** Redis is checked first, then Postgres. The `X-Cache` header shows `HIT` or `MISS`.
- **Clicks** add a tally in Redis after the reply is sent. A loop copies the tallies into Postgres every few seconds.
- **Two app copies** share the same Redis and Postgres, so either can serve any request.

## Known limits

- Codes are sequential and guessable.
- No login, rate limiting, HTTPS or link expiry.
- Click totals in Postgres can lag by a few seconds, and unsaved tallies are lost if Redis restarts.
- Nginx is a single point of failure.
- Tables are created when the app starts. There is no migration tool.
- Development settings (`--reload`, simple passwords) are used throughout.