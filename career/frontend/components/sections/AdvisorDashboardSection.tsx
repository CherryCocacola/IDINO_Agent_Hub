'use client';

import { useState, useEffect, useCallback } from 'react';
import { advisorService } from '@/lib/api/advisor';
import type {
  AdvisorDashboardResponse,
  MeetingResponse,
  MeetingCreate,
  StudentSummary,
} from '@/types/advisor';

interface AdvisorDashboardSectionProps {
  advisorId: string;
}

export default function AdvisorDashboardSection({ advisorId }: AdvisorDashboardSectionProps) {
  const [dashboard, setDashboard] = useState<AdvisorDashboardResponse | null>(null);
  const [students, setStudents] = useState<StudentSummary[]>([]);
  const [meetings, setMeetings] = useState<MeetingResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'students' | 'meetings'>('overview');
  const [selectedStudent, setSelectedStudent] = useState<StudentSummary | null>(null);
  const [showMeetingModal, setShowMeetingModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [riskFilter, setRiskFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');

  // New meeting form
  const [newMeeting, setNewMeeting] = useState<Partial<MeetingCreate>>({
    advisor_id: advisorId,
    student_id: '',
    meeting_type: 'in_person',
    scheduled_at: '',
    title: '',
    description: '',
  });

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const [dashboardData, studentsData, meetingsData] = await Promise.all([
        advisorService.getDashboard(advisorId),
        advisorService.getStudents(advisorId),
        advisorService.getMeetings(advisorId),
      ]);
      setDashboard(dashboardData);
      setStudents(studentsData);
      setMeetings(meetingsData);
    } catch (error) {
      console.error('Failed to fetch advisor dashboard:', error);
    } finally {
      setLoading(false);
    }
  }, [advisorId]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const handleCreateMeeting = async () => {
    if (!newMeeting.student_id || !newMeeting.scheduled_at || !newMeeting.title) return;

    try {
      const meeting = await advisorService.createMeeting(newMeeting as MeetingCreate);
      setMeetings(prev => [meeting, ...prev]);
      setShowMeetingModal(false);
      setNewMeeting({
        advisor_id: advisorId,
        student_id: '',
        meeting_type: 'in_person',
        scheduled_at: '',
        title: '',
        description: '',
      });
    } catch (error) {
      console.error('Failed to create meeting:', error);
    }
  };

  const handleCompleteMeeting = async (meetingId: string) => {
    try {
      const updated = await advisorService.completeMeeting(meetingId);
      setMeetings(prev => prev.map(m => m.meeting_id === meetingId ? updated : m));
    } catch (error) {
      console.error('Failed to complete meeting:', error);
    }
  };

  const filteredStudents = students.filter(student => {
    const matchesSearch = student.student_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      student.student_id.includes(searchTerm);
    const matchesRisk = riskFilter === 'all' || student.risk_level === riskFilter;
    return matchesSearch && matchesRisk;
  });

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high': return 'bg-red-100 text-red-800 border-red-300';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low': return 'bg-green-100 text-green-800 border-green-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getRiskLabel = (level: string) => {
    switch (level) {
      case 'high': return '고위험';
      case 'medium': return '중위험';
      case 'low': return '저위험';
      default: return '미평가';
    }
  };

  const getMeetingStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'scheduled': return 'bg-blue-100 text-blue-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-8">
        <div className="animate-pulse space-y-4">
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Dashboard Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm p-4">
          <div className="text-3xl font-bold text-indigo-600">{dashboard?.analytics?.total_students || 0}</div>
          <div className="text-sm text-gray-500">담당 학생</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-4">
          <div className="text-3xl font-bold text-red-600">
            {(dashboard?.analytics?.by_risk_level?.high || 0) + (dashboard?.analytics?.by_risk_level?.critical || 0)}
          </div>
          <div className="text-sm text-gray-500">고위험 학생</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-4">
          <div className="text-3xl font-bold text-yellow-600">{dashboard?.analytics?.pending_followups || 0}</div>
          <div className="text-sm text-gray-500">후속 조치 필요</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-4">
          <div className="text-3xl font-bold text-blue-600">{meetings.filter(m => m.status === 'scheduled').length}</div>
          <div className="text-sm text-gray-500">예정 상담</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="border-b">
          <nav className="flex">
            {[
              { id: 'overview', label: '개요' },
              { id: 'students', label: `학생 관리 (${students.length})` },
              { id: 'meetings', label: `상담 일정 (${meetings.length})` },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`px-6 py-3 font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'text-indigo-600 border-indigo-600'
                    : 'text-gray-500 border-transparent hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Risk Distribution */}
              <div>
                <h3 className="text-lg font-semibold mb-4">위험도 분포</h3>
                <div className="flex gap-4">
                  <div className="flex-1 p-4 rounded-lg bg-red-50 border border-red-200">
                    <div className="text-2xl font-bold text-red-600">
                      {students.filter(s => s.risk_level === 'high').length}
                    </div>
                    <div className="text-sm text-red-700">고위험</div>
                  </div>
                  <div className="flex-1 p-4 rounded-lg bg-yellow-50 border border-yellow-200">
                    <div className="text-2xl font-bold text-yellow-600">
                      {students.filter(s => s.risk_level === 'medium').length}
                    </div>
                    <div className="text-sm text-yellow-700">중위험</div>
                  </div>
                  <div className="flex-1 p-4 rounded-lg bg-green-50 border border-green-200">
                    <div className="text-2xl font-bold text-green-600">
                      {students.filter(s => s.risk_level === 'low').length}
                    </div>
                    <div className="text-sm text-green-700">저위험</div>
                  </div>
                </div>
              </div>

              {/* Attention Required */}
              <div>
                <h3 className="text-lg font-semibold mb-4">주의 필요 학생</h3>
                {students.filter(s => s.risk_level === 'high').length > 0 ? (
                  <div className="space-y-3">
                    {students
                      .filter(s => s.risk_level === 'high')
                      .slice(0, 5)
                      .map(student => (
                        <div
                          key={student.student_id}
                          className="p-4 border border-red-200 rounded-lg bg-red-50 cursor-pointer hover:bg-red-100"
                          onClick={() => setSelectedStudent(student)}
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <span className="font-medium">{student.student_name}</span>
                              <span className="text-sm text-gray-500 ml-2">({student.student_id})</span>
                            </div>
                            <span className={`px-2 py-1 rounded text-xs ${getRiskColor(student.risk_level)}`}>
                              {getRiskLabel(student.risk_level)}
                            </span>
                          </div>
                          {student.active_alerts > 0 && (
                            <div className="mt-2 text-sm text-red-700">
                              ⚠️ {student.active_alerts}건의 알림
                            </div>
                          )}
                        </div>
                      ))}
                  </div>
                ) : (
                  <p className="text-gray-500">주의가 필요한 학생이 없습니다.</p>
                )}
              </div>

              {/* Upcoming Meetings */}
              <div>
                <h3 className="text-lg font-semibold mb-4">예정된 상담</h3>
                {meetings.filter(m => m.status === 'scheduled').length > 0 ? (
                  <div className="space-y-2">
                    {meetings
                      .filter(m => m.status === 'scheduled')
                      .slice(0, 5)
                      .map(meeting => (
                        <div key={meeting.meeting_id} className="p-3 border rounded-lg flex items-center justify-between">
                          <div>
                            <span className="font-medium">{meeting.student_name}</span>
                            <span className="text-sm text-gray-500 ml-2">- {meeting.title}</span>
                          </div>
                          <span className="text-sm text-gray-500">{meeting.scheduled_at}</span>
                        </div>
                      ))}
                  </div>
                ) : (
                  <p className="text-gray-500">예정된 상담이 없습니다.</p>
                )}
              </div>
            </div>
          )}

          {/* Students Tab */}
          {activeTab === 'students' && (
            <div>
              {/* Filters */}
              <div className="flex gap-4 mb-6">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={e => setSearchTerm(e.target.value)}
                  placeholder="학생 검색..."
                  className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
                <select
                  value={riskFilter}
                  onChange={e => setRiskFilter(e.target.value as typeof riskFilter)}
                  className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="all">전체 위험도</option>
                  <option value="high">고위험</option>
                  <option value="medium">중위험</option>
                  <option value="low">저위험</option>
                </select>
              </div>

              {/* Students List */}
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">학생</th>
                      <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">학과</th>
                      <th className="text-center px-4 py-3 text-sm font-medium text-gray-600">학년</th>
                      <th className="text-center px-4 py-3 text-sm font-medium text-gray-600">평점</th>
                      <th className="text-center px-4 py-3 text-sm font-medium text-gray-600">위험도</th>
                      <th className="text-center px-4 py-3 text-sm font-medium text-gray-600">진도</th>
                      <th className="text-center px-4 py-3 text-sm font-medium text-gray-600">작업</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {filteredStudents.map(student => (
                      <tr key={student.student_id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div className="font-medium">{student.student_name}</div>
                          <div className="text-sm text-gray-500">{student.student_id}</div>
                        </td>
                        <td className="px-4 py-3 text-sm">{student.major || '-'}</td>
                        <td className="px-4 py-3 text-center text-sm">{student.grade}학년</td>
                        <td className="px-4 py-3 text-center text-sm">{student.gpa?.toFixed(2) || '-'}</td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(student.risk_level)}`}>
                            {getRiskLabel(student.risk_level)}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-indigo-600 h-2 rounded-full"
                              style={{ width: `${student.progress_percentage || 0}%` }}
                            />
                          </div>
                          <div className="text-xs text-gray-500 text-center mt-1">
                            {student.progress_percentage || 0}%
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <button
                            onClick={() => setSelectedStudent(student)}
                            className="px-3 py-1 text-sm text-indigo-600 hover:bg-indigo-50 rounded"
                          >
                            상세
                          </button>
                          <button
                            onClick={() => {
                              setNewMeeting(prev => ({ ...prev, student_id: student.student_id }));
                              setShowMeetingModal(true);
                            }}
                            className="px-3 py-1 text-sm text-green-600 hover:bg-green-50 rounded"
                          >
                            상담
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Meetings Tab */}
          {activeTab === 'meetings' && (
            <div>
              <div className="flex justify-end mb-4">
                <button
                  onClick={() => setShowMeetingModal(true)}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                >
                  + 새 상담 일정
                </button>
              </div>

              <div className="space-y-3">
                {meetings.map(meeting => (
                  <div key={meeting.meeting_id} className="p-4 border rounded-lg">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{meeting.student_name}</span>
                          <span className={`px-2 py-0.5 rounded text-xs ${getMeetingStatusColor(meeting.status)}`}>
                            {meeting.status === 'scheduled' ? '예정' : meeting.status === 'completed' ? '완료' : '취소'}
                          </span>
                        </div>
                        <div className="text-sm text-gray-600 mt-1">{meeting.title}</div>
                        <div className="text-sm text-gray-500 mt-1">{meeting.scheduled_at}</div>
                      </div>
                      {meeting.status === 'scheduled' && (
                        <button
                          onClick={() => handleCompleteMeeting(meeting.meeting_id)}
                          className="px-3 py-1 text-sm border border-green-500 text-green-600 rounded hover:bg-green-50"
                        >
                          완료
                        </button>
                      )}
                    </div>
                    {meeting.notes && (
                      <div className="mt-3 p-3 bg-gray-50 rounded text-sm text-gray-600">
                        {meeting.notes}
                      </div>
                    )}
                  </div>
                ))}

                {meetings.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    상담 일정이 없습니다.
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Student Detail Modal */}
      {selectedStudent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold">학생 상세 정보</h2>
                <button
                  onClick={() => setSelectedStudent(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-6">
                {/* Basic Info */}
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-full bg-indigo-100 flex items-center justify-center text-2xl font-bold text-indigo-600">
                    {selectedStudent.student_name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="text-xl font-bold">{selectedStudent.student_name}</h3>
                    <div className="text-gray-500">{selectedStudent.student_id} • {selectedStudent.major || '-'}</div>
                  </div>
                  <span className={`ml-auto px-3 py-1 rounded-full text-sm ${getRiskColor(selectedStudent.risk_level)}`}>
                    {getRiskLabel(selectedStudent.risk_level)}
                  </span>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-3 bg-gray-50 rounded-lg text-center">
                    <div className="text-2xl font-bold">{selectedStudent.grade}</div>
                    <div className="text-sm text-gray-500">학년</div>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg text-center">
                    <div className="text-2xl font-bold">{selectedStudent.gpa?.toFixed(2) || '-'}</div>
                    <div className="text-sm text-gray-500">평점</div>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg text-center">
                    <div className="text-2xl font-bold">{selectedStudent.progress_percentage || 0}%</div>
                    <div className="text-sm text-gray-500">진도</div>
                  </div>
                </div>

                {/* Alerts */}
                {selectedStudent.active_alerts > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">활성 알림</h4>
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                      ⚠️ {selectedStudent.active_alerts}건의 활성 알림이 있습니다.
                    </div>
                  </div>
                )}

                {/* Progress Info */}
                {selectedStudent.needs_attention && (
                  <div>
                    <h4 className="font-medium mb-2">주의 필요</h4>
                    <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-700">
                      📌 이 학생은 추가적인 관심이 필요합니다.
                    </div>
                  </div>
                )}
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => {
                    setNewMeeting(prev => ({ ...prev, student_id: selectedStudent.student_id }));
                    setSelectedStudent(null);
                    setShowMeetingModal(true);
                  }}
                  className="flex-1 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                >
                  상담 예약
                </button>
                <button
                  onClick={() => setSelectedStudent(null)}
                  className="flex-1 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  닫기
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Meeting Modal */}
      {showMeetingModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">새 상담 일정</h2>
                <button
                  onClick={() => setShowMeetingModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">학생</label>
                  <select
                    value={newMeeting.student_id}
                    onChange={e => setNewMeeting(prev => ({ ...prev, student_id: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">선택하세요</option>
                    {students.map(student => (
                      <option key={student.student_id} value={student.student_id}>
                        {student.student_name} ({student.student_id})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">상담 유형</label>
                  <select
                    value={newMeeting.meeting_type || 'in_person'}
                    onChange={e => setNewMeeting(prev => ({ ...prev, meeting_type: e.target.value as 'in_person' | 'video' | 'phone' }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="in_person">대면 상담</option>
                    <option value="video">화상 상담</option>
                    <option value="phone">전화 상담</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">일시</label>
                  <input
                    type="datetime-local"
                    value={newMeeting.scheduled_at}
                    onChange={e => setNewMeeting(prev => ({ ...prev, scheduled_at: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">주제</label>
                  <input
                    type="text"
                    value={newMeeting.title || ''}
                    onChange={e => setNewMeeting(prev => ({ ...prev, title: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="상담 주제"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">메모 (선택)</label>
                  <textarea
                    value={newMeeting.description || ''}
                    onChange={e => setNewMeeting(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                    rows={3}
                    placeholder="사전 메모"
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowMeetingModal(false)}
                  className="flex-1 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  취소
                </button>
                <button
                  onClick={handleCreateMeeting}
                  disabled={!newMeeting.student_id || !newMeeting.scheduled_at || !newMeeting.title}
                  className="flex-1 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  예약
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
