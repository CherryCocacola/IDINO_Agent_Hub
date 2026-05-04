from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from uuid import UUID

from ..schemas import (
    RiskSeverity,
    RiskCategory,
    AlertStatus,
    RiskAlertCreate,
    RiskAlertUpdate,
    RiskAlertResponse,
    ConstraintCheckResponse,
    PrerequisiteRuleResponse,
    StudentRiskProfile,
    RiskAnalysisRequest,
    RiskAnalysisResponse,
)
from ..services import risk_service

router = APIRouter(prefix="/risks", tags=["Risk Alerts"])


# ============================================
# Risk Analysis
# ============================================

@router.post("/analyze", response_model=RiskAnalysisResponse)
async def analyze_student_risks(request: RiskAnalysisRequest):
    """
    학생 위험 분석 실행

    모든 위험 카테고리를 분석하고 알림을 생성합니다.

    - **categories**: 분석할 카테고리 (미지정시 전체)
    - **include_recommendations**: 권장사항 포함 여부
    """
    try:
        return await risk_service.run_full_analysis(
            student_id=request.student_id,
            categories=request.categories,
            create_alerts=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/analyze/{student_id}", response_model=RiskAnalysisResponse)
async def analyze_student_risks_get(
    student_id: str,
    category: Optional[RiskCategory] = Query(None, description="분석할 카테고리"),
):
    """학생 위험 분석 (GET 버전)"""
    categories = [category] if category else None
    try:
        return await risk_service.run_full_analysis(
            student_id=student_id,
            categories=categories,
            create_alerts=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/profile/{student_id}", response_model=StudentRiskProfile)
async def get_risk_profile(student_id: str):
    """
    학생 위험 프로필 조회

    전체 위험 점수와 활성 알림을 포함합니다.
    """
    try:
        result = await risk_service.run_full_analysis(
            student_id=student_id,
            create_alerts=False,
        )
        return result.profile
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================
# Risk Alerts
# ============================================

@router.get("/alerts/{student_id}", response_model=List[RiskAlertResponse])
async def get_student_alerts(
    student_id: str,
    status: Optional[AlertStatus] = Query(None, description="알림 상태"),
    category: Optional[RiskCategory] = Query(None, description="위험 카테고리"),
    severity: Optional[RiskSeverity] = Query(None, description="심각도"),
):
    """학생의 위험 알림 목록"""
    alerts = await risk_service.get_student_alerts(
        student_id=student_id,
        status=status,
        category=category,
        severity=severity,
    )
    return [RiskAlertResponse(**a) for a in alerts]


@router.get("/alerts/detail/{alert_id}", response_model=RiskAlertResponse)
async def get_alert(alert_id: UUID):
    """알림 상세 조회"""
    alert = await risk_service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return RiskAlertResponse(**alert)


@router.post("/alerts", response_model=RiskAlertResponse, status_code=201)
async def create_alert(data: RiskAlertCreate):
    """수동 위험 알림 생성"""
    result = await risk_service.create_alert(data)
    return RiskAlertResponse(**result)


@router.put("/alerts/{alert_id}", response_model=RiskAlertResponse)
async def update_alert(alert_id: UUID, data: RiskAlertUpdate):
    """알림 상태 업데이트"""
    result = await risk_service.update_alert(alert_id, data)
    if not result:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return RiskAlertResponse(**result)


@router.post("/alerts/{alert_id}/acknowledge", response_model=RiskAlertResponse)
async def acknowledge_alert(alert_id: UUID):
    """알림 확인 처리"""
    result = await risk_service.update_alert(
        alert_id,
        RiskAlertUpdate(status=AlertStatus.ACKNOWLEDGED),
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return RiskAlertResponse(**result)


@router.post("/alerts/{alert_id}/resolve", response_model=RiskAlertResponse)
async def resolve_alert(
    alert_id: UUID,
    resolution_note: Optional[str] = Query(None, description="해결 노트"),
):
    """알림 해결 처리"""
    result = await risk_service.update_alert(
        alert_id,
        RiskAlertUpdate(status=AlertStatus.RESOLVED, resolution_note=resolution_note),
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return RiskAlertResponse(**result)


# ============================================
# Constraint Checks
# ============================================

@router.get("/constraints/{student_id}", response_model=List[ConstraintCheckResponse])
async def get_constraint_checks(student_id: str):
    """학생의 제약조건 체크 결과"""
    checks = await risk_service.get_constraint_checks(student_id)
    return [ConstraintCheckResponse(**c) for c in checks]


# ============================================
# Risk Summary (Dashboard)
# ============================================

@router.get("/summary/{student_id}")
async def get_risk_summary(student_id: str):
    """
    대시보드용 위험 요약 조회

    - **risk_level**: 위험 수준 (low, medium, high, critical)
    - **score**: 종합 위험 점수 (0-100)
    - **active_alerts**: 활성 알림 수
    - **critical_alerts**: 긴급 알림 수
    - **top_risks**: 주요 위험 요인
    """
    try:
        alerts = await risk_service.get_student_alerts(student_id=student_id)
        active_alerts = [a for a in alerts if a.get("status") in ["new", "acknowledged"]]
        critical_alerts = [a for a in active_alerts if a.get("severity") == "critical"]

        # Calculate risk score based on alerts
        score = min(100, len(active_alerts) * 15 + len(critical_alerts) * 25)

        # Determine risk level
        if score >= 75:
            risk_level = "critical"
        elif score >= 50:
            risk_level = "high"
        elif score >= 25:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Get top risks from alerts
        top_risks = list(set([a.get("category", "unknown") for a in active_alerts[:5]]))

        return {
            "risk_level": risk_level,
            "score": score,
            "active_alerts": len(active_alerts),
            "critical_alerts": len(critical_alerts),
            "top_risks": top_risks,
        }
    except Exception:
        # Return safe default if analysis fails
        return {
            "risk_level": "low",
            "score": 0,
            "active_alerts": 0,
            "critical_alerts": 0,
            "top_risks": [],
        }


# ============================================
# Prerequisite Rules
# ============================================

@router.get("/prerequisites", response_model=List[PrerequisiteRuleResponse])
async def get_prerequisite_rules(
    course_cd: Optional[str] = Query(None, description="과목 코드"),
):
    """선수과목 규칙 조회"""
    rules = await risk_service.get_prerequisite_rules(course_cd)
    return [PrerequisiteRuleResponse(**r) for r in rules]
