'use client';

import { useState, useEffect, useCallback } from 'react';
import { portfolioService } from '@/lib/api/portfolio';
import type {
  PortfolioResponse,
  PortfolioListResponse,
  PortfolioCreate,
  PortfolioUpdate,
  ArtifactType,
  PortfolioSummaryResponse,
} from '@/types';
import {
  ARTIFACT_TYPE_LABELS,
  ARTIFACT_TYPE_ICONS,
  ARTIFACT_TYPE_COLORS,
} from '@/types/portfolio';

interface PortfolioBuilderSectionProps {
  studentId: string;
}

export default function PortfolioBuilderSection({ studentId }: PortfolioBuilderSectionProps) {
  const [portfolioData, setPortfolioData] = useState<PortfolioListResponse | null>(null);
  const [summary, setSummary] = useState<PortfolioSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingItem, setEditingItem] = useState<PortfolioResponse | null>(null);
  const [selectedType, setSelectedType] = useState<ArtifactType | 'all'>('all');

  // Form state
  const [formData, setFormData] = useState<Partial<PortfolioCreate>>({
    student_id: studentId,
    artifact_type: 'github',
    title: '',
    url: '',
    description: '',
    is_primary: false,
    tags: [],
    skills: [],
  });
  const [tagInput, setTagInput] = useState('');
  const [skillInput, setSkillInput] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [portfolioResult, summaryResult] = await Promise.all([
        portfolioService.getStudentPortfolio(studentId),
        portfolioService.getPortfolioSummary(studentId),
      ]);
      setPortfolioData(portfolioResult);
      setSummary(summaryResult);
    } catch (error) {
      console.error('Failed to fetch portfolio data:', error);
    } finally {
      setLoading(false);
    }
  }, [studentId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const resetForm = () => {
    setFormData({
      student_id: studentId,
      artifact_type: 'github',
      title: '',
      url: '',
      description: '',
      is_primary: false,
      tags: [],
      skills: [],
    });
    setTagInput('');
    setSkillInput('');
  };

  const handleCreate = async () => {
    if (!formData.title || !formData.url || !formData.artifact_type) return;

    try {
      await portfolioService.createPortfolioItem(formData as PortfolioCreate);
      await fetchData();
      setShowCreateModal(false);
      resetForm();
    } catch (error) {
      console.error('Failed to create portfolio item:', error);
    }
  };

  const handleUpdate = async () => {
    if (!editingItem || !formData.title) return;

    try {
      const updateData: PortfolioUpdate = {
        artifact_type: formData.artifact_type,
        title: formData.title,
        url: formData.url,
        description: formData.description,
        is_primary: formData.is_primary,
        tags: formData.tags,
        skills: formData.skills,
      };
      await portfolioService.updatePortfolioItem(editingItem.portfolio_id, updateData);
      await fetchData();
      setEditingItem(null);
      setShowCreateModal(false);
      resetForm();
    } catch (error) {
      console.error('Failed to update portfolio item:', error);
    }
  };

  const handleDelete = async (portfolioId: string) => {
    if (!confirm('이 항목을 삭제하시겠습니까?')) return;

    try {
      await portfolioService.deletePortfolioItem(portfolioId);
      await fetchData();
    } catch (error) {
      console.error('Failed to delete portfolio item:', error);
    }
  };

  const handleSetPrimary = async (portfolioId: string) => {
    try {
      await portfolioService.setPrimaryItem(portfolioId);
      await fetchData();
    } catch (error) {
      console.error('Failed to set primary item:', error);
    }
  };

  const openEditModal = (item: PortfolioResponse) => {
    setEditingItem(item);
    setFormData({
      student_id: studentId,
      artifact_type: item.artifact_type,
      title: item.title,
      url: item.url,
      description: item.description || '',
      is_primary: item.is_primary,
      tags: item.tags || [],
      skills: item.skills || [],
    });
    setShowCreateModal(true);
  };

  const addTag = () => {
    if (tagInput.trim() && !formData.tags?.includes(tagInput.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...(prev.tags || []), tagInput.trim()],
      }));
      setTagInput('');
    }
  };

  const removeTag = (index: number) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags?.filter((_, i) => i !== index),
    }));
  };

  const addSkill = () => {
    if (skillInput.trim() && !formData.skills?.includes(skillInput.trim())) {
      setFormData(prev => ({
        ...prev,
        skills: [...(prev.skills || []), skillInput.trim()],
      }));
      setSkillInput('');
    }
  };

  const removeSkill = (index: number) => {
    setFormData(prev => ({
      ...prev,
      skills: prev.skills?.filter((_, i) => i !== index),
    }));
  };

  const filteredItems = portfolioData?.items.filter(
    item => selectedType === 'all' || item.artifact_type === selectedType
  ) || [];

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-12 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-48 bg-gray-200 rounded"></div>
            <div className="h-48 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow-sm p-4 text-center">
            <div className="text-3xl font-bold text-indigo-600">{summary.total_items}</div>
            <div className="text-sm text-gray-500">총 아이템</div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-4 text-center">
            <div className="text-3xl font-bold text-green-600">
              {summary.has_primary ? '1' : '0'}
            </div>
            <div className="text-sm text-gray-500">대표 포트폴리오</div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-4 text-center">
            <div className="text-3xl font-bold text-purple-600">
              {Object.keys(summary.by_type).length}
            </div>
            <div className="text-sm text-gray-500">활성 유형</div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-4 text-center">
            <div className="text-3xl font-bold text-orange-600">
              {summary.top_skills?.length || 0}
            </div>
            <div className="text-sm text-gray-500">주요 스킬</div>
          </div>
        </div>
      )}

      {/* Top Skills */}
      {summary?.top_skills && summary.top_skills.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2">주요 스킬</h3>
          <div className="flex flex-wrap gap-2">
            {summary.top_skills.map((skill, idx) => (
              <span
                key={idx}
                className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Filter & Actions */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex gap-2 overflow-x-auto">
            <button
              onClick={() => setSelectedType('all')}
              className={`px-4 py-2 rounded-full text-sm whitespace-nowrap ${
                selectedType === 'all'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              전체 ({portfolioData?.total_count || 0})
            </button>
            {Object.entries(ARTIFACT_TYPE_LABELS).map(([type, label]) => {
              const count = portfolioData?.items.filter(i => i.artifact_type === type).length || 0;
              return (
                <button
                  key={type}
                  onClick={() => setSelectedType(type as ArtifactType)}
                  className={`px-4 py-2 rounded-full text-sm whitespace-nowrap ${
                    selectedType === type
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {label} ({count})
                </button>
              );
            })}
          </div>
          <button
            onClick={() => {
              resetForm();
              setEditingItem(null);
              setShowCreateModal(true);
            }}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 whitespace-nowrap"
          >
            + 새 항목 추가
          </button>
        </div>
      </div>

      {/* Portfolio Items Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredItems.map(item => (
          <div
            key={item.portfolio_id}
            className={`bg-white rounded-lg shadow-sm p-4 border-2 ${
              item.is_primary ? 'border-indigo-500' : 'border-transparent'
            } hover:shadow-md transition-shadow`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{ARTIFACT_TYPE_ICONS[item.artifact_type]}</span>
                <div>
                  <h3 className="font-medium">{item.title}</h3>
                  <span
                    className="text-xs px-2 py-0.5 rounded"
                    style={{ backgroundColor: ARTIFACT_TYPE_COLORS[item.artifact_type] + '20', color: ARTIFACT_TYPE_COLORS[item.artifact_type] }}
                  >
                    {ARTIFACT_TYPE_LABELS[item.artifact_type]}
                  </span>
                </div>
              </div>
              {item.is_primary && (
                <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded">
                  대표
                </span>
              )}
            </div>

            {item.description && (
              <p className="text-sm text-gray-600 mt-3 line-clamp-2">{item.description}</p>
            )}

            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:underline mt-2 block truncate"
            >
              {item.url}
            </a>

            {item.skills && item.skills.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-3">
                {item.skills.slice(0, 3).map((skill, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs"
                  >
                    {skill}
                  </span>
                ))}
                {item.skills.length > 3 && (
                  <span className="text-xs text-gray-500">+{item.skills.length - 3}</span>
                )}
              </div>
            )}

            <div className="flex items-center justify-between mt-4 pt-3 border-t">
              <div className="flex gap-2">
                <button
                  onClick={() => openEditModal(item)}
                  className="text-sm text-indigo-600 hover:bg-indigo-50 px-2 py-1 rounded"
                >
                  수정
                </button>
                <button
                  onClick={() => handleDelete(item.portfolio_id)}
                  className="text-sm text-red-600 hover:bg-red-50 px-2 py-1 rounded"
                >
                  삭제
                </button>
              </div>
              {!item.is_primary && (
                <button
                  onClick={() => handleSetPrimary(item.portfolio_id)}
                  className="text-sm text-gray-600 hover:bg-gray-100 px-2 py-1 rounded"
                >
                  대표로 설정
                </button>
              )}
            </div>
          </div>
        ))}

        {filteredItems.length === 0 && (
          <div className="col-span-full text-center py-12 text-gray-500">
            {selectedType === 'all'
              ? '포트폴리오 항목이 없습니다. 새 항목을 추가해보세요.'
              : `${ARTIFACT_TYPE_LABELS[selectedType as ArtifactType]} 유형의 항목이 없습니다.`}
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-lg w-full max-h-[85vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">
                  {editingItem ? '항목 수정' : '새 포트폴리오 항목'}
                </h2>
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingItem(null);
                    resetForm();
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">유형</label>
                  <select
                    value={formData.artifact_type}
                    onChange={e => setFormData(prev => ({ ...prev, artifact_type: e.target.value as ArtifactType }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                  >
                    {Object.entries(ARTIFACT_TYPE_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>
                        {ARTIFACT_TYPE_ICONS[value as ArtifactType]} {label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">제목</label>
                  <input
                    type="text"
                    value={formData.title || ''}
                    onChange={e => setFormData(prev => ({ ...prev, title: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="포트폴리오 제목"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">URL</label>
                  <input
                    type="url"
                    value={formData.url || ''}
                    onChange={e => setFormData(prev => ({ ...prev, url: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="https://..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">설명</label>
                  <textarea
                    value={formData.description || ''}
                    onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                    rows={3}
                    placeholder="포트폴리오 설명 (선택)"
                  />
                </div>

                {/* Tags */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">태그</label>
                  <div className="flex gap-2 mb-2">
                    <input
                      type="text"
                      value={tagInput}
                      onChange={e => setTagInput(e.target.value)}
                      onKeyPress={e => e.key === 'Enter' && (e.preventDefault(), addTag())}
                      className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                      placeholder="태그 입력 후 Enter"
                    />
                    <button
                      type="button"
                      onClick={addTag}
                      className="px-3 py-2 bg-gray-100 rounded-lg hover:bg-gray-200"
                    >
                      추가
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {formData.tags?.map((tag, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm flex items-center gap-1"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() => removeTag(idx)}
                          className="text-blue-500 hover:text-blue-700"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                </div>

                {/* Skills */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">관련 스킬</label>
                  <div className="flex gap-2 mb-2">
                    <input
                      type="text"
                      value={skillInput}
                      onChange={e => setSkillInput(e.target.value)}
                      onKeyPress={e => e.key === 'Enter' && (e.preventDefault(), addSkill())}
                      className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                      placeholder="스킬 입력 후 Enter"
                    />
                    <button
                      type="button"
                      onClick={addSkill}
                      className="px-3 py-2 bg-gray-100 rounded-lg hover:bg-gray-200"
                    >
                      추가
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {formData.skills?.map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-sm flex items-center gap-1"
                      >
                        {skill}
                        <button
                          type="button"
                          onClick={() => removeSkill(idx)}
                          className="text-indigo-500 hover:text-indigo-700"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="is_primary"
                    checked={formData.is_primary || false}
                    onChange={e => setFormData(prev => ({ ...prev, is_primary: e.target.checked }))}
                    className="w-4 h-4 text-indigo-600 rounded"
                  />
                  <label htmlFor="is_primary" className="text-sm text-gray-700">
                    대표 포트폴리오로 설정
                  </label>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingItem(null);
                    resetForm();
                  }}
                  className="flex-1 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  취소
                </button>
                <button
                  onClick={editingItem ? handleUpdate : handleCreate}
                  disabled={!formData.title || !formData.url}
                  className="flex-1 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  {editingItem ? '수정' : '추가'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
