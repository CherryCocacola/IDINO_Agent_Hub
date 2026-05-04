"""
Worknet API Connector.

Handles connection to 워크넷 (Korea Employment Information Service) API.
Uses mock data when USE_MOCK_DATA is enabled.
"""
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

import httpx

from ..config import settings
from ..schemas.integration import WorknetJobResponse

logger = logging.getLogger(__name__)


class WorknetConnector:
    """Connector for Worknet API."""

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.api_url = settings.WORKNET_API_URL
        self.api_key = settings.WORKNET_API_KEY
        self.use_mock = settings.USE_MOCK_DATA
        self._mock_data: Optional[Dict[str, Any]] = None

    def _load_mock_data(self) -> Dict[str, Any]:
        """Load mock data from JSON file."""
        if self._mock_data is None:
            mock_path = Path(__file__).parent.parent / "mock" / "worknet_mock.json"
            with open(mock_path, "r", encoding="utf-8") as f:
                self._mock_data = json.load(f)
        return self._mock_data

    async def get_job(self, job_code: str) -> Optional[WorknetJobResponse]:
        """Get job information by code."""

        # Check cache first
        if self.redis:
            cached = await self.redis.get(f"worknet_job:{job_code}")
            if cached:
                return WorknetJobResponse.model_validate_json(cached)

        if self.use_mock:
            # Use mock data
            data = self._load_mock_data()
            for job in data.get("jobs", []):
                if job["job_code"] == job_code:
                    result = WorknetJobResponse(**job)

                    # Cache the result
                    if self.redis:
                        await self.redis.set(
                            f"worknet_job:{job_code}",
                            result.model_dump_json(),
                            ex=settings.CACHE_TTL_SECONDS
                        )

                    return result
            return None

        # Real API call (for future integration)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.api_url}/jobs/{job_code}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                if response.status_code == 200:
                    result = WorknetJobResponse(**response.json())

                    if self.redis:
                        await self.redis.set(
                            f"worknet_job:{job_code}",
                            result.model_dump_json(),
                            ex=settings.CACHE_TTL_SECONDS
                        )

                    return result
        except Exception as e:
            logger.error(f"Failed to fetch job from Worknet: {e}")

        return None

    async def search_jobs(
        self,
        query: str,
        category: Optional[str] = None,
        education_level: Optional[str] = None,
        limit: int = 10,
    ) -> List[WorknetJobResponse]:
        """Search for jobs."""

        if self.use_mock:
            data = self._load_mock_data()
            results = []

            for job in data.get("jobs", []):
                # Simple text matching
                if query.lower() in job["job_name"].lower() or \
                   query.lower() in job.get("description", "").lower():

                    if category and job.get("category") != category:
                        continue

                    results.append(WorknetJobResponse(**job))

                    if len(results) >= limit:
                        break

            return results

        # Real API call (for future integration)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {
                    "query": query,
                    "limit": limit
                }
                if category:
                    params["category"] = category
                if education_level:
                    params["education_level"] = education_level

                response = await client.get(
                    f"{self.api_url}/jobs/search",
                    params=params,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                if response.status_code == 200:
                    return [WorknetJobResponse(**job) for job in response.json().get("results", [])]
        except Exception as e:
            logger.error(f"Failed to search jobs in Worknet: {e}")

        return []

    async def get_all_jobs(self) -> List[WorknetJobResponse]:
        """Get all available jobs (for mock mode)."""
        if self.use_mock:
            data = self._load_mock_data()
            return [WorknetJobResponse(**job) for job in data.get("jobs", [])]
        return []

    async def get_jobs_by_category(self, category: str) -> List[WorknetJobResponse]:
        """Get jobs filtered by category."""
        if self.use_mock:
            data = self._load_mock_data()
            results = []
            for job in data.get("jobs", []):
                if job.get("category") == category:
                    results.append(WorknetJobResponse(**job))
            return results
        return []

    async def get_jobs_by_department(self, department_nm: str) -> List[WorknetJobResponse]:
        """Get jobs relevant to a department based on category mapping."""
        # Department to category mapping
        category_mapping = {
            # Medical/Health
            "의": "의료/보건",
            "간호": "의료/보건",
            "약": "의료/보건",
            "보건": "의료/보건",
            "치": "의료/보건",
            "임상": "의료/보건",
            # IT
            "컴퓨터": "IT/정보통신",
            "소프트웨어": "IT/정보통신",
            "정보": "IT/정보통신",
            "AI": "IT/정보통신",
            "데이터": "IT/정보통신",
            # Engineering
            "전자": "공학",
            "전기": "공학",
            "기계": "공학",
            "건축": "공학",
            "토목": "공학",
            "화공": "공학",
            "산업": "공학",
            # Education
            "교육": "교육",
            "사범": "교육",
            # Design/Arts
            "디자인": "디자인",
            "미술": "디자인",
            "예술": "디자인",
            "음악": "예술/문화",
            "영상": "디자인",
            # Business
            "경영": "기획/경영",
            "경제": "기획/경영",
            "회계": "기획/경영",
            "금융": "기획/경영",
            "무역": "기획/경영",
            "마케팅": "마케팅/광고",
            # Social
            "행정": "공공/행정",
            "사회복지": "사회복지",
            "심리": "사회복지",
            "법": "법률",
        }

        # Find matching category
        matched_category = None
        for keyword, category in category_mapping.items():
            if keyword in department_nm:
                matched_category = category
                break

        if not matched_category:
            matched_category = "기획/경영"  # Default fallback

        return await self.get_jobs_by_category(matched_category)
