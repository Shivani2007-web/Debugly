// Mirrors backend app/models/misconception.py (the subset the frontend needs).

export type EvidenceSource = "code" | "error" | "behavior";

export interface Evidence {
  source: EvidenceSource;
  weight: number;
  detail: string;
  line: number | null;
  error_type: string | null;
}

export interface DetectedMisconception {
  concept: string;
  misconception_key: string;
  misconception: string;
  confidence: number;
  evidence: Evidence[];
  lines: number[];
  error_type: string | null;
}

export interface DiagnosisResult {
  misconceptions: DetectedMisconception[];
  analyzed_lines: number;
  had_execution_evidence: boolean;
}
