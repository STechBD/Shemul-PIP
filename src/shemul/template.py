from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Any, Dict, List


TemplateInfo = Dict[str, str]


_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "docker-fastapi-backend": {
        "title": "Docker FastAPI Backend",
        "aliases": ["docker fastapi backend", "docker-fastapi", "fastapi-docker"],
        "desc": "FastAPI backend using docker compose for local/prod workflows.",
    },
    "fastapi-backend": {
        "title": "FastAPI Backend",
        "aliases": ["fastapi backend", "fastapi"],
        "desc": "Local FastAPI backend workflow without docker.",
    },
    "django-drf-backend": {
        "title": "Django DRF Backend",
        "aliases": ["django drf backend", "drf backend", "django-backend"],
        "desc": "Django + DRF backend workflow.",
    },
    "expressjs-backend": {
        "title": "Express.js Backend",
        "aliases": ["express.js backend", "express backend", "expressjs", "express"],
        "desc": "Express.js backend workflow.",
    },
    "nestjs-backend": {
        "title": "Nest.js Backend",
        "aliases": ["nest.js backend", "nest backend", "nestjs", "nest"],
        "desc": "Nest.js backend workflow.",
    },
    "react-native-expo-app": {
        "title": "React Native Expo App",
        "aliases": ["react native expo app", "expo app", "react-native", "expo"],
        "desc": "React Native app workflow using Expo.",
    },
    "nextjs-frontend": {
        "title": "Next.js Frontend",
        "aliases": ["next.js frontend", "next frontend", "nextjs"],
        "desc": "Next.js frontend workflow.",
    },
    "none": {
        "title": "None (Starter Schema)",
        "aliases": ["blank", "starter", "minimal"],
        "desc": "Minimal valid shemul.json to get started quickly.",
    },
}


def _normalize(text: str) -> str:
    text = text.strip().lower()
    text = text.replace(".", "")
    text = text.replace("_", " ")
    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def list_templates() -> List[TemplateInfo]:
    items: List[TemplateInfo] = []
    for key, data in _TEMPLATES.items():
        items.append({"key": key, "title": data["title"], "desc": data["desc"]})
    return items


def resolve_template_key(template_name: str) -> str | None:
    query = _normalize(template_name)
    if not query:
        return None
    for key, data in _TEMPLATES.items():
        if query == _normalize(key):
            return key
        if query == _normalize(data["title"]):
            return key
        for alias in data["aliases"]:
            if query == _normalize(alias):
                return key
    return None


def template_aliases(key: str) -> List[str]:
    data = _TEMPLATES.get(key)
    if not data:
        return []
    return list(data["aliases"])


def build_template_config(template_key: str, project_name: str) -> Dict[str, Any]:
    base = {
        "$schema": "https://shemul.dev/schema.json",
        "name": project_name,
        "version": "1.0",
        "commands": {},
    }

    if template_key == "docker-fastapi-backend":
        base["runtime"] = "docker"
        base["env"] = {
            "local": {"compose": "docker-compose.yml"},
            "prod": {"compose": "docker-compose.prod.yml"},
        }
        base["vars"] = {"API": "api"}
        base["commands"] = {
            "up": {"run": "docker compose up --build", "env": "local", "desc": "Start local stack"},
            "up:bg": {"run": "docker compose up -d --build", "env": "local", "desc": "Start local stack in background"},
            "down": {"run": "docker compose down --remove-orphans", "env": "local", "desc": "Stop local stack"},
            "logs": {"run": "docker compose logs -f {{API}}", "env": "local", "desc": "Tail API logs"},
            "migrate:up": {"run": "docker compose exec {{API}} alembic upgrade head", "confirm": True, "desc": "Run DB migrations"},
            "test": {"run": "docker compose exec {{API}} pytest -q", "group": "quality", "desc": "Run tests"},
            "prod:up": {"run": "docker compose -f {{env.compose}} up -d", "env": "prod", "danger": True, "desc": "Start production stack"},
        }
    elif template_key == "fastapi-backend":
        base["runtime"] = "python"
        base["commands"] = {
            "dev": {"run": "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000", "desc": "Run dev server"},
            "start": {"run": "python -m app.main", "desc": "Run app entrypoint"},
            "test": {"run": "pytest -q", "group": "quality", "desc": "Run tests"},
            "lint": {"run": "ruff check .", "group": "quality", "desc": "Run linter"},
            "format": {"run": "ruff format .", "group": "quality", "desc": "Format source"},
        }
    elif template_key == "django-drf-backend":
        base["runtime"] = "python"
        base["commands"] = {
            "dev": {"run": "python manage.py runserver 0.0.0.0:8000", "desc": "Run dev server"},
            "migrate:make": {"run": "python manage.py makemigrations", "group": "db", "desc": "Create migrations"},
            "migrate:up": {"run": "python manage.py migrate", "group": "db", "desc": "Apply migrations"},
            "superuser": {"run": "python manage.py createsuperuser", "confirm": True, "desc": "Create admin user"},
            "test": {"run": "python manage.py test", "group": "quality", "desc": "Run tests"},
            "lint": {"run": "ruff check .", "group": "quality", "desc": "Run linter"},
        }
    elif template_key == "expressjs-backend":
        base["runtime"] = "node"
        base["commands"] = {
            "install": {"run": "npm install", "group": "setup", "desc": "Install dependencies"},
            "dev": {"run": "npm run dev", "desc": "Run dev server"},
            "start": {"run": "npm start", "desc": "Run production server"},
            "test": {"run": "npm test", "group": "quality", "desc": "Run tests"},
            "lint": {"run": "npm run lint", "group": "quality", "desc": "Run linter"},
        }
    elif template_key == "nestjs-backend":
        base["runtime"] = "node"
        base["commands"] = {
            "install": {"run": "npm install", "group": "setup", "desc": "Install dependencies"},
            "dev": {"run": "npm run start:dev", "desc": "Run dev server"},
            "build": {"run": "npm run build", "group": "build", "desc": "Build application"},
            "start": {"run": "npm run start:prod", "desc": "Run production server"},
            "test": {"run": "npm run test", "group": "quality", "desc": "Run tests"},
            "lint": {"run": "npm run lint", "group": "quality", "desc": "Run linter"},
        }
    elif template_key == "react-native-expo-app":
        base["runtime"] = "node"
        base["commands"] = {
            "install": {"run": "npm install", "group": "setup", "desc": "Install dependencies"},
            "dev": {"run": "npx expo start", "desc": "Start Expo dev server"},
            "android": {"run": "npx expo run:android", "desc": "Run Android build"},
            "ios": {"run": "npx expo run:ios", "desc": "Run iOS build"},
            "web": {"run": "npx expo start --web", "desc": "Run web preview"},
            "test": {"run": "npm test", "group": "quality", "desc": "Run tests"},
        }
    elif template_key == "nextjs-frontend":
        base["runtime"] = "node"
        base["commands"] = {
            "install": {"run": "npm install", "group": "setup", "desc": "Install dependencies"},
            "dev": {"run": "npm run dev", "desc": "Run dev server"},
            "build": {"run": "npm run build", "group": "build", "desc": "Build frontend"},
            "start": {"run": "npm run start", "desc": "Run production server"},
            "lint": {"run": "npm run lint", "group": "quality", "desc": "Run linter"},
            "test": {"run": "npm test", "group": "quality", "desc": "Run tests"},
        }
    else:
        base["runtime"] = "generic"
        base["commands"] = {
            "example": {
                "run": "echo \"Edit shemul.json and replace this command\"",
                "desc": "Starter command",
            }
        }

    return base


def write_template_file(template_key: str, target_path: Path, project_name: str, force: bool = False) -> Path:
    if target_path.exists() and not force:
        raise FileExistsError(f"{target_path} already exists")
    payload = build_template_config(template_key, project_name)
    target_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target_path
