import {
  DocumentItem,
  DocumentDetail,
  CollectionItem,
  ConversationItem,
  MessageItem,
  VerificationClaimItem,
  ConflictItem,
  ActivityItem,
  AnalyticsSummary,
  ConflictReviewStatus
} from "../types";

const API_BASE = "/api";

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    Accept: "application/json",
    ...options.headers,
  };

  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    let errorDetail = "An unexpected server error occurred.";
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {
      errorDetail = `Request failed with status ${res.status}`;
    }
    throw new Error(errorDetail);
  }
  return res.json() as Promise<T>;
}

// Documents API
export async function fetchDocuments(
  query?: string,
  statusFilter?: string,
  collectionId?: string
): Promise<DocumentItem[]> {
  const params = new URLSearchParams();
  if (query) params.append("query", query);
  if (statusFilter && statusFilter !== "ALL") params.append("status_filter", statusFilter);
  if (collectionId && collectionId !== "ALL") params.append("collection_id", collectionId);
  return request<DocumentItem[]>(`/documents/?${params.toString()}`);
}

export async function uploadDocument(
  file: File,
  collectionId?: string
): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append("file", file);
  if (collectionId && collectionId !== "none") {
    formData.append("collection_id", collectionId);
  }

  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function fetchDocumentDetail(id: string): Promise<DocumentDetail> {
  return request<DocumentDetail>(`/documents/${id}`);
}

export async function deleteDocument(id: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/documents/${id}`, { method: "DELETE" });
}

export async function reprocessDocument(id: string): Promise<DocumentItem> {
  return request<DocumentItem>(`/documents/${id}/reprocess`, { method: "POST" });
}

// Collections API
export async function fetchCollections(): Promise<CollectionItem[]> {
  return request<CollectionItem[]>("/collections/");
}

export async function createCollection(
  name: string,
  description?: string
): Promise<CollectionItem> {
  return request<CollectionItem>("/collections/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description }),
  });
}

// Chat API
export async function fetchConversations(): Promise<ConversationItem[]> {
  return request<ConversationItem[]>("/chat/conversations");
}

export async function createConversation(
  title?: string,
  documentId?: string,
  collectionId?: string
): Promise<ConversationItem> {
  return request<ConversationItem>("/chat/conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, document_id: documentId, collection_id: collectionId }),
  });
}

export async function fetchConversation(id: string): Promise<ConversationItem> {
  return request<ConversationItem>(`/chat/conversations/${id}`);
}

export async function sendMessage(
  conversationId: string,
  content: string,
  documentId?: string,
  collectionId?: string
): Promise<MessageItem> {
  return request<MessageItem>(`/chat/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      content,
      document_id: documentId,
      collection_id: collectionId,
      enable_verification: true,
    }),
  });
}

export async function sendFeedback(
  messageId: string,
  rating: "positive" | "negative",
  comment?: string
): Promise<{ message: string }> {
  return request<{ message: string }>(`/chat/messages/${messageId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rating, comment }),
  });
}

export async function fetchSuggestedQuestions(): Promise<string[]> {
  return request<string[]>("/chat/suggested_questions");
}

// Verification API
export async function fetchVerifiedClaims(statusFilter?: string): Promise<VerificationClaimItem[]> {
  const params = new URLSearchParams();
  if (statusFilter && statusFilter !== "ALL") params.append("status_filter", statusFilter);
  return request<VerificationClaimItem[]>(`/verification/claims?${params.toString()}`);
}

export async function verifyCustomClaim(
  claimText: string,
  documentId?: string
): Promise<VerificationClaimItem> {
  return request<VerificationClaimItem>("/verification/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ claim_text: claimText, document_id: documentId }),
  });
}

// Conflicts API
export async function fetchConflicts(statusFilter?: string): Promise<ConflictItem[]> {
  const params = new URLSearchParams();
  if (statusFilter && statusFilter !== "ALL") params.append("status_filter", statusFilter);
  return request<ConflictItem[]>(`/conflicts/?${params.toString()}`);
}

export async function detectConflicts(): Promise<ConflictItem[]> {
  return request<ConflictItem[]>("/conflicts/detect", { method: "POST" });
}

export async function updateConflictStatus(
  conflictId: string,
  reviewStatus: ConflictReviewStatus,
  resolutionNotes?: string
): Promise<ConflictItem> {
  return request<ConflictItem>(`/conflicts/${conflictId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      review_status: reviewStatus,
      resolution_notes: resolutionNotes,
    }),
  });
}

// Analytics API
export async function fetchAnalyticsSummary(): Promise<AnalyticsSummary> {
  return request<AnalyticsSummary>("/analytics/summary");
}

// Activity API
export async function fetchActivities(
  eventType?: string,
  statusFilter?: string
): Promise<ActivityItem[]> {
  const params = new URLSearchParams();
  if (eventType && eventType !== "ALL") params.append("event_type", eventType);
  if (statusFilter && statusFilter !== "ALL") params.append("status_filter", statusFilter);
  return request<ActivityItem[]>(`/activity/?${params.toString()}`);
}
