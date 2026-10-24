import axios from 'axios';
import type { AxiosInstance } from 'axios';
import type { 
  SOCStats, Incident, CanonicalEvent, DetectionFinding, 
  AttackGraphData, BenchmarkReport, ThreatIndicator, ResponseExecution,
  BankAccount, Transfer, TransferCreatePayload, VerificationSubmitPayload
} from '../types/soc';

export function getApiBaseUrl(): string {
  // If production environment variable is defined (e.g. on Vercel deployment)
  const envApiUrl = import.meta.env.VITE_API_BASE_URL;
  if (envApiUrl && typeof envApiUrl === 'string' && envApiUrl.trim().length > 0) {
    const cleanUrl = envApiUrl.trim().replace(/\/$/, '');
    return cleanUrl.endsWith('/api') ? cleanUrl : cleanUrl + '/api';
  }

  // If running locally in browser, dynamically connect to backend port 8888 (Docker) or 8000 (Local)
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname || 'localhost';
    if (window.location.port === '3000') {
      return `http://${hostname}:8888/api`;
    }
    return `http://${hostname}:8000/api`;
  }
  return 'http://localhost:8888/api';
}

class ApiService {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: getApiBaseUrl(),
      timeout: 15000,
    });

    // Check stored token
    const stored = localStorage.getItem('sentinelx_token');
    if (stored) {
      this.token = stored;
      this.client.defaults.headers.common['Authorization'] = `Bearer ${stored}`;
    }
  }

  public setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('sentinelx_token', token);
      this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      localStorage.removeItem('sentinelx_token');
      delete this.client.defaults.headers.common['Authorization'];
    }
  }

  public getToken(): string | null {
    return this.token;
  }

  public async login(username: string, password: string): Promise<{ access_token: string; role: string; username: string }> {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    const res = await this.client.post('/auth/login', formData);
    this.setToken(res.data.access_token);
    return res.data;
  }

  public logout() {
    this.setToken(null);
  }

  public async getStats(): Promise<SOCStats> {
    const res = await this.client.get('/overview/stats');
    return res.data;
  }

  public async getEvents(limit: number = 50, offset: number = 0, sourceType?: string): Promise<CanonicalEvent[]> {
    const params: any = { limit, offset };
    if (sourceType) params.source_type = sourceType;
    const res = await this.client.get('/events', { params });
    return res.data;
  }

  public async getIncidents(): Promise<Incident[]> {
    const res = await this.client.get('/incidents');
    return res.data;
  }

  public async getIncidentDetail(id: string): Promise<{ incident: Incident; findings: DetectionFinding[]; evidence_events: CanonicalEvent[] }> {
    const res = await this.client.get(`/incidents/${id}`);
    return res.data;
  }

  public async updateIncidentStatus(id: string, status: string): Promise<{ status: string; new_status: string }> {
    const res = await this.client.patch(`/incidents/${id}/status?status=${status}`);
    return res.data;
  }

  public async getAttackGraph(incidentId: string): Promise<AttackGraphData> {
    const res = await this.client.get(`/graph/incident/${incidentId}`);
    return res.data;
  }

  public async runBenchmark(nEvents: number = 1000): Promise<BenchmarkReport> {
    const res = await this.client.post(`/evaluation/run-benchmark?n_events=${nEvents}`);
    return res.data;
  }

  public async getThreatIndicators(): Promise<ThreatIndicator[]> {
    const res = await this.client.get('/threat-intel');
    return res.data;
  }

  public async addThreatIndicator(indicator: ThreatIndicator): Promise<any> {
    const res = await this.client.post('/threat-intel', indicator);
    return res.data;
  }

  public async executeResponse(payload: { action_type: string; target: string; dry_run: boolean; incident_id?: string }): Promise<any> {
    const res = await this.client.post('/response/execute', payload);
    return res.data;
  }

  public async getResponseHistory(): Promise<ResponseExecution[]> {
    const res = await this.client.get('/response/history');
    return res.data;
  }

  public async uploadTelemetry(sourceType: string, sourceName: string, file: File): Promise<any> {
    const formData = new FormData();
    formData.append('source_type', sourceType);
    formData.append('source_name', sourceName);
    formData.append('file', file);
    const res = await this.client.post('/ingestion/upload', formData);
    return res.data;
  }

  public async getBankAccounts(): Promise<BankAccount[]> {
    const res = await this.client.get('/banking/accounts');
    return res.data;
  }

  public async getBankAccount(id: string): Promise<BankAccount> {
    const res = await this.client.get('/banking/accounts/' + id);
    return res.data;
  }

  public async createTransfer(payload: TransferCreatePayload): Promise<Transfer> {
    const res = await this.client.post('/banking/transfers', payload);
    return res.data;
  }

  public async verifyTransferChallenge(transferId: string, payload: VerificationSubmitPayload): Promise<Transfer> {
    const res = await this.client.post('/banking/transfers/' + transferId + '/verify', payload);
    return res.data;
  }

  public async getTransfers(accountId?: string): Promise<Transfer[]> {
    const url = accountId ? '/banking/transfers?account_id=' + accountId : '/banking/transfers';
    const res = await this.client.get(url);
    return res.data;
  }

  public async getTransferDetail(id: string): Promise<Transfer> {
    const res = await this.client.get('/banking/transfers/' + id);
    return res.data;
  }
}

export const api = new ApiService();
