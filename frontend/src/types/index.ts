export interface User {
  id: string;
  email: string;
  full_name: string;
  role_id: string;
  organization_id: string;
}

export interface Document {
  id: string;
  organization_id?: string;
  uploaded_by?: string;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  processing_status: 'PENDING' | 'UPLOADED' | 'PROCESSING' | 'PROCESSED' | 'FAILED';
  metadata?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface DocumentSource {
  field?: string;
  value?: string;
  source?: {
    page?: number;
    section?: string;
    paragraph?: number;
  };
}

export interface DocumentAnalysisData {
  document_id: string;
  document_type: string;
  title: string;
  summary: string;
  key_points: string[];
  entities: Record<string, any>;
  structured_data: Record<string, any>;
  sources: DocumentSource[];
  confidence: number;
  needs_ocr: boolean;
  warnings: string[];
  execution_time_ms?: number;
}


export interface Approval {
  id: string;
  action_type: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  reason: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  created_at: string;
}
