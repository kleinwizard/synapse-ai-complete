"""
LLM Router Module

This module provides sophisticated routing logic for selecting optimal Large Language Models
based on user-selected Power Level (Low, Med, High, Pro) and Task Type (code, writing, research).
The system intelligently maps requests to the most appropriate model within each tier.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

MODEL_CATALOG: Dict[str, Dict[str, str]] = {
    "low": {
        "code": "claude-3-haiku-20240307",
        "writing": "gpt-4o-mini",
        "research": "gpt-4o-mini",
        "default": "gpt-4o-mini",
    },
    "med": {
        "code": "claude-3-5-sonnet-20240620",
        "writing": "gpt-4o",
        "research": "claude-3-5-sonnet-20240620",
        "default": "claude-3-5-sonnet-20240620",
    },
    "high": {
        "code": "claude-3-5-sonnet-20241022",
        "writing": "gpt-4o",
        "research": "claude-3-5-sonnet-20241022",
        "default": "claude-3-5-sonnet-20241022",
    },
    "pro": {
        "code": "claude-3-5-sonnet-20241022",
        "writing": "gpt-4o",
        "research": "claude-3-5-sonnet-20241022",
        "default": "gpt-4o",
    },
}

VALID_POWER_LEVELS = {"low", "med", "high", "pro"}

VALID_TASK_TYPES = {"code", "writing", "research"}


def select_model(power_level: str, task_type: str) -> str:
    """
    Select the optimal Large Language Model based on power level and task type.
    
    This function implements the core decision-making logic for the Synapse AI application,
    providing intelligent model selection within tiered power levels.
    
    Args:
        power_level (str): The user-selected power tier. Must be one of:
                          'low', 'med', 'high', or 'pro'
        task_type (str): The specific task type for optimization. Common values:
                        'code', 'writing', 'research', or any custom task type
    
    Returns:
        str: The exact string identifier for the chosen model
             (e.g., "claude-3-5-sonnet-20240620")
    
    Raises:
        None: Function handles all errors gracefully with fallbacks and logging
    
    Examples:
        >>> select_model("high", "code")
        "claude-3-opus-20240229"
        
        >>> select_model("med", "writing")
        "gpt-4o-2024-05-13"
        
        >>> select_model("invalid", "code")  # Falls back to 'low'
        "claude-3-haiku-20240307"
        
        >>> select_model("pro", "unknown_task")  # Falls back to default
        "gpt-4o-2024-05-13"
    """
    
    if power_level not in VALID_POWER_LEVELS:
        logger.warning(
            f"Invalid power_level '{power_level}' provided. "
            f"Valid options are: {', '.join(VALID_POWER_LEVELS)}. "
            f"Defaulting to 'low'."
        )
        power_level = "low"
    
    power_level = power_level.lower()
    task_type = task_type.lower() if task_type else "default"
    
    tier_models = MODEL_CATALOG[power_level]
    
    if task_type in tier_models:
        selected_model = tier_models[task_type]
        logger.info(
            f"Selected model '{selected_model}' for power_level='{power_level}', "
            f"task_type='{task_type}'"
        )
    else:
        selected_model = tier_models["default"]
        logger.info(
            f"Task type '{task_type}' not found in '{power_level}' tier. "
            f"Using default model '{selected_model}'"
        )
    
    return selected_model


def get_available_models(power_level: str) -> Dict[str, str]:
    """
    Get all available models for a specific power level.
    
    Args:
        power_level (str): The power tier to query
        
    Returns:
        Dict[str, str]: Dictionary mapping task types to model identifiers
                       for the specified power level
    
    Examples:
        >>> get_available_models("med")
        {
            "code": "claude-3-5-sonnet-20240620",
            "writing": "gpt-4o-2024-05-13",
            "research": "gemini-1.5-pro-preview-0514",
            "default": "claude-3-5-sonnet-20240620"
        }
    """
    if power_level not in VALID_POWER_LEVELS:
        logger.warning(f"Invalid power_level '{power_level}'. Returning empty dict.")
        return {}
    
    return MODEL_CATALOG[power_level].copy()


def get_model_info() -> Dict[str, Any]:
    """
    Get comprehensive information about the model catalog structure.
    
    Returns:
        Dict[str, Any]: Information about available power levels, task types,
                       and total model count
    """
    total_models = sum(len(tier) for tier in MODEL_CATALOG.values())
    
    return {
        "power_levels": list(VALID_POWER_LEVELS),
        "task_types": list(VALID_TASK_TYPES),
        "total_models": total_models,
        "catalog_structure": {
            level: list(models.keys()) 
            for level, models in MODEL_CATALOG.items()
        }
    }


def validate_routing_request(power_level: str, task_type: str) -> Dict[str, Any]:
    """
    Validate a routing request and provide detailed feedback.
    
    Args:
        power_level (str): The power level to validate
        task_type (str): The task type to validate
        
    Returns:
        Dict[str, Any]: Validation results with status and recommendations
    """
    validation_result = {
        "is_valid": True,
        "warnings": [],
        "recommendations": [],
        "normalized_power_level": power_level.lower() if power_level else "low",
        "normalized_task_type": task_type.lower() if task_type else "default"
    }
    
    if power_level not in VALID_POWER_LEVELS:
        validation_result["is_valid"] = False
        validation_result["warnings"].append(
            f"Invalid power_level '{power_level}'. Will default to 'low'."
        )
        validation_result["normalized_power_level"] = "low"
    
    if task_type and task_type.lower() not in VALID_TASK_TYPES:
        validation_result["recommendations"].append(
            f"Task type '{task_type}' will use default model for the selected tier. "
            f"Consider using: {', '.join(VALID_TASK_TYPES)}"
        )
    
    return validation_result
