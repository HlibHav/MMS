"""
Webhook endpoints (stubs) to mirror documented events.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from backend.api.dependencies import auth_guard, rate_limit_guard

router = APIRouter(
    tags=["webhooks"],
    dependencies=[Depends(auth_guard), Depends(rate_limit_guard)],
)


@router.post("/scenario/validated")
async def scenario_validated(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Stub webhook receiver for scenario.validated."""
    return {"received": True, "event": "scenario.validated", "data": payload}


@router.post("/data/processing-completed")
async def data_processing_completed(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Stub webhook receiver for data.processing.completed."""
    return {"received": True, "event": "data.processing.completed", "data": payload}


@router.post("/creative/generated")
async def creative_generated(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Stub webhook receiver for creative.generated."""
    return {"received": True, "event": "creative.generated", "data": payload}
