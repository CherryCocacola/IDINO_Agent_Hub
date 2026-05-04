"""Pydantic v2 schemas for the admin dashboard module."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Dashboard overview
# ---------------------------------------------------------------------------


class DashboardMetrics(BaseModel):
    """High-level summary metrics displayed on the admin dashboard."""

    total_users: int = Field(..., description="Total registered users in the organisation.")
    active_users: int = Field(..., description="Users with status 'active'.")
    total_documents: int = Field(..., description="Total documents uploaded.")
    total_searches: int = Field(..., description="Total search requests recorded.")
    feature_usage: dict = Field(
        default_factory=dict,
        description="Arbitrary feature-usage counters (e.g. chat, QA, keyword).",
    )


# ---------------------------------------------------------------------------
# Search usage
# ---------------------------------------------------------------------------


class SearchUsageStats(BaseModel):
    """Aggregated search-request statistics for a given period."""

    total_requests: int = Field(..., description="Number of search requests.")
    total_responses: int = Field(..., description="Number of successful responses.")
    total_failures: int = Field(..., description="Number of failed requests.")
    period: str = Field(
        ..., description="Human-readable period label (e.g. '7d', '30d')."
    )


# ---------------------------------------------------------------------------
# Upload status chart
# ---------------------------------------------------------------------------


class UploadStatusChart(BaseModel):
    """Document counts broken down by processing status."""

    completed: int = Field(0, description="Documents fully processed.")
    processing: int = Field(0, description="Documents currently being processed.")
    waiting: int = Field(0, description="Documents waiting in queue.")
    error: int = Field(0, description="Documents that failed processing.")


# ---------------------------------------------------------------------------
# Response-time data (time series)
# ---------------------------------------------------------------------------


class ResponseTimeData(BaseModel):
    """Hourly average response times for plotting."""

    timestamps: list[str] = Field(
        default_factory=list,
        description="ISO-formatted hour timestamps.",
    )
    values: list[float] = Field(
        default_factory=list,
        description="Average response time in milliseconds per hour.",
    )


# ---------------------------------------------------------------------------
# Search-error data (time series)
# ---------------------------------------------------------------------------


class SearchErrorData(BaseModel):
    """Daily error counts for search requests."""

    dates: list[str] = Field(
        default_factory=list,
        description="ISO-formatted date strings.",
    )
    error_counts: list[int] = Field(
        default_factory=list,
        description="Number of search errors per date.",
    )


# ---------------------------------------------------------------------------
# System settings
# ---------------------------------------------------------------------------


class SystemSettings(BaseModel):
    """Editable system-wide settings for the organisation."""

    default_language: str = Field(
        default="en", description="Default UI / content language."
    )
    max_upload_size_mb: int = Field(
        default=100, description="Maximum single-file upload size in MB."
    )
    allowed_formats: list[str] = Field(
        default_factory=list,
        description="MIME types or extensions permitted for upload.",
    )
    maintenance_mode: bool = Field(
        default=False, description="Whether the system is in maintenance mode."
    )
