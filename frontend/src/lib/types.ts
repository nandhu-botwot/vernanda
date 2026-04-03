export interface Call {
  id: string;
  filename: string;
  file_size_bytes: number;
  duration_seconds: number | null;
  status: CallStatus;
  error_message: string | null;
  agent_name: string | null;
  call_language: string;
  call_type: string | null;
  transcript: string | null;
  whisper_confidence: number | null;
  stt_engine_used: string | null;
  created_at: string;
  updated_at: string;
}

export type CallStatus =
  | "UPLOADED"
  | "PREPROCESSING"
  | "TRANSCRIBING"
  | "EVALUATING"
  | "COMPLETED"
  | "FAILED";

export interface CallListItem {
  id: string;
  filename: string;
  duration_seconds: number | null;
  status: CallStatus;
  agent_name: string | null;
  call_language: string;
  call_type: string | null;
  total_score: number | null;
  grade: string | null;
  created_at: string;
}

export interface CallListResponse {
  calls: CallListItem[];
  total: number;
  page: number;
  limit: number;
}

export interface ParameterScore {
  score: number;
  max_score: number;
  method: string;
  evidence: string[];
  feedback: string;
  improvement: string;
  label?: string;
}

export interface QAReport {
  id: string;
  call_id: string;
  total_score: number;
  grade: string;
  scores: Record<string, ParameterScore>;
  strengths: string[] | null;
  weaknesses: string[] | null;
  critical_issues: string[] | null;
  improvements: string | null;
  call_summary: string | null;
  llm_model: string | null;
  prompt_version: string | null;
  rule_engine_version: string | null;
  eval_duration_ms: number | null;
  created_at: string;
}

export interface AgentStats {
  agent_name: string;
  total_calls: number;
  avg_score: number;
  best_score: number;
  worst_score: number;
  avg_grade: string;
}

export interface ParameterStats {
  parameter: string;
  avg_score: number;
  max_possible: number;
  avg_percentage: number;
}

export interface AnalyticsSummary {
  total_calls: number;
  total_evaluated: number;
  avg_score: number;
  grade_distribution: Record<string, number>;
}
