"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Brain,
  Send,
  Sparkles,
  Files,
  FileText,
  Search,
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Copy,
  Check,
  ThumbsUp,
  ThumbsDown,
  RotateCw,
  ExternalLink,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Loader2,
  Plus
} from "lucide-react";
import {
  fetchDocuments,
  fetchDocumentDetail,
  fetchConversations,
  createConversation,
  fetchConversation,
  sendMessage,
  sendFeedback,
  fetchSuggestedQuestions
} from "../../services/api";
import {
  DocumentItem,
  DocumentDetail,
  ConversationItem,
  MessageItem,
  CitationItem,
  VerificationClaimItem
} from "../../types";

interface IntelligenceProps {
  initialDocId?: string | null;
}

export const IntelligenceWorkspace: React.FC<IntelligenceProps> = ({ initialDocId }) => {
  // State for Documents & Viewer (LEFT PANEL)
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [activeDocId, setActiveDocId] = useState<string | null>(null);
  const [activeDocDetail, setActiveDocDetail] = useState<DocumentDetail | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [zoomLevel, setZoomLevel] = useState<number>(100);
  const [pdfSearchText, setPdfSearchText] = useState<string>("");
  const [highlightedSnippet, setHighlightedSnippet] = useState<string | null>(null);

  // State for Chat & Intelligence (RIGHT PANEL)
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [inputText, setInputText] = useState("");
  const [sending, setSending] = useState(false);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const [copiedMsgId, setCopiedMsgId] = useState<string | null>(null);
  const [feedbackSent, setFeedbackSent] = useState<Record<string, "positive" | "negative">>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 1. Initial Load: Documents, Conversations, Suggestions
  useEffect(() => {
    async function init() {
      try {
        const [docs, convs, suggestions] = await Promise.all([
          fetchDocuments(),
          fetchConversations(),
          fetchSuggestedQuestions(),
        ]);
        setDocuments(docs);
        setConversations(convs);
        setSuggestedQuestions(suggestions);

        // Set initial document
        const initialDoc = initialDocId || (docs.length > 0 ? docs[0].id : null);
        if (initialDoc) {
          setActiveDocId(initialDoc);
        }

        // Set or create initial conversation
        if (convs.length > 0) {
          setActiveConversationId(convs[0].id);
        } else {
          const newConv = await createConversation("Research Session", initialDoc || undefined);
          setConversations([newConv]);
          setActiveConversationId(newConv.id);
        }
      } catch (err) {
        console.error("Initialization error:", err);
      }
    }
    init();
  }, [initialDocId]);

  // 2. Load Active Document Details when activeDocId changes
  useEffect(() => {
    if (!activeDocId) return;
    async function loadDoc() {
      try {
        const detail = await fetchDocumentDetail(activeDocId!);
        setActiveDocDetail(detail);
      } catch (err) {
        console.error("Error loading document detail:", err);
      }
    }
    loadDoc();
  }, [activeDocId]);

  // 3. Load Active Conversation Messages
  useEffect(() => {
    if (!activeConversationId) return;
    async function loadConv() {
      try {
        const conv = await fetchConversation(activeConversationId!);
        setMessages(conv.messages || []);
      } catch (err) {
        console.error("Error loading conversation:", err);
      }
    }
    loadConv();
  }, [activeConversationId]);

  // Auto-scroll chat to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Handle New Conversation
  const handleNewConversation = async () => {
    try {
      const conv = await createConversation("New Research Session", activeDocId || undefined);
      setConversations([conv, ...conversations]);
      setActiveConversationId(conv.id);
      setMessages([]);
    } catch (err) {
      console.error("Error creating conversation:", err);
    }
  };

  // Handle Sending Message
  const handleSendMessage = async (textToSend?: string) => {
    const q = textToSend || inputText;
    if (!q.trim() || sending || !activeConversationId) return;

    setInputText("");
    setSending(true);

    // Optimistic user message
    const tempUserMsg: MessageItem = {
      id: "temp-" + Date.now(),
      conversation_id: activeConversationId,
      role: "user",
      content: q,
      retrieval_latency_ms: 0,
      answer_latency_ms: 0,
      citations: [],
      verification_claims: [],
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      const asstMsg = await sendMessage(activeConversationId, q, activeDocId || undefined);
      setMessages(prev => [...prev.filter(m => m.id !== tempUserMsg.id), tempUserMsg, asstMsg]);
    } catch (err: any) {
      const errorMsg: MessageItem = {
        id: "err-" + Date.now(),
        conversation_id: activeConversationId,
        role: "assistant",
        content: `Error generating grounded answer: ${err.message}`,
        retrieval_latency_ms: 0,
        answer_latency_ms: 0,
        citations: [],
        verification_claims: [],
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setSending(false);
    }
  };

  // Handle Citation Click -> Navigate Left Panel PDF Viewer!
  const handleCitationClick = (citation: CitationItem) => {
    if (citation.document_id && citation.document_id !== activeDocId) {
      setActiveDocId(citation.document_id);
    }
    if (citation.page_number) {
      setCurrentPage(citation.page_number);
    }
    if (citation.snippet) {
      setHighlightedSnippet(citation.snippet);
      // Automatically clear highlight after 8 seconds
      setTimeout(() => setHighlightedSnippet(null), 8000);
    }
  };

  // Copy Answer
  const handleCopy = (msgId: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedMsgId(msgId);
    setTimeout(() => setCopiedMsgId(null), 2000);
  };

  // Feedback
  const handleFeedback = async (msgId: string, rating: "positive" | "negative") => {
    setFeedbackSent(prev => ({ ...prev, [msgId]: rating }));
    try {
      await sendFeedback(msgId, rating);
    } catch (err) {
      console.error("Feedback failed:", err);
    }
  };

  // Filter page chunks for current page in PDF text view
  const currentPageChunks = activeDocDetail?.chunks.filter(
    c => c.page_number === currentPage
  ) || [];

  return (
    <div className="flex flex-col lg:flex-row h-[calc(100vh-3.5rem)] w-full overflow-hidden">
      {/* ========================================================= */}
      {/* LEFT PANEL: PDF VIEWER & EVIDENCE NAVIGATION */}
      {/* ========================================================= */}
      <div className="w-full lg:w-1/2 flex flex-col border-b lg:border-b-0 lg:border-r border-slate-800/80 bg-[#0A0E18] h-1/2 lg:h-full">
        {/* Viewer Top Toolbar */}
        <div className="h-12 border-b border-slate-800/80 bg-[#0D1322] px-3 flex items-center justify-between gap-2 flex-shrink-0">
          {/* Document Selector */}
          <div className="flex items-center space-x-2 truncate flex-1 max-w-xs sm:max-w-sm">
            <FileText className="h-4 w-4 text-indigo-400 flex-shrink-0" />
            <select
              value={activeDocId || ""}
              onChange={(e) => {
                setActiveDocId(e.target.value);
                setCurrentPage(1);
                setHighlightedSnippet(null);
              }}
              className="bg-slate-900 border border-slate-700/80 text-xs text-slate-200 rounded px-2 py-1 truncate focus:outline-none focus:border-indigo-500 max-w-[220px]"
            >
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.filename} ({doc.page_count} pgs)
                </option>
              ))}
            </select>
          </div>

          {/* Page Controls & Zoom */}
          <div className="flex items-center space-x-1.5 text-xs text-slate-300">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage <= 1}
              className="p-1 rounded hover:bg-slate-800 disabled:opacity-30 transition"
              title="Previous Page"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="font-mono text-[11px] px-1">
              Page {currentPage} of {activeDocDetail?.page_count || 1}
            </span>
            <button
              onClick={() => setCurrentPage(Math.min(activeDocDetail?.page_count || 1, currentPage + 1))}
              disabled={currentPage >= (activeDocDetail?.page_count || 1)}
              className="p-1 rounded hover:bg-slate-800 disabled:opacity-30 transition"
              title="Next Page"
            >
              <ChevronRight className="h-4 w-4" />
            </button>

            <div className="h-4 w-[1px] bg-slate-700 mx-1" />

            <button
              onClick={() => setZoomLevel(Math.max(70, zoomLevel - 15))}
              className="p-1 rounded hover:bg-slate-800 transition"
              title="Zoom Out"
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </button>
            <span className="font-mono text-[11px]">{zoomLevel}%</span>
            <button
              onClick={() => setZoomLevel(Math.min(150, zoomLevel + 15))}
              className="p-1 rounded hover:bg-slate-800 transition"
              title="Zoom In"
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* Viewer In-Document Search Bar */}
        <div className="px-3 py-1.5 bg-[#0B0F1A] border-b border-slate-800/60 flex items-center justify-between text-xs">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2.5 top-2 h-3 w-3 text-slate-400" />
            <input
              type="text"
              value={pdfSearchText}
              onChange={(e) => setPdfSearchText(e.target.value)}
              placeholder="Find in page text..."
              className="w-full pl-7 pr-2 py-1 rounded bg-slate-900/90 border border-slate-800 text-[11px] text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
          {highlightedSnippet && (
            <span className="text-[10px] text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 font-medium">
              Evidence Passage Active
            </span>
          )}
        </div>

        {/* Viewer Document Surface */}
        <div className="flex-1 overflow-y-auto p-4 flex justify-center bg-[#070A12]">
          <div
            style={{ width: `${Math.round(595 * (zoomLevel / 100))}px` }}
            className="min-h-[700px] bg-[#0F172A] border border-slate-700/80 rounded-lg shadow-2xl p-6 sm:p-8 flex flex-col justify-between transition-all"
          >
            {/* Page Header */}
            <div>
              <div className="border-b border-slate-700/60 pb-3 mb-4 flex items-center justify-between text-[11px] text-slate-400 font-mono">
                <span className="truncate max-w-[280px] font-medium text-slate-300">
                  {activeDocDetail?.filename || "Loading document..."}
                </span>
                <span>Page {currentPage} of {activeDocDetail?.page_count || 1}</span>
              </div>

              {/* Extracted Page Content with Highlights */}
              <div className="space-y-4 text-xs leading-relaxed text-slate-200 select-text">
                {currentPageChunks.length === 0 ? (
                  <p className="text-slate-500 italic py-12 text-center">
                    No text chunks indexed for Page {currentPage}.
                  </p>
                ) : (
                  currentPageChunks.map((chunk) => {
                    const isSnippetTarget =
                      highlightedSnippet &&
                      chunk.content.toLowerCase().includes(highlightedSnippet.slice(0, 40).toLowerCase());

                    return (
                      <div
                        key={chunk.id}
                        className={`p-3 rounded-md transition-all ${
                          isSnippetTarget
                            ? "bg-amber-500/20 border-2 border-amber-400 text-amber-100 shadow-lg shadow-amber-500/20"
                            : "hover:bg-slate-800/40"
                        }`}
                      >
                        <p className="whitespace-pre-wrap">{chunk.content}</p>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Page Footer */}
            <div className="border-t border-slate-700/60 pt-3 mt-8 flex items-center justify-between text-[10px] text-slate-500 font-mono">
              <span>DocuMind Evidence Indexer • Verified Attribution</span>
              <span>SHA-256 Hash Verified</span>
            </div>
          </div>
        </div>
      </div>

      {/* ========================================================= */}
      {/* RIGHT PANEL: AI RESEARCH & EVIDENCE GROUNDED CHAT */}
      {/* ========================================================= */}
      <div className="w-full lg:w-1/2 flex flex-col bg-[#090D16] h-1/2 lg:h-full">
        {/* Chat Toolbar */}
        <div className="h-12 border-b border-slate-800/80 bg-[#0B0F19] px-4 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center space-x-2">
            <div className="h-6 w-6 rounded-md bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Brain className="h-3.5 w-3.5" />
            </div>
            <span className="text-xs font-semibold text-white">Grounded Intelligence Session</span>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleNewConversation}
              className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition"
              title="Start a new research conversation"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>New Session</span>
            </button>
          </div>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400">
              <div className="h-12 w-12 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-3 shadow-lg shadow-indigo-500/10">
                <Brain className="h-6 w-6" />
              </div>
              <h3 className="text-sm font-semibold text-slate-200 mb-1">
                Evidence-Grounded Document Research
              </h3>
              <p className="text-xs text-slate-400 max-w-sm mb-6">
                Ask multi-document financial, policy, or technical questions. Every factual claim is validated and cited with exact page links.
              </p>

              {/* Suggested Questions */}
              <div className="w-full max-w-md space-y-2 text-left">
                <p className="text-[11px] font-mono text-slate-500 uppercase tracking-wider mb-1">
                  Suggested Research Inquiries:
                </p>
                {suggestedQuestions.slice(0, 4).map((sq, i) => (
                  <button
                    key={i}
                    onClick={() => handleSendMessage(sq)}
                    className="w-full p-2.5 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800/80 text-xs text-slate-300 hover:text-indigo-300 transition text-left flex items-center justify-between group"
                  >
                    <span className="truncate pr-2">{sq}</span>
                    <Sparkles className="h-3 w-3 text-slate-500 group-hover:text-indigo-400 flex-shrink-0" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => {
              const isUser = msg.role === "user";
              return (
                <div
                  key={msg.id}
                  className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}
                >
                  <div
                    className={`max-w-[90%] sm:max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed ${
                      isUser
                        ? "bg-indigo-600 text-white rounded-br-none shadow-md shadow-indigo-600/20"
                        : "bg-[#0E1424] border border-slate-800 text-slate-200 rounded-bl-none shadow-xl"
                    }`}
                  >
                    {/* Message Header */}
                    {!isUser && (
                      <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800/60 text-[10px] text-slate-400">
                        <span className="flex items-center gap-1.5 font-medium text-indigo-400">
                          <Sparkles className="h-3 w-3" />
                          DocuMind Intelligence
                        </span>
                        <div className="flex items-center space-x-2 font-mono">
                          <span>R: {msg.retrieval_latency_ms}ms</span>
                          <span>•</span>
                          <span>G: {msg.answer_latency_ms}ms</span>
                        </div>
                      </div>
                    )}

                    {/* Content */}
                    <div className="whitespace-pre-wrap">{msg.content}</div>

                    {/* Evidence Citations Pills */}
                    {!isUser && msg.citations && msg.citations.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-800/60">
                        <p className="text-[10px] font-mono uppercase text-slate-400 tracking-wider mb-2">
                          Grounding Citations (Click to jump left viewer):
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.citations.map((cit, cIdx) => (
                            <button
                              key={cIdx}
                              onClick={() => handleCitationClick(cit)}
                              className="inline-flex items-center space-x-1.5 px-2 py-1 rounded bg-slate-800/90 hover:bg-indigo-600/30 border border-indigo-500/30 text-indigo-300 text-[10px] font-mono transition"
                              title={`Jump to ${cit.document_name} Page ${cit.page_number}`}
                            >
                              <FileText className="h-2.5 w-2.5" />
                              <span className="font-semibold truncate max-w-[140px]">{cit.document_name}</span>
                              <span className="px-1 rounded bg-indigo-500/20 text-indigo-200">
                                P.{cit.page_number}
                              </span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Claim Verification Statuses */}
                    {!isUser && msg.verification_claims && msg.verification_claims.length > 0 && (
                      <div className="mt-3 pt-2.5 border-t border-slate-800/50 space-y-1.5">
                        <p className="text-[10px] font-mono uppercase text-slate-400 tracking-wider">
                          Claim-to-Evidence Verification:
                        </p>
                        {msg.verification_claims.slice(0, 3).map((vc, vIdx) => (
                          <div
                            key={vIdx}
                            className={`p-2 rounded text-[11px] border ${
                              vc.status === "SUPPORTED"
                                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-300"
                                : vc.status === "CONTRADICTED"
                                ? "bg-rose-500/10 border-rose-500/20 text-rose-300"
                                : "bg-amber-500/10 border-amber-500/20 text-amber-300"
                            }`}
                          >
                            <div className="flex items-center justify-between font-medium">
                              <span className="truncate pr-2 font-sans">{vc.claim_text}</span>
                              <span className="font-mono text-[9px] uppercase px-1.5 py-0.5 rounded bg-black/40 flex-shrink-0">
                                {vc.status}
                              </span>
                            </div>
                            {vc.rationale && (
                              <p className="text-[10px] text-slate-400 mt-1">{vc.rationale}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Message Actions (Copy & Feedback) */}
                    {!isUser && (
                      <div className="mt-3 pt-2 border-t border-slate-800/40 flex items-center justify-between text-[11px] text-slate-400">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleCopy(msg.id, msg.content)}
                            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition"
                            title="Copy answer"
                          >
                            {copiedMsgId === msg.id ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                          </button>
                          <button
                            onClick={() => handleSendMessage(messages[messages.indexOf(msg) - 1]?.content || "")}
                            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition"
                            title="Regenerate answer"
                          >
                            <RotateCw className="h-3.5 w-3.5" />
                          </button>
                        </div>

                        <div className="flex items-center space-x-1.5">
                          <button
                            onClick={() => handleFeedback(msg.id, "positive")}
                            className={`p-1 rounded hover:bg-slate-800 transition ${
                              feedbackSent[msg.id] === "positive" ? "text-emerald-400" : "text-slate-500"
                            }`}
                            title="Helpful"
                          >
                            <ThumbsUp className="h-3 w-3" />
                          </button>
                          <button
                            onClick={() => handleFeedback(msg.id, "negative")}
                            className={`p-1 rounded hover:bg-slate-800 transition ${
                              feedbackSent[msg.id] === "negative" ? "text-rose-400" : "text-slate-500"
                            }`}
                            title="Unhelpful"
                          >
                            <ThumbsDown className="h-3 w-3" />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-3 border-t border-slate-800/80 bg-[#0B0F19]">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center space-x-2"
          >
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Ask a question across your document corpus..."
              disabled={sending}
              className="flex-1 px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!inputText.trim() || sending}
              className="h-9 w-9 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 flex items-center justify-center text-white shadow-md shadow-indigo-600/30 transition flex-shrink-0"
            >
              {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
