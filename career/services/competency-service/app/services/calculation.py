"""
Competency score calculation logic.
"""
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class CompetencyCalculator:
    """
    Calculates competency scores based on multiple data sources.

    Formula:
    최종점수 = 진단점수_가중평균(최근2회)
             + 교과기여도(역량배점 × 성적)
             + 비교과보정(활동유형별 계수)
    """

    # Activity type coefficients for competency contribution
    ACTIVITY_COEFFICIENTS = {
        "인턴십": {"C001": 0.15, "C002": 0.25, "C003": 0.10, "C004": 0.15},
        "봉사활동": {"C003": 0.10, "C004": 0.20},
        "동아리": {"C003": 0.10, "C004": 0.15},
        "대외활동": {"C002": 0.10, "C003": 0.15, "C004": 0.20},
        "공모전": {"C001": 0.15, "C002": 0.20, "C003": 0.15},
        "자격증": {"C001": 0.20, "C002": 0.15},
        "어학": {"C003": 0.15, "C004": 0.10},
    }

    # Grade to point conversion
    GRADE_POINTS = {
        "A+": 4.5, "A0": 4.0, "A": 4.0,
        "B+": 3.5, "B0": 3.0, "B": 3.0,
        "C+": 2.5, "C0": 2.0, "C": 2.0,
        "D+": 1.5, "D0": 1.0, "D": 1.0,
        "F": 0.0,
    }

    def __init__(self):
        self.max_score = 100.0

    def calculate_assessment_weighted_average(
        self,
        assessments: List[Dict[str, float]],
        weights: Optional[List[float]] = None
    ) -> Dict[str, float]:
        """
        Calculate weighted average of recent assessments.

        Args:
            assessments: List of assessment score dictionaries
            weights: Optional weights (default: more recent = higher weight)

        Returns:
            Weighted average scores by competency
        """
        if not assessments:
            return {}

        # Default weights: more recent assessments have higher weight
        if weights is None:
            n = len(assessments)
            weights = [i / sum(range(1, n + 1)) for i in range(1, n + 1)]

        result: Dict[str, float] = {}
        total_weight = sum(weights[:len(assessments)])

        for competency_id in assessments[0].keys():
            weighted_sum = 0.0
            for i, assessment in enumerate(assessments):
                if competency_id in assessment:
                    weighted_sum += assessment[competency_id] * weights[i]
            result[competency_id] = weighted_sum / total_weight if total_weight > 0 else 0

        return result

    def calculate_course_contribution(
        self,
        courses: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate competency contribution from courses.

        Args:
            courses: List of course records with competency_mappings and grades

        Returns:
            Competency contribution scores
        """
        contribution: Dict[str, float] = {}

        for course in courses:
            grade = course.get("grade", "")
            grade_point = self.GRADE_POINTS.get(grade, 0.0)
            credits = float(course.get("credits", 0))
            mappings = course.get("competency_mappings", {})

            # Calculate contribution for each competency
            for comp_id, weight in mappings.items():
                if comp_id not in contribution:
                    contribution[comp_id] = 0.0

                # Contribution = weight × grade_point × credits / max_credits
                course_contribution = float(weight) * grade_point * credits / 4.5  # Normalized
                contribution[comp_id] += course_contribution

        return contribution

    def calculate_activity_contribution(
        self,
        activities: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate competency contribution from extracurricular activities.

        Args:
            activities: List of activities with type, hours, and competency_gains

        Returns:
            Competency contribution scores
        """
        contribution: Dict[str, float] = {}

        for activity in activities:
            activity_type = activity.get("activity_type", "")
            status = activity.get("status", "")
            hours = activity.get("hours_completed", 0)
            gains = activity.get("competency_gains", {})

            # Get coefficients for this activity type
            coefficients = self.ACTIVITY_COEFFICIENTS.get(activity_type, {})

            # Use explicit gains if provided, otherwise use coefficients
            effective_gains = gains if gains else coefficients

            # Calculate contribution
            completion_factor = 1.0 if status == "completed" else 0.5

            for comp_id, gain in effective_gains.items():
                if comp_id not in contribution:
                    contribution[comp_id] = 0.0

                # Contribution based on hours and completion status
                hours_factor = min(hours / 100, 1.0)  # Normalize by 100 hours
                activity_contribution = gain * hours_factor * completion_factor
                contribution[comp_id] += activity_contribution

        return contribution

    def calculate_total_scores(
        self,
        assessment_scores: Dict[str, float],
        course_contribution: Dict[str, float],
        activity_contribution: Dict[str, float],
        assessment_weight: float = 0.5,
        course_weight: float = 0.3,
        activity_weight: float = 0.2
    ) -> Dict[str, float]:
        """
        Calculate final competency scores.

        Args:
            assessment_scores: Weighted average of recent assessments
            course_contribution: Contribution from courses
            activity_contribution: Contribution from activities
            assessment_weight: Weight for assessment scores (default 0.5)
            course_weight: Weight for course contribution (default 0.3)
            activity_weight: Weight for activity contribution (default 0.2)

        Returns:
            Final competency scores (0-100 scale)
        """
        all_competencies = set(assessment_scores.keys()) | set(course_contribution.keys()) | set(activity_contribution.keys())

        final_scores: Dict[str, float] = {}

        for comp_id in all_competencies:
            assessment = assessment_scores.get(comp_id, 0)
            course = course_contribution.get(comp_id, 0) * 20  # Scale to 0-100
            activity = activity_contribution.get(comp_id, 0) * 100  # Scale to 0-100

            # Weighted sum
            score = (
                assessment * assessment_weight +
                course * course_weight +
                activity * activity_weight
            )

            # Clamp to 0-100
            final_scores[comp_id] = min(max(score, 0), self.max_score)

        return final_scores

    def calculate_percentiles(
        self,
        scores: Dict[str, float],
        all_student_scores: List[Dict[str, float]]
    ) -> Dict[str, int]:
        """
        Calculate percentile ranks based on all students' scores.

        Args:
            scores: Student's competency scores
            all_student_scores: All students' scores for comparison

        Returns:
            Percentile ranks by competency (0-100)
        """
        percentiles: Dict[str, int] = {}

        for comp_id, score in scores.items():
            # Count how many students have lower scores
            lower_count = sum(
                1 for s in all_student_scores
                if s.get(comp_id, 0) < score
            )
            total = len(all_student_scores)

            if total > 0:
                percentiles[comp_id] = int((lower_count / total) * 100)
            else:
                percentiles[comp_id] = 50  # Default to median

        return percentiles

    def get_status(self, score: float) -> str:
        """Get status label based on score."""
        if score >= 90:
            return "excellent"
        elif score >= 70:
            return "high"
        elif score >= 50:
            return "normal"
        else:
            return "low"
