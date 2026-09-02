export interface User {
  id: string;
  email: string;
  full_name: string;
  role_id: string;
  organization_id: string;
}

export interface Document {
  id: string;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  processing_status: string;
  created_at: string;
}

export interface Approval {
  id: string;
  action_type: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  reason: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  created_at: string;
}
