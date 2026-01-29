from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime


class AgentInput(BaseModel):
    """Base input model for all agents"""
    data: Any
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.now()


class AgentOutput(BaseModel):
    """Base output model for all agents"""
    data: Any
    status: str = "success"
    errors: List[str] = []
    metadata: Dict[str, Any] = {}
    processing_time: Optional[float] = None
    output_preview: Optional[str] = None


class PipelineState(BaseModel):
    """Tracks the state across the sequential pipeline"""
    current_step: int = 0
    total_steps: int = 4
    history: List[Dict[str, Any]] = []
    final_output: Optional[Any] = None
