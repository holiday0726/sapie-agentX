"""Natural Language to Flow API endpoint."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from langflow.api.v1.schemas import NLToFlowRequest, NLToFlowResponse
from langflow.interface.components import get_and_cache_all_types_dict
from langflow.services.auth.utils import get_current_active_user
from langflow.services.database.models.user import User
from langflow.services.deps import get_settings_service
from langflow.services.nl_flow.service import NLFlowService
from loguru import logger

router = APIRouter(prefix="/nl-flow", tags=["NL Flow"])


@router.post("/generate", response_model=NLToFlowResponse)
async def generate_flow_from_nl(
    request: NLToFlowRequest,
    current_user: User = Depends(get_current_active_user),
) -> NLToFlowResponse:
    """
    Generate a Langflow flow from natural language description.

    Args:
        request: Natural language flow description
        current_user: Current authenticated user

    Returns:
        NLToFlowResponse with generated nodes and edges
    """
    try:
        logger.info(f"Generating flow from NL: {request.prompt[:100]}...")

        # Get all available components
        settings_service = get_settings_service()
        all_types = await get_and_cache_all_types_dict(settings_service=settings_service)

        # Initialize NL Flow service
        nl_service = NLFlowService()

        # Generate flow using LLM
        flow_data = await nl_service.generate_flow(
            prompt=request.prompt, available_components=all_types
        )

        logger.info(f"Successfully generated flow with {len(flow_data['nodes'])} nodes")

        return NLToFlowResponse(**flow_data)

    except ValueError as e:
        logger.error(f"Validation error in NL to Flow: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error generating flow from NL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate flow") from e
