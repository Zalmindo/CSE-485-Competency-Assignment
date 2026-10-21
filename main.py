from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from db import SkillStore, timestamp
from models import Skill, SkillIn, SkillPatch, Status

app = FastAPI(
    title="Competency Tracker API",
    description="Keeps track of the skills I'm learning. Made for my Growing a Competency assignment.",
    version="1.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

store = SkillStore()


ERROR_NAMES = {
    400: "bad_request",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
}


def error_response(status_code, message, details=None):
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "status": status_code,
                "code": ERROR_NAMES.get(status_code, "error"),
                "message": message,
                "details": details,
            }
        },
    )


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(request, exc):
    message = exc.detail
    if exc.status_code == 404 and exc.detail == "Not Found":
        message = "Route not found."
    return error_response(exc.status_code, message)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request, exc):
    problems = []
    for err in exc.errors():
        field = ".".join(str(part) for part in err["loc"] if part != "body")
        problems.append({"field": field, "problem": err["msg"]})
    return error_response(422, "The request data is invalid.", problems)


def find_skill(skill_id):
    skill = store.get(skill_id)
    if skill is None:
        raise HTTPException(404, f"Skill {skill_id} does not exist.")
    return skill


@app.get("/", tags=["Info"])
def home():
    return {
        "name": "Competency Tracker API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "list_skills": "GET /api/v1/skills",
            "get_skill": "GET /api/v1/skills/{id}",
            "create_skill": "POST /api/v1/skills",
            "replace_skill": "PUT /api/v1/skills/{id}",
            "update_skill": "PATCH /api/v1/skills/{id}",
            "delete_skill": "DELETE /api/v1/skills/{id}",
        },
    }


@app.get("/health", tags=["Info"])
def health():
    return {"status": "ok", "time": timestamp(), "skills_stored": len(store.all())}


@app.get("/api/v1/skills", tags=["Skills"])
def list_skills(
    status: Status | None = None,
    category: str | None = None,
    q: str | None = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    results = store.all()

    if status:
        results = [s for s in results if s.status == status]
    if category:
        results = [s for s in results if s.category.lower() == category.lower()]
    if q:
        q = q.lower()
        results = [s for s in results if q in s.name.lower() or q in s.notes.lower()]

    page = results[offset:offset + limit]
    return {
        "data": page,
        "meta": {"total": len(results), "count": len(page), "limit": limit, "offset": offset},
    }


@app.get("/api/v1/skills/{skill_id}", tags=["Skills"])
def get_skill(skill_id: int):
    return {"data": find_skill(skill_id)}


@app.post("/api/v1/skills", status_code=201, tags=["Skills"])
def create_skill(new_skill: SkillIn, response: Response):
    if store.name_taken(new_skill.name):
        raise HTTPException(409, f"A skill named '{new_skill.name}' already exists.")

    skill = store.add(new_skill)
    response.headers["Location"] = f"/api/v1/skills/{skill.id}"
    return {"message": "Skill created.", "data": skill}


@app.put("/api/v1/skills/{skill_id}", tags=["Skills"])
def replace_skill(skill_id: int, new_skill: SkillIn):
    old = find_skill(skill_id)
    if store.name_taken(new_skill.name, skip_id=skill_id):
        raise HTTPException(409, f"A skill named '{new_skill.name}' already exists.")

    skill = Skill(id=skill_id, created_at=old.created_at, updated_at=timestamp(), **new_skill.model_dump())
    store.save(skill)
    return {"message": "Skill replaced.", "data": skill}


@app.patch("/api/v1/skills/{skill_id}", tags=["Skills"])
def update_skill(skill_id: int, patch: SkillPatch):
    changes = patch.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(400, "Send at least one field to update.")

    null_fields = [name for name, value in changes.items() if value is None]
    if null_fields:
        raise HTTPException(400, f"These fields can't be null: {', '.join(null_fields)}")

    skill = find_skill(skill_id)
    if "name" in changes and store.name_taken(changes["name"], skip_id=skill_id):
        raise HTTPException(409, f"A skill named '{changes['name']}' already exists.")

    skill = skill.model_copy(update={**changes, "updated_at": timestamp()})
    store.save(skill)
    return {"message": "Skill updated.", "updated_fields": sorted(changes), "data": skill}


@app.delete("/api/v1/skills/{skill_id}", tags=["Skills"])
def delete_skill(skill_id: int):
    find_skill(skill_id)
    removed = store.remove(skill_id)
    return {"message": f"Skill {skill_id} deleted.", "data": removed}
