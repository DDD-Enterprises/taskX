"""Spec feedback loop module."""

from taskx.pipeline.spec_feedback.feedback import generate_feedback
from taskx.pipeline.spec_feedback.types import Evidence, Patch

__all__ = ["generate_feedback", "Evidence", "Patch"]
