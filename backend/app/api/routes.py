"""All public `/api` endpoints."""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from starlette.datastructures import UploadFile

from app.api import service
from app.auth import Principal, create_token, current_principal, require_hr, require_self_or_hr
from app.hr.analytics import overview
from app.models import (
    ActivityRequest,
    Catalog,
    Health,
    HrEmployeeSummary,
    HrOverview,
    ImportReport,
    Language,
    LoginRequest,
    LoginResponse,
    PersonSummary,
    Profile,
    ProgressUpdate,
    RecommendationMode,
    RecommendationResult,
    AskRequest,
    AskResponse,
    LandingEvent,
)
from app.store import CareerStore


router = APIRouter(prefix="/api")


def get_store(request: Request) -> CareerStore:
    return request.app.state.store


Store = Annotated[CareerStore, Depends(get_store)]


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, store: Store) -> LoginResponse:
    if payload.role == "employee":
        if not payload.employee_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="employee_id is required for employee login")
        if not store.employee(payload.employee_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    employee_id = payload.employee_id if payload.role == "employee" else None
    return LoginResponse(token=create_token(payload.role, employee_id), role=payload.role, employee_id=employee_id)


@router.get("/demo/people", response_model=list[PersonSummary])
def demo_people(store: Store) -> list[PersonSummary]:
    return [
        PersonSummary(
            employee_id=employee["employee_id"],
            full_name=employee["full_name"],
            role=employee["role"],
            grade=employee["grade"],
        )
        for employee in sorted(store.employees.values(), key=lambda item: item["full_name"])
    ]


@router.get("/health", response_model=Health)
def health() -> Health:
    key = os.getenv("LLM_API_KEY", "")
    try:
        from app.llm.client import llm_enabled, model_name
        enabled = llm_enabled()
    except Exception:
        enabled = bool(key)
    return Health(status="ok", llm_enabled=enabled, model=(model_name() if enabled else None))


@router.get("/employees/{employee_id}", response_model=Profile)
def get_employee(employee_id: str, store: Store, _: Principal = Depends(require_self_or_hr)) -> Profile:
    try:
        return service.profile(store, employee_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found") from None


@router.get("/employees/{employee_id}/recommendations", response_model=RecommendationResult)
def get_recommendations(
    employee_id: str,
    store: Store,
    _: Principal = Depends(require_self_or_hr),
    mode: RecommendationMode = "rules",
    lang: Language | None = None,
) -> RecommendationResult:
    if not store.employee(employee_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return service.recommend(store, employee_id, mode, lang)


@router.post("/employees/{employee_id}/activities", response_model=ProgressUpdate)
def update_activity(
    employee_id: str, payload: ActivityRequest, store: Store, principal: Principal = Depends(require_self_or_hr)
) -> ProgressUpdate:
    if principal.role != "employee":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only employees can update their own activities")
    if not store.employee(employee_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    try:
        return service.apply_activity(store, employee_id, payload.event_id, payload.action)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found") from None


@router.post("/employees/{employee_id}/ask", response_model=AskResponse)
def ask_question(
    employee_id: str, payload: AskRequest, store: Store, _: Principal = Depends(require_self_or_hr)
) -> AskResponse:
    if not store.employee(employee_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return AskResponse.model_validate(service.ask(store, employee_id, payload.question, payload.lang))


@router.get("/catalog", response_model=Catalog)
def catalog(store: Store, _: Principal = Depends(current_principal)) -> Catalog:
    return Catalog(skills=list(store.skills.values()), proficiency_scale=store.proficiency_scale, events=list(store.events.values()))


@router.get("/hr/overview", response_model=HrOverview)
def hr_overview(store: Store, _: Principal = Depends(require_hr), department: str | None = None) -> HrOverview:
    return overview(store, department)


@router.get("/hr/employees", response_model=list[HrEmployeeSummary])
def hr_employees(store: Store, _: Principal = Depends(require_hr), q: str | None = None) -> list[HrEmployeeSummary]:
    query = (q or "").casefold()
    result = []
    for employee in store.employees.values():
        haystack = f"{employee['employee_id']} {employee['full_name']} {employee['role']} {employee['grade']}".casefold()
        if query and query not in haystack:
            continue
        recommendation = service.recommend(store, employee["employee_id"])
        result.append(HrEmployeeSummary(employee_id=employee["employee_id"], full_name=employee["full_name"], role=employee["role"], grade=employee["grade"], empty_reason=recommendation.empty_reason))
    return sorted(result, key=lambda item: item.full_name)


@router.post("/hr/import", response_model=ImportReport)
async def import_data(request: Request, store: Store, _: Principal = Depends(require_hr)) -> ImportReport:
    form = await request.form()
    uploads: list[tuple[str, bytes]] = []
    for field_name, value in form.multi_items():
        if not isinstance(value, UploadFile):
            continue
        filename = value.filename or field_name
        uploads.append((filename, await value.read()))
    return ImportReport.model_validate(store.import_files(uploads))


@router.post("/landing/events", status_code=status.HTTP_204_NO_CONTENT)
def landing_event(payload: LandingEvent, store: Store) -> Response:
    """Anonymous landing analytics (demo_opened / contact_clicked), stored in data/runtime."""
    store.record_landing_event(payload.model_dump())
    return Response(status_code=status.HTTP_204_NO_CONTENT)
