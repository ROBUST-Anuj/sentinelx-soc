import type { 
  SOCStats, Incident, CanonicalEvent, DetectionFinding, 
  AttackGraphData, BenchmarkReport, ThreatIndicator, ResponseExecution 
} from '../types/soc';
import { 
  DEMO_BENCHMARK_REPORT, INITIAL_DEMO_INCIDENTS, DEMO_FINDINGS_MAP, 
  DEMO_EVIDENCE_EVENTS, DEMO_ATTACK_GRAPHS, INITIAL_DEMO_THREAT_INDICATORS, 
  INITIAL_DEMO_RESPONSE_HISTORY 
} from './demoData';

class DemoStorage {
  private incidents: Incident[];
  private threatIndicators: ThreatIndicator[];
  private responseHistory: ResponseExecution[];
  private events: CanonicalEvent[];

  constructor() {
    this.incidents = [...INITIAL_DEMO_INCIDENTS];
    this.threatIndicators = [...INITIAL_DEMO_THREAT_INDICATORS];
    this.responseHistory = [...INITIAL_DEMO_RESPONSE_HISTORY];
    this.events = [...DEMO_EVIDENCE_EVENTS];
  }

  public async getStats(): Promise<SOCStats> {
    const severityCount: Record<string, number> = { critical: 0, high: 0, medium: 0, low: 0, informational: 0 };
    this.incidents.forEach(inc => {
      severityCount[inc.severity] = (severityCount[inc.severity] || 0) + 1;
    });

    return {
      total_events: 1000,
      total_findings: 56,
      total_incidents: this.incidents.length,
      active_sources: 4,
      severity_distribution: severityCount,
      recent_incidents: [...this.incidents],
    };
  }

  public async getEvents(limit: number = 50, offset: number = 0, sourceType?: string): Promise<CanonicalEvent[]> {
    let filtered = [...this.events];
    if (sourceType) {
      filtered = filtered.filter(e => e.source_type.toLowerCase() === sourceType.toLowerCase());
    }
    return filtered.slice(offset, offset + limit);
  }

  public async getIncidents(): Promise<Incident[]> {
    return [...this.incidents];
  }

  public async getIncidentDetail(id: string): Promise<{ incident: Incident; findings: DetectionFinding[]; evidence_events: CanonicalEvent[] }> {
    const inc = this.incidents.find(i => i.id === id) || this.incidents[0];
    const findings = DEMO_FINDINGS_MAP[inc.id] || DEMO_FINDINGS_MAP["INC-2026-001"];
    const evidence = this.events.slice(0, 3);
    return {
      incident: inc,
      findings,
      evidence_events: evidence,
    };
  }

  public async updateIncidentStatus(id: string, status: string): Promise<{ status: string; new_status: string }> {
    const inc = this.incidents.find(i => i.id === id);
    if (inc) {
      inc.status = status as any;
    }
    return { status: "success", new_status: status };
  }

  public async getAttackGraph(incidentId: string): Promise<AttackGraphData> {
    const graph = DEMO_ATTACK_GRAPHS[incidentId] || DEMO_ATTACK_GRAPHS["INC-2026-001"];
    return graph;
  }

  public async runBenchmark(_nEvents: number = 1000): Promise<BenchmarkReport> {
    return DEMO_BENCHMARK_REPORT;
  }

  public async getThreatIndicators(): Promise<ThreatIndicator[]> {
    return [...this.threatIndicators];
  }

  public async addThreatIndicator(indicator: ThreatIndicator): Promise<any> {
    const newIndicator: ThreatIndicator = {
      ...indicator,
      id: `ioc-demo-${Date.now()}`,
    };
    this.threatIndicators.unshift(newIndicator);
    return { status: "created", indicator: newIndicator };
  }

  public async executeResponse(payload: { action_type: string; target: string; dry_run: boolean; incident_id?: string }): Promise<any> {
    const execution: ResponseExecution = {
      id: `RESP-DEMO-${Date.now()}`,
      incident_id: payload.incident_id,
      action_type: payload.action_type,
      target: payload.target,
      status: "executed",
      dry_run: true,
      executed_by: "demo_analyst",
      approved_by: "demo_policy_engine",
      created_at: new Date().toISOString(),
      result_details: {
        action: payload.action_type,
        simulated: true,
        target: payload.target,
        message: `[DEMO SIMULATION] Action '${payload.action_type}' safely applied to '${payload.target}'. No real infrastructure touched.`,
        duration_ms: Math.floor(Math.random() * 30 + 15),
      },
    };
    this.responseHistory.unshift(execution);
    return {
      status: "success",
      execution_id: execution.id,
      dry_run: true,
      message: execution.result_details.message,
    };
  }

  public async getResponseHistory(): Promise<ResponseExecution[]> {
    return [...this.responseHistory];
  }

  public async uploadTelemetry(sourceType: string, sourceName: string, file: File): Promise<any> {
    const newEvent: CanonicalEvent = {
      event_id: `EVT-DEMO-${Date.now()}`,
      timestamp: new Date().toISOString(),
      source_type: sourceType,
      source_name: sourceName,
      event_type: `Demo Ingested File: ${file.name}`,
      severity: "medium",
      raw_event: `Simulated file upload: ${file.name} (${file.size} bytes)`,
    };
    this.events.unshift(newEvent);
    return {
      status: "success",
      events_ingested: 1,
      message: `[DEMO] Simulated parsing and ingestion of ${file.name}. Added 1 synthetic event.`,
    };
  }
}

export const demoStorage = new DemoStorage();
