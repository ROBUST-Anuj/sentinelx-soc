export interface BankAccount {
  id: string;
  user_id: string;
  account_number: string;
  account_type: 'checking' | 'savings' | 'merchant';
  currency: string;
  balance_minor: number;
  balance_formatted: string;
  status: 'active' | 'frozen' | 'suspended' | 'closed';
  is_synthetic: boolean;
  created_at: string;
}

export interface Beneficiary {
  id: string;
  name: string;
  account_number: string;
  bank_name: string;
  risk_category: 'trusted' | 'standard' | 'restricted';
}

export type TransferStatus = 
  | 'CREATED'
  | 'ASSESSING'
  | 'AWAITING_VERIFICATION'
  | 'HELD'
  | 'APPROVED'
  | 'POSTED'
  | 'BLOCKED'
  | 'REJECTED'
  | 'EXPIRED'
  | 'FAILED';

export interface TransferResult {
  id: string;
  idempotency_key: string;
  source_account_id: string;
  destination_account_id: string;
  amount_minor: number;
  amount_formatted: string;
  currency: string;
  status: TransferStatus;
  policy_decision?: 'ALLOW' | 'VERIFY' | 'HOLD' | 'BLOCK';
  created_at: string;
  verification_challenge_id?: string;
  mock_challenge_code?: string;
  customer_message?: string;
}

export interface LedgerEntry {
  id: string;
  transaction_id: string;
  account_id: string;
  entry_type: 'DEBIT' | 'CREDIT';
  amount_minor: number;
  currency: string;
  balance_after_minor: number;
  description?: string;
  created_at: string;
}

export interface UserSession {
  username: string;
  token: string;
  role: string;
}
