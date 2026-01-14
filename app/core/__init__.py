"""Core module for ingestion, normalization, validation, mapping, and metrics"""

from app.core.gl_ingestion import GLIngestionEngine, ProcessingReport
from app.core.validation import GLValidator, ValidationResult, ValidationStatus
from app.core.gl_pipeline import GLPipeline
from app.core.mapping import (
    GLAccountMapper,
    MultiEntityProcessor,
    AccountMapping,
    DEFAULT_CATEGORIES,
)
from app.core.adjustments import (
    AdjustmentRulesEngine,
    AdjustmentRule,
)

__all__ = [
    "GLIngestionEngine",
    "ProcessingReport",
    "GLValidator",
    "ValidationResult",
    "ValidationStatus",
    "GLPipeline",
    "GLAccountMapper",
    "MultiEntityProcessor",
    "AccountMapping",
    "DEFAULT_CATEGORIES",
    "AdjustmentRulesEngine",
    "AdjustmentRule",
]
