## Purpose

> What does this API do, who consumes it, and what problem does it solve?
> Example: "Exposes CRUD operations for user profiles, consumed by the mobile app and admin dashboard."

## Base URL & Versioning

```
Base URL : https://api.example.com/v1
Version  : v1
Strategy : [URL path / header / query param]
Breaking change policy: [e.g. "New major version for breaking changes; old version supported for 6 months"]
```

## Authentication

> How do callers authenticate? Be specific.

```
Method : [Bearer JWT / API Key / OAuth2 / None]
Header : Authorization: Bearer <token>
Obtain : [How to get a token — login endpoint, dashboard, etc.]
```

## Data Models

> Define shared types here. Endpoints reference these by name.

### `User`
```json
{
  "id": "string (uuid)",
  "email": "string",
  "created_at": "string (ISO 8601)",
  "role": "admin | member | viewer"
}
```

> Add more models as needed.

## Endpoints

### `POST /resource`

**Purpose**: [One sentence]

**Request:**
```json
{
  "field": "type — description"
}
```

**Response `201`:**
```json
{
  "id": "string",
  "field": "value"
}
```

**Errors:**

| Code | Condition | Response body |
|------|-----------|---------------|
| 400  | Missing required field | `{"error": "validation_error", "field": "..."}` |
| 401  | Unauthenticated | `{"error": "unauthorized"}` |
| 409  | Conflict (duplicate) | `{"error": "already_exists"}` |

---

### `GET /resource`

**Purpose**: [One sentence]

**Query params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `page` | integer | No | Page number, 1-indexed (default: 1) |
| `limit` | integer | No | Items per page, max 100 (default: 20) |
| `filter` | string | No | [Filter description] |

**Response `200`:**
```json
{
  "data": ["<Model>"],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "next_cursor": "string | null"
  }
}
```

---

> Add more endpoints following the same pattern.

## Rate Limiting

```
Limit   : [e.g. 100 requests / minute per API key]
Headers : X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
On hit  : 429 Too Many Requests — retry after X-RateLimit-Reset
```

## Error Format

> All errors use a consistent shape:

```json
{
  "error": "snake_case_code",
  "message": "Human-readable description",
  "detail": {}
}
```

## Human Gate Checklist

> When the AI says "done", the human verifies each item before passing the gate.

- [ ] **Hit every endpoint**: use `curl` or API client — request/response shapes match the spec exactly?
- [ ] **Test authentication**: call without a token → expect `401`; call with invalid token → expect `401`?
- [ ] **Test validation errors**: send a request missing required fields → correct `400` response with meaningful error?
- [ ] **Test a conflict / edge case**: [describe the specific scenario for this API]
- [ ] **Check pagination**: if a list endpoint exists, request page 2 — does `next_cursor` / `total` work correctly?
- [ ] **Read the diff**: `git diff main` — no hardcoded secrets, no debug routes, no commented-out endpoints?
