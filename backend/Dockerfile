FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./backend/
RUN cd backend && uv pip install --system --requirement pyproject.toml
COPY backend/ ./backend/
COPY docs/ ./docs/
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
