'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Network, ZoomIn, ZoomOut, RefreshCw, Info } from 'lucide-react';
import { skillService } from '@/lib/api/skill';
import type { SkillGraphResponse, SkillNode, SkillEdge } from '@/types';

interface SkillGraphSectionProps {
  studentId: string;
  selectedRole: string;
  onRoleChange: (role: string) => void;
}

interface Role {
  role_cd: string;
  role_nm: string;
  industry?: string;
}

// Force simulation for graph layout
const useForceSimulation = (nodes: SkillNode[], edges: SkillEdge[], width: number, height: number) => {
  const [positions, setPositions] = useState<Map<string, { x: number; y: number }>>(new Map());

  useEffect(() => {
    if (nodes.length === 0) return;

    // Initialize positions
    const newPositions = new Map<string, { x: number; y: number }>();
    nodes.forEach((node, index) => {
      const angle = (2 * Math.PI * index) / nodes.length;
      const radius = Math.min(width, height) * 0.3;
      newPositions.set(node.id, {
        x: width / 2 + radius * Math.cos(angle),
        y: height / 2 + radius * Math.sin(angle),
      });
    });

    // Simple force simulation (runs a few iterations)
    const iterations = 100;
    const nodeArray = [...nodes];
    const edgeSet = new Set(edges.map(e => `${e.source}-${e.target}`));

    for (let i = 0; i < iterations; i++) {
      const forces = new Map<string, { fx: number; fy: number }>();
      nodeArray.forEach(n => forces.set(n.id, { fx: 0, fy: 0 }));

      // Repulsion between all nodes
      for (let a = 0; a < nodeArray.length; a++) {
        for (let b = a + 1; b < nodeArray.length; b++) {
          const posA = newPositions.get(nodeArray[a].id)!;
          const posB = newPositions.get(nodeArray[b].id)!;
          const dx = posB.x - posA.x;
          const dy = posB.y - posA.y;
          const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
          const force = 500 / (dist * dist);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          forces.get(nodeArray[a].id)!.fx -= fx;
          forces.get(nodeArray[a].id)!.fy -= fy;
          forces.get(nodeArray[b].id)!.fx += fx;
          forces.get(nodeArray[b].id)!.fy += fy;
        }
      }

      // Attraction for connected nodes
      edges.forEach(edge => {
        const posA = newPositions.get(edge.source);
        const posB = newPositions.get(edge.target);
        if (!posA || !posB) return;
        const dx = posB.x - posA.x;
        const dy = posB.y - posA.y;
        const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
        const force = (dist - 100) * 0.01 * edge.strength;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        if (forces.has(edge.source)) {
          forces.get(edge.source)!.fx += fx;
          forces.get(edge.source)!.fy += fy;
        }
        if (forces.has(edge.target)) {
          forces.get(edge.target)!.fx -= fx;
          forces.get(edge.target)!.fy -= fy;
        }
      });

      // Center gravity
      nodeArray.forEach(node => {
        const pos = newPositions.get(node.id)!;
        const dx = width / 2 - pos.x;
        const dy = height / 2 - pos.y;
        forces.get(node.id)!.fx += dx * 0.001;
        forces.get(node.id)!.fy += dy * 0.001;
      });

      // Apply forces
      nodeArray.forEach(node => {
        const pos = newPositions.get(node.id)!;
        const force = forces.get(node.id)!;
        const decay = 0.9 - (i / iterations) * 0.5;
        pos.x += force.fx * decay;
        pos.y += force.fy * decay;
        // Keep within bounds
        pos.x = Math.max(50, Math.min(width - 50, pos.x));
        pos.y = Math.max(50, Math.min(height - 50, pos.y));
      });
    }

    setPositions(newPositions);
  }, [nodes, edges, width, height]);

  return positions;
};

// Node color based on category or gap
const getNodeColor = (node: SkillNode): string => {
  if (node.gap !== undefined && node.gap > 0) {
    if (node.gap >= 3) return '#ef4444'; // red
    if (node.gap >= 2) return '#f59e0b'; // amber
    if (node.gap >= 1) return '#eab308'; // yellow
  }
  switch (node.category) {
    case 'programming': return '#3b82f6';
    case 'data': return '#22c55e';
    case 'ai': return '#8b5cf6';
    case 'soft_skill': return '#ec4899';
    default: return '#6b7280';
  }
};

// Edge color based on type
const getEdgeColor = (type: string): string => {
  switch (type) {
    case 'prerequisite': return '#ef4444';
    case 'builds_on': return '#3b82f6';
    case 'complementary': return '#22c55e';
    case 'alternative': return '#9ca3af';
    default: return '#d1d5db';
  }
};

export default function SkillGraphSection({
  studentId,
  selectedRole,
  onRoleChange,
}: SkillGraphSectionProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [graphData, setGraphData] = useState<SkillGraphResponse | null>(null);
  const [roles, setRoles] = useState<Role[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const [hoveredNode, setHoveredNode] = useState<SkillNode | null>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });

  // Fetch roles filtered by student's department
  useEffect(() => {
    const fetchRoles = async () => {
      try {
        const data = await skillService.getStudentRoles(studentId);
        setRoles(data);
        if (!selectedRole && data.length > 0) {
          onRoleChange(data[0].role_cd);
        }
      } catch (err) {
        console.error('Failed to fetch roles:', err);
      }
    };
    fetchRoles();
  }, [studentId]);

  // Fetch skill graph
  useEffect(() => {
    const fetchGraph = async () => {
      if (!selectedRole) return;
      setIsLoading(true);
      setError(null);
      try {
        const data = await skillService.getStudentSkillGraph(studentId, selectedRole);
        setGraphData(data);
      } catch (err) {
        setError('스킬 그래프를 불러오는데 실패했습니다.');
        console.error('Failed to fetch skill graph:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchGraph();
  }, [studentId, selectedRole]);

  // Container resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: 500,
        });
      }
    };
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  const positions = useForceSimulation(
    graphData?.nodes || [],
    graphData?.edges || [],
    dimensions.width,
    dimensions.height
  );

  const handleRefresh = useCallback(async () => {
    if (!selectedRole) return;
    setIsLoading(true);
    try {
      const data = await skillService.getStudentSkillGraph(studentId, selectedRole);
      setGraphData(data);
    } catch (err) {
      console.error('Failed to refresh:', err);
    } finally {
      setIsLoading(false);
    }
  }, [studentId, selectedRole]);

  return (
    <div className="bg-card rounded-xl p-6 border border-border">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-blue-100">
            <Network className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-text">스킬 관계 그래프</h3>
            <p className="text-xs text-muted">스킬 간의 관계를 시각화합니다</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedRole}
            onChange={(e) => onRoleChange(e.target.value)}
            className="px-3 py-1.5 text-sm border border-border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">역할 선택</option>
            {roles.map((role) => (
              <option key={role.role_cd} value={role.role_cd}>
                {role.role_nm}
              </option>
            ))}
          </select>

          <div className="flex items-center border border-border rounded-lg">
            <button
              onClick={() => setZoom(Math.max(0.5, zoom - 0.1))}
              className="p-1.5 hover:bg-hover rounded-l-lg"
              title="축소"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="px-2 text-sm text-muted">{Math.round(zoom * 100)}%</span>
            <button
              onClick={() => setZoom(Math.min(2, zoom + 0.1))}
              className="p-1.5 hover:bg-hover rounded-r-lg"
              title="확대"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="p-1.5 hover:bg-hover rounded-lg disabled:opacity-50"
            title="새로고침"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Graph Container */}
      <div
        ref={containerRef}
        className="relative bg-gray-50 rounded-lg overflow-hidden"
        style={{ height: dimensions.height }}
      >
        {isLoading && !graphData && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              <p className="text-sm text-muted">그래프 로딩 중...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center text-red-500">
              <p>{error}</p>
              <button
                onClick={handleRefresh}
                className="mt-2 px-3 py-1 text-sm bg-red-100 rounded-lg hover:bg-red-200"
              >
                다시 시도
              </button>
            </div>
          </div>
        )}

        {graphData && positions.size > 0 && (
          <svg
            width="100%"
            height="100%"
            viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
            style={{ transform: `scale(${zoom})`, transformOrigin: 'center' }}
          >
            {/* Edges */}
            {graphData.edges.map((edge, i) => {
              const source = positions.get(edge.source);
              const target = positions.get(edge.target);
              if (!source || !target) return null;
              const dashArray =
                edge.relation_type === 'prerequisite' ? '4,3' :
                edge.relation_type === 'builds_on' ? '8,4' :
                undefined;
              return (
                <line
                  key={i}
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                  stroke={getEdgeColor(edge.relation_type)}
                  strokeWidth={edge.strength * 2}
                  strokeOpacity={0.6}
                  strokeDasharray={dashArray}
                />
              );
            })}

            {/* Nodes */}
            {graphData.nodes.map((node) => {
              const pos = positions.get(node.id);
              if (!pos) return null;
              const isHovered = hoveredNode?.id === node.id;
              const importanceNum = node.importance ? Number(node.importance) : 0;
              const baseRadius = importanceNum > 0 ? Math.max(18, Math.min(30, 14 + importanceNum * 3)) : 24;
              const radius = isHovered ? baseRadius + 4 : baseRadius;
              return (
                <g
                  key={node.id}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  onMouseEnter={() => setHoveredNode(node)}
                  onMouseLeave={() => setHoveredNode(null)}
                  style={{ cursor: 'pointer' }}
                >
                  <circle
                    r={radius}
                    fill={getNodeColor(node)}
                    stroke={isHovered ? '#1e40af' : 'white'}
                    strokeWidth={isHovered ? 3 : 2}
                    className="transition-all duration-150"
                  />
                  <text
                    textAnchor="middle"
                    dy="0.35em"
                    fill="white"
                    fontSize={isHovered ? 11 : 10}
                    fontWeight="500"
                    className="select-none pointer-events-none"
                  >
                    {node.name.length > 6 ? node.name.slice(0, 6) + '..' : node.name}
                  </text>
                  {node.student_level !== undefined && (
                    <text
                      textAnchor="middle"
                      dy="2.2em"
                      fill={getNodeColor(node)}
                      fontSize={9}
                      className="select-none pointer-events-none"
                    >
                      Lv.{node.student_level}/{node.required_level || '?'}
                    </text>
                  )}
                </g>
              );
            })}
          </svg>
        )}

        {/* Tooltip */}
        {hoveredNode && (
          <div className="absolute top-4 right-4 bg-white p-3 rounded-lg shadow-lg border border-border max-w-xs">
            <h4 className="font-semibold text-text">{hoveredNode.name}</h4>
            <div className="text-sm text-muted mt-1 space-y-1">
              {hoveredNode.category && <p>카테고리: {hoveredNode.category}</p>}
              {hoveredNode.student_level !== undefined && (
                <p>현재 레벨: {hoveredNode.student_level}</p>
              )}
              {hoveredNode.required_level !== undefined && (
                <p>필요 레벨: {hoveredNode.required_level}</p>
              )}
              {hoveredNode.gap !== undefined && hoveredNode.gap > 0 && (
                <p className="text-red-500">갭: {hoveredNode.gap}</p>
              )}
              {hoveredNode.importance && <p>중요도: {hoveredNode.importance}</p>}
            </div>
          </div>
        )}
      </div>

      {/* Description */}
      <p className="text-xs text-muted mt-4 mb-2">
        목표 직무 대비 현재 스킬 갭을 시각화합니다. 노드 크기는 해당 스킬의 중요도(importance)에 비례합니다.
      </p>

      {/* Legend */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3 bg-gray-50 rounded-lg text-xs text-muted">
        {/* Node Colors */}
        <div>
          <p className="font-medium text-text mb-1.5">노드 색상 (스킬 갭)</p>
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-red-500"></span>
              <span>큰 갭 (≥3)</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-amber-500"></span>
              <span>보통 갭 (2)</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
              <span>낮은 갭 (1)</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-green-500"></span>
              <span>달성 (갭 없음)</span>
            </div>
          </div>
        </div>
        {/* Edge Types */}
        <div>
          <p className="font-medium text-text mb-1.5">엣지 유형 (스킬 관계)</p>
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1">
              <svg width="20" height="4"><line x1="0" y1="2" x2="20" y2="2" stroke="#ef4444" strokeWidth="2" strokeDasharray="3,2"/></svg>
              <span>선행관계</span>
            </div>
            <div className="flex items-center gap-1">
              <svg width="20" height="4"><line x1="0" y1="2" x2="20" y2="2" stroke="#22c55e" strokeWidth="2"/></svg>
              <span>보완관계</span>
            </div>
            <div className="flex items-center gap-1">
              <svg width="20" height="4"><line x1="0" y1="2" x2="20" y2="2" stroke="#3b82f6" strokeWidth="2" strokeDasharray="6,3"/></svg>
              <span>발전관계</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
