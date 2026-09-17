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

export interface ImageArtifact {
  id: string;
  organization_id?: string;
  uploaded_by?: string;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  width: number;
  height: number;
  processing_status: string;
  created_at?: string;
}

export interface VisionDetection {
  label: string;
  confidence: number;
  bbox?: number[];
  description?: string;
}

export interface OCRRegion {
  text: string;
  confidence: number;
  bbox?: number[];
}

export interface OCRResultData {
  text: string;
  confidence: number;
  status: string;
  regions: OCRRegion[];
  error?: string;
}

export interface VisualFindingData {
  title: string;
  description: string;
  severity?: 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence: number;
  bbox?: number[];
  category?: string;
}

export interface VisionCitationData {
  citation_id: string;
  source_type: 'bounding_box' | 'ocr_region' | 'visual_finding' | 'image_region';
  label: string;
  confidence: number;
  bbox?: number[];
  text?: string;
  details?: string;
}

export interface VisionComponentStatuses {
  vision_model: string;
  ocr: string;
  object_detection: string;
}

export interface VisionAnalysisData {
  request_id: string;
  image_id: string;
  task_type: string;
  question: string;
  summary: string;
  answer: string;
  findings: VisualFindingData[];
  detected_objects: VisionDetection[];
  ocr_result: OCRResultData;
  citations: VisionCitationData[];
  confidence: number;
  image_metadata: {
    width?: number;
    height?: number;
    format?: string;
    size_bytes?: number;
    channels?: number;
  };
  component_statuses: VisionComponentStatuses;
  warnings: string[];
  execution_time_ms?: number;
}

