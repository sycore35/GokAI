---
name: fastapi-services
description: FastAPI asynchronous REST API best practices and dependency injection
when_to_use: "Use when creating FastAPI backends, endpoints, routers, or microservices"
tags: ["fastapi", "api", "rest", "backend", "python"]
---

# FastAPI Service Guidelines

1. Use APIRouter to group endpoints logically (e.g. `/api/users`, `/api/tasks`).
2. Use Pydantic v2 `BaseModel` schemas for request body validation and response serialization.
3. Use async def route handlers with proper HTTP status codes (`status_code=201` for creations).
4. Implement standard HTTPException handling with clear error detail messages.
5. Provide automatic OpenAPI interactive documentation via `/docs`.
