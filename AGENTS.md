# AGENTS.md

## Cursor Cloud specific instructions

### Project Overview
AlgoForge는 알고리즘 트레이딩 전략 백테스팅 도구입니다. 자세한 내용은 `README.md` 참조.

### Services

| Service | Port | Command |
|---------|------|---------|
| FastAPI Backend | 6000 | `source .venv/bin/activate && python -m uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 6000` |
| Next.js Frontend | 5001 | `cd apps/web && pnpm dev` |

SQLite database (`db/algoforge.db`) is auto-created on API startup. No external DB needed.

### Known Issues

- **Root `.gitignore` blocks `lib/` globally** (line 13): This Python packaging pattern also excludes `apps/web/lib/`, preventing frontend lib files from being tracked. The Next.js frontend fails to compile (500 error) because `@/lib/api-client`, `@/lib/types`, etc. are missing from the repository. The developer has these files locally but they were never committed.
- **Chrome blocks port 6000** by default (ERR_UNSAFE_PORT). Launch Chrome with `--explicitly-allowed-ports=6000` to access the Swagger UI at `http://localhost:6000/docs`.
- Backend pytest: 18 tests fail due to pre-existing assertion/validation issues (67 pass). See `pyproject.toml` for test config.
- Frontend Jest tests: all 7 suites fail due to missing `lib/` modules (same root cause as above).

### Commands Reference

See `README.md` for full list. Key commands:
- **Backend tests**: `source .venv/bin/activate && pytest`
- **Frontend lint**: `cd apps/web && pnpm lint`
- **Frontend tests**: `cd apps/web && pnpm test`
- **API docs**: http://localhost:6000/docs (Swagger UI)
- **Health check**: http://localhost:6000/health

### System Dependencies

- Python 3.10+ (uses `.venv` virtual environment in project root)
- Node.js 22.x with pnpm (for `apps/web`)
- `python3.12-venv` apt package required if not pre-installed
