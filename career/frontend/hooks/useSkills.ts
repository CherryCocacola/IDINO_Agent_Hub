'use client';

import { useState, useEffect, useCallback } from 'react';
import { skillService } from '@/lib/api/skill';
import type {
  StudentSkillResponse,
  SkillGraphResponse,
  GapAnalysisResponse,
  RoleRequirementResponse,
} from '@/types';

interface SkillsState {
  skills: StudentSkillResponse[];
  graph: SkillGraphResponse | null;
  gapAnalysis: GapAnalysisResponse | null;
  roleRequirements: RoleRequirementResponse | null;
  roles: Array<{ role_cd: string; role_nm: string; industry?: string }>;
  loading: boolean;
  error: string | null;
}

const initialState: SkillsState = {
  skills: [],
  graph: null,
  gapAnalysis: null,
  roleRequirements: null,
  roles: [],
  loading: true,
  error: null,
};

export function useSkills(studentId: string | null, selectedRoleCd?: string) {
  const [state, setState] = useState<SkillsState>(initialState);

  // Fetch student skills
  const fetchSkills = useCallback(async () => {
    if (!studentId) {
      setState(prev => ({ ...prev, loading: false }));
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const [skills, roles] = await Promise.all([
        skillService.getStudentSkills(studentId),
        skillService.getRoles(),
      ]);

      setState(prev => ({
        ...prev,
        skills,
        roles,
        loading: false,
      }));
    } catch (error) {
      console.error('Skills fetch error:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: '스킬 데이터를 불러오는데 실패했습니다.',
      }));
    }
  }, [studentId]);

  // Fetch skill graph
  const fetchGraph = useCallback(async (roleCd?: string) => {
    if (!studentId) return;

    try {
      const graph = await skillService.getStudentSkillGraph(studentId, roleCd);
      setState(prev => ({ ...prev, graph }));
    } catch (error) {
      console.error('Graph fetch error:', error);
    }
  }, [studentId]);

  // Fetch gap analysis
  const fetchGapAnalysis = useCallback(async (roleCd: string) => {
    if (!studentId) return;

    try {
      const gapAnalysis = await skillService.getGapAnalysis(studentId, roleCd);
      setState(prev => ({ ...prev, gapAnalysis }));
    } catch (error) {
      console.error('Gap analysis fetch error:', error);
    }
  }, [studentId]);

  // Fetch role requirements
  const fetchRoleRequirements = useCallback(async (roleCd: string) => {
    try {
      const roleRequirements = await skillService.getRoleRequirements(roleCd);
      setState(prev => ({ ...prev, roleRequirements }));
    } catch (error) {
      console.error('Role requirements fetch error:', error);
    }
  }, []);

  // Update skill level
  const updateSkillLevel = useCallback(async (skillCd: string, currentLevel: number, targetLevel?: number) => {
    if (!studentId) return;

    try {
      const updated = await skillService.updateStudentSkill(studentId, skillCd, {
        current_level: currentLevel,
        target_level: targetLevel,
      });
      setState(prev => ({
        ...prev,
        skills: prev.skills.map(s => s.skill_cd === skillCd ? updated : s),
      }));
    } catch (error) {
      console.error('Update skill error:', error);
      throw error;
    }
  }, [studentId]);

  // Initial fetch
  useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  // Fetch graph and gap when role changes
  useEffect(() => {
    if (selectedRoleCd) {
      fetchGraph(selectedRoleCd);
      fetchGapAnalysis(selectedRoleCd);
      fetchRoleRequirements(selectedRoleCd);
    }
  }, [selectedRoleCd, fetchGraph, fetchGapAnalysis, fetchRoleRequirements]);

  return {
    ...state,
    refetch: fetchSkills,
    fetchGraph,
    fetchGapAnalysis,
    fetchRoleRequirements,
    updateSkillLevel,
  };
}
