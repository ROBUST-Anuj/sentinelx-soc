import axios from 'axios';
import { BankAccount, TransferResult, LedgerEntry } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://sentinelx-api-316t.onrender.com';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('nexabank_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const api = {
  // Authentication
  async login(username: string, password: string):Promise<{ access_token: string; token_type: string; role: string }> {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    const resp = await apiClient.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    return resp.data;
  },

  // Accounts
  async getAccounts(): Promise<BankAccount[]> {
    const resp = await apiClient.get<BankAccount[]>('/api/banking/accounts');
    return resp.data;
  },

  async getAccountDetail(accountId: string): Promise<BankAccount> {
    const resp = await apiClient.get<BankAccount>(`/api/banking/accounts/${accountId}`);
    return resp.data;
  },

  async getLedger(accountId: string): Promise<LedgerEntry[]> {
    const resp = await apiClient.get<LedgerEntry[]>(`/api/banking/accounts/${accountId}/ledger`);
    return resp.data;
  },

  // Transfers
  async initiateTransfer(params: {
    source_account_id: string;
    destination_account_number: string;
    amount_minor: number;
    currency?: string;
    description?: string;
    idempotency_key: string;
  }): Promise<TransferResult> {
    const resp = await apiClient.post<TransferResult>('/api/banking/transfers', {
      source_account_id: params.source_account_id,
      destination_account_number: params.destination_account_number,
      amount_minor: params.amount_minor,
      currency: params.currency || 'INR',
      description: params.description || 'NexaBank Transfer',
      idempotency_key: params.idempotency_key,
    });
    return resp.data;
  },

  // Step-up OTP Verification
  async submitVerification(transferId: string, verificationCode: string): Promise<TransferResult> {
    const resp = await apiClient.post<TransferResult>(`/api/banking/transfers/${transferId}/verify`, {
      verification_code: verificationCode,
    });
    return resp.data;
  },

  // Transfer history
  async getTransfers(): Promise<TransferResult[]> {
    const resp = await apiClient.get<TransferResult[]>('/api/banking/transfers');
    return resp.data;
  },

  // Security Telemetry
  async submitTelemetry(payload: {
    event_type: string;
    category: string;
    session_id?: string;
    transaction_id?: string;
    device_id?: string;
    source_application?: string;
    event_metadata?: Record<string, any>;
    is_simulation?: boolean;
  }): Promise<any> {
    const resp = await apiClient.post('/api/banking/security/events', payload);
    return resp.data;
  }
};
