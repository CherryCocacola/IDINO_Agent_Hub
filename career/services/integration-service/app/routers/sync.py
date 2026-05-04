"""
Data Synchronization API endpoints.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from ..connectors import WorknetConnector, UniversityConnector, HRDConnector
from ..schemas.integration import SyncRequest, SyncResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Create connector instances
worknet_connector = WorknetConnector()
university_connector = UniversityConnector()
hrd_connector = HRDConnector()


@router.post("/{source}", response_model=SyncResponse)
async def sync_data(
    source: str,
    request: Optional[SyncRequest] = None,
):
    """
    Synchronize data from external source.

    Supported sources:
    - worknet: Job information from Worknet
    - university: Academic data from university system
    - hrd: Employment data from HRD-Net

    In mock mode, this simulates a successful sync.
    """
    valid_sources = ["worknet", "university", "hrd"]

    if source not in valid_sources:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid source. Must be one of: {valid_sources}"
        )

    records_synced = 0
    records_failed = 0
    errors = []

    try:
        if source == "worknet":
            # Sync job data
            jobs = await worknet_connector.get_all_jobs()
            records_synced = len(jobs)
            logger.info(f"Synced {records_synced} jobs from Worknet")

        elif source == "university":
            # Sync student data
            if request and request.target_ids:
                for student_id in request.target_ids:
                    success = await university_connector.sync_student_data(student_id)
                    if success:
                        records_synced += 1
                    else:
                        records_failed += 1
                        errors.append(f"Failed to sync student {student_id}")
            else:
                # Full sync not implemented for mock mode
                records_synced = 2  # Mock count
                logger.info("Mock full sync for university data")

        elif source == "hrd":
            # Sync alumni data
            alumni = await hrd_connector.get_alumni(limit=100)
            records_synced = len(alumni)
            logger.info(f"Synced {records_synced} alumni records from HRD-Net")

        status_str = "success" if records_failed == 0 else "partial"

    except Exception as e:
        logger.error(f"Sync failed for {source}: {e}")
        status_str = "failed"
        errors.append(str(e))

    return SyncResponse(
        source=source,
        status=status_str,
        records_synced=records_synced,
        records_failed=records_failed,
        errors=errors,
        sync_timestamp=datetime.utcnow(),
    )


@router.get("/status")
async def get_sync_status():
    """
    Get synchronization status for all sources.

    Returns last sync time and record counts for each source.
    """
    # In production, this would query a sync history table
    return {
        "sources": {
            "worknet": {
                "last_sync": None,
                "record_count": 5,
                "status": "mock"
            },
            "university": {
                "last_sync": None,
                "record_count": 2,
                "status": "mock"
            },
            "hrd": {
                "last_sync": None,
                "record_count": 5,
                "status": "mock"
            }
        },
        "mode": "mock"
    }
