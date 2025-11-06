"""Langfuse tracing API endpoints."""

from __future__ import annotations

import base64
import os
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/langfuse", tags=["Langfuse"])


class TraceItem(BaseModel):
    """Single trace item."""

    id: str
    name: str | None = None
    timestamp: str
    input: dict[str, Any] | None = None
    output: dict[str, Any] | None = None
    total_cost: float | None = None
    metadata: dict[str, Any] | None = None


class TracesResponse(BaseModel):
    """Response for traces list."""

    traces: list[TraceItem]
    total: int
    has_more: bool


class TraceDetailResponse(BaseModel):
    """Response for single trace detail."""

    id: str
    name: str | None = None
    timestamp: str
    input: dict[str, Any] | None = None
    output: dict[str, Any] | None = None
    total_cost: float | None = None
    metadata: dict[str, Any] | None = None
    user_id: str | None = None
    session_id: str | None = None


class ConnectionStatusResponse(BaseModel):
    """Response for connection status."""

    connected: bool
    host: str | None = None
    error: str | None = None


def _get_langfuse_config():
    """Get Langfuse configuration."""
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    host = os.getenv("LANGFUSE_HOST")

    if not all([secret_key, public_key, host]):
        return None, "Langfuse environment variables not configured"

    # Create Basic Auth header
    credentials = f"{public_key}:{secret_key}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    auth_header = f"Basic {encoded_credentials}"

    return {
        "host": host,
        "auth_header": auth_header,
    }, None


@router.get("/status", response_model=ConnectionStatusResponse)
async def get_connection_status() -> ConnectionStatusResponse:
    """
    Check Langfuse connection status.

    Returns connection status including host and any error messages.
    """
    config, error = _get_langfuse_config()

    if error:
        return ConnectionStatusResponse(
            connected=False,
            host=os.getenv("LANGFUSE_HOST"),
            error=error,
        )

    # Test connection by making a simple API call
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config['host']}/api/public/traces",
                headers={"Authorization": config["auth_header"]},
                params={"limit": 1},
                timeout=5.0,
            )

            if response.status_code == 401:
                return ConnectionStatusResponse(
                    connected=False,
                    host=config["host"],
                    error="Invalid credentials. Check your Langfuse API keys.",
                )

            if response.status_code >= 400:
                return ConnectionStatusResponse(
                    connected=False,
                    host=config["host"],
                    error=f"HTTP {response.status_code}: {response.text}",
                )

            return ConnectionStatusResponse(
                connected=True,
                host=config["host"],
                error=None,
            )

    except Exception as e:
        return ConnectionStatusResponse(
            connected=False,
            host=config["host"],
            error=f"Connection error: {e}",
        )


@router.get("/traces", response_model=TracesResponse)
async def get_traces(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> TracesResponse:
    """
    Get list of traces from Langfuse.

    Args:
        limit: Maximum number of traces to return (1-100)
        offset: Number of traces to skip

    Returns:
        List of traces with pagination info
    """
    config, error = _get_langfuse_config()

    if error:
        raise HTTPException(status_code=503, detail=error)

    try:
        # Calculate page number (1-indexed)
        page = (offset // limit) + 1

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config['host']}/api/public/traces",
                headers={"Authorization": config["auth_header"]},
                params={"page": page, "limit": limit},
                timeout=10.0,
            )

            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid Langfuse credentials")

            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Langfuse API error: {response.text}",
                )

            data = response.json()

            traces = []
            for trace in data.get("data", []):
                traces.append(
                    TraceItem(
                        id=trace.get("id", ""),
                        name=trace.get("name"),
                        timestamp=trace.get("timestamp", ""),
                        input=trace.get("input"),
                        output=trace.get("output"),
                        total_cost=trace.get("totalCost"),
                        metadata=trace.get("metadata"),
                    )
                )

            # Extract metadata from response
            meta = data.get("meta", {})
            total = meta.get("totalItems", len(traces))
            total_pages = meta.get("totalPages", 1)
            has_more = page < total_pages

            return TracesResponse(
                traces=traces,
                total=total,
                has_more=has_more,
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching traces: {e}")


@router.get("/traces/{trace_id}", response_model=TraceDetailResponse)
async def get_trace_detail(trace_id: str) -> TraceDetailResponse:
    """
    Get detailed information for a specific trace.

    Args:
        trace_id: The trace ID to fetch

    Returns:
        Detailed trace information
    """
    config, error = _get_langfuse_config()

    if error:
        raise HTTPException(status_code=503, detail=error)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config['host']}/api/public/traces/{trace_id}",
                headers={"Authorization": config["auth_header"]},
                timeout=10.0,
            )

            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid Langfuse credentials")

            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Trace not found")

            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Langfuse API error: {response.text}",
                )

            trace = response.json()

            return TraceDetailResponse(
                id=trace.get("id", ""),
                name=trace.get("name"),
                timestamp=trace.get("timestamp", ""),
                input=trace.get("input"),
                output=trace.get("output"),
                total_cost=trace.get("totalCost"),
                metadata=trace.get("metadata"),
                user_id=trace.get("userId"),
                session_id=trace.get("sessionId"),
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trace: {e}")
