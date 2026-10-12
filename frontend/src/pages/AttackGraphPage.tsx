import React, { useState, useEffect } from 'react';
import { 
  Share2, Info, RefreshCw, ZoomIn, ZoomOut
} from 'lucide-react';
import type { Incident, AttackGraphData, AttackGraphNode } from '../types/soc';
import { api } from '../services/api';

export const AttackGraphPage: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>('');
  const [graphData, setGraphData] = useState<AttackGraphData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedNode, setSelectedNode] = useState<AttackGraphNode | null>(null);
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [filterNodeType, setFilterNodeType] = useState<string>('all');

  useEffect(() => {
    loadIncidents();
  }, []);

  const loadIncidents = async () => {
    try {
      const data = await api.getIncidents();
      setIncidents(data);
      if (data.length > 0) {
        setSelectedIncidentId(data[0].id);
        loadGraph(data[0].id);
      } else {
        setLoading(false);
      }
    } catch (err) {
      console.error('Failed to fetch incidents', err);
      setLoading(false);
    }
  };

  const loadGraph = async (incidentId: string) => {
    setLoading(true);
    setSelectedNode(null);
    try {
      const data = await api.getAttackGraph(incidentId);
      setGraphData(data);
    } catch (err) {
      console.error('Failed to load attack graph', err);
    } finally {
      setLoading(false);
    }
  };

  const handleIncidentChange = (id: string) => {
    setSelectedIncidentId(id);
    loadGraph(id);
  };

  // Compute node coordinates dynamically in an elliptical circular layout with central incident
  const getNodeCoordinates = (nodes: AttackGraphNode[], width: number = 800, height: number = 550) => {
    const coords: Record<string, { x: number; y: number }> = {};
    const centerX = width / 2;
    const centerY = height / 2;

    const incidentNodes = nodes.filter((n) => n.type === 'incident');
    const otherNodes = nodes.filter((n) => n.type !== 'incident');

    if (incidentNodes.length > 0) {
      coords[incidentNodes[0].id] = { x: centerX, y: centerY };
    }

    const radiusX = width * 0.38;
    const radiusY = height * 0.38;
    const count = otherNodes.length;

    otherNodes.forEach((node, index) => {
      const angle = (index / count) * 2 * Math.PI;
      coords[node.id] = {
        x: centerX + radiusX * Math.cos(angle),
        y: centerY + radiusY * Math.sin(angle),
      };
    });

    return coords;
  };

  const getNodeColor = (type: string, severity: string) => {
    switch (type) {
      case 'incident':
        return '#f43f5e'; // rose-500
      case 'finding':
        return severity === 'critical' ? '#ef4444' : '#f59e0b';
      case 'host':
        return '#06b6d4'; // cyan-500
      case 'user':
        return '#8b5cf6'; // purple-500
      case 'ip':
        return '#3b82f6'; // blue-500
      case 'process':
        return '#10b981'; // emerald-500
      default:
        return '#64748b'; // slate-500
    }
  };

  const visibleNodes = (graphData?.nodes || []).filter(
    (n) => filterNodeType === 'all' || n.type === filterNodeType || n.type === 'incident'
  );
  const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));

  const visibleEdges = (graphData?.edges || []).filter(
    (e) => visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)
  );

  const coords = getNodeCoordinates(visibleNodes);

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Share2 className="w-5 h-5 text-cyan-400" />
            Attack-Graph Topological Reasoning Canvas
          </h2>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            NetworkX multi-hop entity relationship graph linking host telemetry, network endpoints, and IOC indicators
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-[var(--text-muted)] font-mono">INCIDENT:</span>
            <select
              value={selectedIncidentId}
              onChange={(e) => handleIncidentChange(e.target.value)}
              className="bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] text-xs text-cyan-300 font-mono rounded-lg px-3 py-1.5 focus:outline-none focus:border-cyan-500"
            >
              {incidents.map((inc) => (
                <option key={inc.id} value={inc.id}>
                  {inc.id.substring(0, 8)} - {inc.title.substring(0, 32)}...
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => selectedIncidentId && loadGraph(selectedIncidentId)}
            disabled={loading}
            className="p-1.5 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] text-slate-300 hover:text-white hover:border-[var(--border-hover)]"
            title="Reload Topology"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Main Canvas & Inspector Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Interactive Graph Area (3 Cols) */}
        <div className="lg:col-span-3 cyber-card p-4 flex flex-col relative min-h-[580px] overflow-hidden">
          {/* Canvas Toolbar overlay */}
          <div className="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)] z-10">
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400">Filter Nodes:</span>
              {['all', 'host', 'ip', 'user', 'process', 'finding'].map((t) => (
                <button
                  key={t}
                  onClick={() => setFilterNodeType(t)}
                  className={`px-2 py-0.5 rounded text-[11px] font-mono capitalize transition-all ${
                    filterNodeType === t
                      ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setZoomLevel((z) => Math.max(0.6, z - 0.15))}
                className="p-1 rounded bg-[var(--bg-tertiary)] text-slate-300 hover:text-white"
                title="Zoom Out"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <span className="text-[10px] font-mono text-slate-400 w-10 text-center">
                {(zoomLevel * 100).toFixed(0)}%
              </span>
              <button
                onClick={() => setZoomLevel((z) => Math.min(1.6, z + 0.15))}
                className="p-1 rounded bg-[var(--bg-tertiary)] text-slate-300 hover:text-white"
                title="Zoom In"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* SVG Canvas */}
          <div className="flex-1 w-full h-full flex items-center justify-center relative overflow-hidden select-none">
            {loading ? (
              <div className="text-center text-slate-400">
                <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                <p className="text-xs">Computing topological risk pathways...</p>
              </div>
            ) : !graphData || visibleNodes.length === 0 ? (
              <div className="text-center text-slate-500">
                <Share2 className="w-10 h-10 mx-auto mb-2 opacity-30" />
                <p className="text-sm">No topological data found for this incident</p>
              </div>
            ) : (
              <div
                className="transition-transform duration-200"
                style={{ transform: `scale(${zoomLevel})` }}
              >
                <svg
                  width="800"
                  height="550"
                  viewBox="0 0 800 550"
                  className="overflow-visible"
                >
                  <defs>
                    <marker
                      id="arrow"
                      viewBox="0 0 10 10"
                      refX="22"
                      refY="5"
                      markerWidth="6"
                      markerHeight="6"
                      orient="auto-start-reverse"
                    >
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
                    </marker>
                  </defs>

                  {/* Edges */}
                  {visibleEdges.map((edge, idx) => {
                    const src = coords[edge.source];
                    const dst = coords[edge.target];
                    if (!src || !dst) return null;

                    const midX = (src.x + dst.x) / 2;
                    const midY = (src.y + dst.y) / 2;

                    return (
                      <g key={idx}>
                        <line
                          x1={src.x}
                          y1={src.y}
                          x2={dst.x}
                          y2={dst.y}
                          stroke="#334155"
                          strokeWidth="1.5"
                          strokeDasharray={edge.relation.includes('finding') ? '3 3' : 'none'}
                          markerEnd="url(#arrow)"
                        />
                        <text
                          x={midX}
                          y={midY - 4}
                          fill="#64748b"
                          fontSize="9"
                          textAnchor="middle"
                          fontFamily="monospace"
                        >
                          {edge.relation}
                        </text>
                      </g>
                    );
                  })}

                  {/* Nodes */}
                  {visibleNodes.map((node) => {
                    const pos = coords[node.id];
                    if (!pos) return null;
                    const isSelected = selectedNode?.id === node.id;
                    const isCentral = node.type === 'incident';
                    const radius = isCentral ? 26 : 18;
                    const color = getNodeColor(node.type, node.severity);

                    return (
                      <g
                        key={node.id}
                        transform={`translate(${pos.x}, ${pos.y})`}
                        onClick={() => setSelectedNode(node)}
                        className="cursor-pointer group"
                      >
                        {/* Glow halo on selection */}
                        {isSelected && (
                          <circle
                            r={radius + 8}
                            fill="none"
                            stroke={color}
                            strokeWidth="2"
                            strokeDasharray="4 2"
                            className="animate-spin origin-center"
                          />
                        )}

                        <circle
                          r={radius}
                          fill="#0f172a"
                          stroke={color}
                          strokeWidth={isSelected ? 3 : 2}
                          className="transition-all hover:scale-110"
                        />

                        {/* Node Label underneath */}
                        <text
                          y={radius + 14}
                          fill={isSelected ? '#38bdf8' : '#cbd5e1'}
                          fontSize="10"
                          fontWeight={isSelected ? 'bold' : 'normal'}
                          textAnchor="middle"
                          fontFamily="monospace"
                        >
                          {node.label.length > 16 ? `${node.label.substring(0, 14)}...` : node.label}
                        </text>

                        {/* Node Type badge text */}
                        <text
                          y={radius + 25}
                          fill="#64748b"
                          fontSize="8"
                          textAnchor="middle"
                          fontFamily="monospace"
                        >
                          [{node.type}]
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>
            )}
          </div>

          {/* Graph Legend bottom-bar */}
          <div className="pt-3 border-t border-[var(--border-subtle)] flex flex-wrap items-center justify-between text-[11px] text-slate-400">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" /> Incident Root
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-500 inline-block" /> Host Entity
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-500 inline-block" /> User / Account
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block" /> IP / Network
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" /> Process
              </span>
            </div>
            <div className="font-mono text-[10px] text-slate-500">
              Total Nodes: {graphData?.node_count || 0} &bull; Total Edges: {graphData?.edge_count || 0}
            </div>
          </div>
        </div>

        {/* Node Inspector Panel (1 Col) */}
        <div className="cyber-card p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)]">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Node Inspector
            </h3>
            {selectedNode && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                {selectedNode.type}
              </span>
            )}
          </div>

          {selectedNode ? (
            <div className="space-y-4 text-xs">
              <div>
                <span className="text-[10px] text-[var(--text-muted)] uppercase block">Node Identifier</span>
                <span className="font-mono font-medium text-white break-all">{selectedNode.label}</span>
              </div>

              <div>
                <span className="text-[10px] text-[var(--text-muted)] uppercase block">Risk Weight</span>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-cyan-500 to-rose-500"
                      style={{ width: `${Math.min(100, selectedNode.risk_score * 10)}%` }}
                    />
                  </div>
                  <span className="font-mono text-slate-200 font-bold">{selectedNode.risk_score} / 10</span>
                </div>
              </div>

              <div>
                <span className="text-[10px] text-[var(--text-muted)] uppercase block">Assigned Severity</span>
                <span className="font-mono capitalize text-slate-300">{selectedNode.severity}</span>
              </div>

              {selectedNode.metadata && Object.keys(selectedNode.metadata).length > 0 && (
                <div className="pt-2 border-t border-[var(--border-subtle)]">
                  <span className="text-[10px] text-[var(--text-muted)] uppercase block mb-1.5">
                    Topological Attributes
                  </span>
                  <div className="bg-[var(--bg-primary)] p-3 rounded-lg border border-[var(--border-subtle)] space-y-1.5 font-mono text-[11px]">
                    {Object.entries(selectedNode.metadata).map(([k, v]) => (
                      <div key={k} className="flex justify-between">
                        <span className="text-slate-500">{k}:</span>
                        <span className="text-cyan-300 break-all">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="py-12 text-center text-slate-500">
              <Info className="w-8 h-8 mx-auto mb-2 opacity-40 text-cyan-400" />
              <p className="text-xs">Click any node on the graph canvas to inspect topological risk attributes.</p>
            </div>
          )}

          {/* Academic Note */}
          <div className="p-3 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] text-[11px] text-[var(--text-muted)] space-y-1">
            <span className="font-semibold text-slate-300 block">Graph Reasoning Algorithm</span>
            <p>
              Uses NetworkX path traversal to link related raw events, identifying lateral movement and privilege escalation clusters.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
