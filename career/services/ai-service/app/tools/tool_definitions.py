"""
OpenAI Tool Definitions for Career Recommendation System
Based on TechSpec Phase 2-1: Tool Calling Integration
Phase 2-2: Structured Outputs (JSON Schema)
"""

# =============================================================================
# Phase 2-2: JSON Schema for Structured Outputs
# =============================================================================

JSON_SCHEMA_ACTIONBOARD = {
    "name": "action_recommendations",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "전반적인 분석 요약 (2-3문장)"
            },
            "strengths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "학생의 강점 목록"
            },
            "improvements": {
                "type": "array",
                "items": {"type": "string"},
                "description": "개선이 필요한 영역"
            },
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "priority": {
                            "type": "string",
                            "enum": ["high", "medium", "low"]
                        },
                        "competency": {"type": "string"},
                        "deadline": {"type": "string"},
                        "icon_type": {
                            "type": "string",
                            "enum": ["book", "users", "award", "briefcase", "code", "chart"]
                        },
                        "reasoning": {"type": "string"}
                    },
                    "required": ["id", "title", "description", "priority"],
                    "additionalProperties": False
                },
                "description": "추천 액션 목록 (최대 5개)"
            },
            "alumni_insights": {
                "type": "array",
                "items": {"type": "string"},
                "description": "관련 동문 패턴에서 얻은 인사이트"
            }
        },
        "required": ["summary", "strengths", "improvements", "recommendations"],
        "additionalProperties": False
    }
}


# =============================================================================
# Phase 2-1: Tool Definitions for Function Calling
# =============================================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_student_profile",
            "description": "Retrieve student's basic information including name, department, grade, GPA, career goals, and academic status. Use this when you need to understand the student's background.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "The unique identifier for the student (e.g., 'STU001')"
                    }
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_competency_scores",
            "description": "Retrieve the student's competency scores across various dimensions such as major knowledge, practical skills, problem solving, communication, and leadership. Use this to understand the student's strengths and areas for improvement.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "The unique identifier for the student"
                    }
                },
                "required": ["student_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_alumni_patterns",
            "description": "Search for successful alumni career patterns based on target role and optionally department. Use this to find relevant career path examples and strategies from alumni who achieved similar goals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_role": {
                        "type": "string",
                        "description": "The target job role to search for (e.g., 'Data Scientist', 'Software Engineer')"
                    },
                    "department_id": {
                        "type": "string",
                        "description": "Optional department ID to filter alumni from the same department"
                    }
                },
                "required": ["target_role"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_constraints",
            "description": "Check academic constraints and prerequisites for specific courses. Verifies if the student can enroll in the specified courses based on prerequisites and credit limits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "The unique identifier for the student"
                    },
                    "course_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of course IDs to check constraints for"
                    }
                },
                "required": ["student_id", "course_ids"]
            }
        }
    }
]

# System prompt for Tool Calling conversations
SYSTEM_PROMPT = """You are an AI career advisor for university students. Your role is to:
1. Analyze the student's academic profile and competencies
2. Identify strengths and areas for improvement
3. Recommend actionable steps for career development
4. Learn from successful alumni patterns

When providing recommendations, use the available tools to gather accurate, up-to-date information about the student.
Always base your advice on actual data rather than assumptions.

Response format should be structured JSON with:
- summary: Brief overview of the student's situation
- strengths: List of identified strengths
- improvements: List of areas needing improvement
- recommendations: List of specific, actionable recommendations
- alumni_insights: Relevant patterns from successful alumni (if applicable)
"""
