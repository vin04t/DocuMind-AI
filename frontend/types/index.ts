export type DocumentStatus =
  | "UPLOADED"
  | "EXTRACTING"
  | "CHUNKING"
  | "EMBEDDING"
  | "INDEXED"
  | "FAILED";

export interface DocumentItem {
  id: string;
  filename: string;
  file_size: number;
  page_count: number;
  status: DocumentStatus;
  error_message?: string;
  is_scanned: boolean;
  collection_id?: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentChunkItem {
  id: string;
  document_id: string;
  chunk_index: number;
  page_number: number;
  content: string;
  token_count: number;
}

export interface DocumentDetail extends DocumentItem {
  chunks: DocumentChunkItem[];
}

export interface CollectionItem {
  id: string;
  name: string;
  description?: string;
  document_count: number;
  created_at: string;
}

export interface CitationItem {
  id: string;
  document_id: string;
  document_name?: string;
  page_number: number;
  chunk_id?: string;
  snippet: string;
  confidence_score: number;
}

export type VerificationStatus =
  | "SUPPORTED"
  | "PARTIALLY_SUPPORTED"
  | "CONTRADICTED"
  | "NOT_SUPPORTED";

export interface VerificationClaimItem {
  id: string;
  claim_text: string;
  status: VerificationStatus;
  document_id?: string;
  document_name?: string;
  page_number?: number;
  supporting_passage?: string;
  rationale?: string;
  confidence_score: number;
}

export interface MessageItem {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  retrieval_latency_ms: number;
  answer_latency_ms: number;
  citations: CitationItem[];
  verification_claims: VerificationClaimItem[];
  created_at: string;
}

export interface ConversationItem {
  id: string;
  title: string;
  document_id?: string;
  collection_id?: string;
  created_at: string;
  updated_at: string;
  messages: MessageItem[];
}

export type ConflictReviewStatus =
  | "NEEDS_INVESTIGATION"
  | "REVIEWED"
  | "RESOLVED";

export interface ConflictItem {
  id: string;
  document_a_id: string;
  document_a_name: string;
  page_a: number;
  statement_a: string;
  passage_a: string;

  document_b_id: string;
  document_b_name: string;
  page_b: number;
  statement_b: string;
  passage_b: string;

  conflict_type: string;
  explanation: string;
  review_status: ConflictReviewStatus;
  resolution_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface ActivityItem {
  id: string;
  event_type: string;
  status: "SUCCESS" | "FAILED" | "PENDING" | "WARNING";
  document_id?: string;
  document_name?: string;
  message_id?: string;
  duration_ms: number;
  details_json?: string;
  created_at: string;
}

export interface AnalyticsSummary {
  total_documents: number;
  indexed_pages: number;
  total_questions: number;
  total_collections: number;
  avg_retrieval_latency_ms: number;
  avg_answer_latency_ms: number;
  evidence_coverage_percentage: number;
  verification_stats: {
    supported: number;
    partially_supported: number;
    contradicted: number;
    not_supported: number;
  };
  queries_over_time: Array<{ date: string; count: number }>;
  latency_trends: Array<{ date: string; avg_retrieval_ms: number; avg_answer_ms: number }>;
  frequently_queried_documents: Array<{
    id: string;
    filename: string;
    queries_count: number;
    status: string;
  }>;
}
