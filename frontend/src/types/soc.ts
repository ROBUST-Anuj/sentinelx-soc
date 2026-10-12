export interface Incident {
  id: string;
  title: string;
  summary: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'informational';
  status: 'new' | 'investigating' | 'contained' | 'resolved' | 'dismissed';
  assigned_to?: string | null;
  findings_count: number;
  first_seen: string;
  last_seen: string;
  affected_entities: string[];
  threat_intel_matches: string[];
  graph_risk_score: number;
  created_at: string;
}

export interface DetectionFinding {
  id: string;
  detector_type: 'rule' | 'ml' | 'threat_intel' | 'hybrid';
  rule_or_model_name: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  evidence_events: string[];
  affected_entity?: string;
  confidence: number;
  created_at: string;
  metadata_info?: Record<string, any>;
}

export interface CanonicalEvent {
  id?: string;
  event_id: string;
  timestamp: string;
  source_type: string;
  source_name: string;
  host_id?: string;
  user_id?: string;
  src_ip?: string;
  src_port?: number;
  dst_ip?: string;
  dst_port?: number;
  protocol?: string;
  event_type: string;
  severity: string;
  process_name?: string;
  command_line?: string;
  raw_event?: string;
}

export interface AttackGraphNode {
  id: string;
  label: string;
  type: 'incident' | 'event' | 'host' | 'user' | 'ip' | 'process' | 'finding';
  severity: string;
  risk_score: number;
  metadata?: Record<string, any>;
}

export interface AttackGraphEdge {
  source: string;
  target: string;
  relation: string;
}

export interface AttackGraphData {
  node_count: number;
  edge_count: number;
  nodes: AttackGraphNode[];
  edges: AttackGraphEdge[];
}

export interface SOCStats {
  total_events: number;
  total_findings: number;
  total_incidents: number;
  active_sources: number;
  severity_distribution: Record<string, number>;
  recent_incidents: Incident[];
}

export interface BenchmarkMetrics {
  precision: number;
  recall: number;
  f1_score: number;
  false_positive_rate: number;
  false_negative_rate: number;
  confusion_matrix: {
    tn: number;
    fp: number;
    fn: number;
    tp: number;
  };
  latency_total_ms: number;
  latency_per_event_ms: number;
}

export interface BenchmarkReport {
  evaluation_timestamp: string;
  split_info: {
    total_dataset_size: number;
    train_samples: number;
    val_samples: number;
    held_out_test_samples: number;
    test_benign_count: number;
    test_attack_count: number;
  };
  results: {
    rule_based: BenchmarkMetrics;
    machine_learning: BenchmarkMetrics;
    hybrid_graph_correlated: BenchmarkMetrics;
  };
  correlation_summary: {
    total_findings_pre_correlation: number;
    total_incidents_post_correlation: number;
    alert_compression_ratio: number;
    campaign_reconstruction_rate: number;
  };
}

export interface ThreatIndicator {
  id?: string;
  indicator_type: 'ip' | 'domain' | 'hash';
  value: string;
  threat_type: string;
  severity: string;
  confidence: number;
  source: string;
  description?: string;
}

export interface ResponseExecution {
  id: string;
  incident_id?: string;
  action_type: string;
  target: string;
  status: 'pending_approval' | 'approved' | 'executed' | 'failed' | 'rolled_back';
  dry_run: boolean;
  executed_by: string;
  approved_by?: string;
  created_at: string;
  result_details: Record<string, any>;
}
