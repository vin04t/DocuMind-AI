"use client";

import React, { useState, useEffect } from "react";
import {
  GitCompare,
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileText,
  Sparkles,
  ArrowRight,
  Loader2,
  RefreshCw,
  Search,
  MessageSquare
} from "lucide-react";
import { fetchConflicts, detectConflicts, updateConflictStatus } from "../../services/api";
import { ConflictItem, ConflictReviewStatus } from "../../types";

export const ConflictsWorkspace: React.FC = () => {
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [editingNotesId, setEditingNotesId] = useState<string | null>(null);
  const [notesInput, setNotesInput] = useState("");

  const loadConflicts = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchConflicts(statusFilter);
      setConflicts(data);
    } catch (err) {
      console.error("Error loading conflicts:", err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    loadConflicts();
  }, [loadConflicts]);

  const handleRunScan = async () => {
    setScanning(true);
    try {
      const results = await detectConflicts();
      setConflicts(results);
    } catch (err: any) {
      alert(`Conflict scan failed: ${err.message}`);
    } finally {
      setScanning(false);
    }
  };

  const handleStatusChange = async (conflictId: string, newStatus: ConflictReviewStatus) => {
    try {
      const updated = await updateConflictStatus(conflictId, newStatus);
      setConflicts(prev => prev.map(c => c.id === conflictId ? updated : c));
    } catch (err: any) {
      alert(`Update status failed: ${err.message}`);
    }
  };

  const handleSaveNotes = async (conflictId: string) => {
    try {
      const conflict = conflicts.find(c => c.id === conflictId);
      if (!conflict) return;
      const updated = await updateConflictStatus(conflictId, conflict.review_status, notesInput);
      setConflicts(prev => prev.map(c => c.id === conflictId ? updated : c));
      setEditingNotesId(null);
      setNotesInput("");
    } catch (err: any) {
      alert(`Save notes failed: ${err.message}`);
    }
  };

  const getReviewBadge = (status: ConflictReviewStatus) => {
    switch (status) {
      case "RESOLVED":
        return {
          color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
          icon: CheckCircle2,
          label: "Resolved"
        };
      case "REVIEWED":
        return {
          color: "text-blue-400 bg-blue-500/10 border-blue-500/20",
          icon: Clock,
          label: "Reviewed"
        };
      default:
        return {
          color: "text-amber-400 bg-amber-500/10 border-amber-500/20",
          icon: AlertTriangle,
          label: "Needs Investigation"
        };
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* HEADER */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            Cross-Document Conflict Detector
            <span className="text-xs px-2 py-0.5 rounded bg-amber-500/15 text-amber-400 border border-amber-500/30 font-mono">
              Contradiction Intelligence
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Detects contradictory numbers, divergent policies, changed deadlines, and version disparities across documents.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRunScan}
            disabled={scanning}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-xs font-medium text-white shadow-md shadow-indigo-600/30 transition"
          >
            {scanning ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
            <span>Run Conflict Scan</span>
          </button>
        </div>
      </div>

      {/* FILTER TABS */}
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
        {[
          { id: "ALL", label: "All Conflicts" },
          { id: "NEEDS_INVESTIGATION", label: "Needs Investigation" },
          { id: "REVIEWED", label: "Reviewed" },
          { id: "RESOLVED", label: "Resolved" },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setStatusFilter(tab.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              statusFilter === tab.id
                ? "bg-slate-800 text-white border border-slate-700"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* CONFLICTS LIST */}
      <div className="space-y-4">
        {loading ? (
          <div className="py-12 text-center text-slate-500">
            <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2 text-indigo-400" />
            <p className="text-xs">Analyzing documents for contradictions...</p>
          </div>
        ) : conflicts.length === 0 ? (
          <div className="py-12 text-center text-slate-500 bg-[#0D1322] border border-slate-800 rounded-xl">
            <CheckCircle2 className="h-8 w-8 mx-auto mb-2 text-emerald-500" />
            <p className="text-xs">No conflicting statements detected under this filter.</p>
          </div>
        ) : (
          conflicts.map((conflict) => {
            const reviewBadge = getReviewBadge(conflict.review_status);
            const Icon = reviewBadge.icon;

            return (
              <div
                key={conflict.id}
                className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-5 shadow-xl hover:border-slate-700 transition space-y-4"
              >
                {/* Conflict Card Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800/70">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-semibold">
                      {conflict.conflict_type} Discrepancy
                    </span>
                    <span className="text-xs text-slate-300 font-medium">
                      {conflict.document_a_name} vs {conflict.document_b_name}
                    </span>
                  </div>

                  {/* Status Dropdown */}
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${reviewBadge.color}`}>
                      <Icon className="h-3 w-3" />
                      {reviewBadge.label}
                    </span>

                    <select
                      value={conflict.review_status}
                      onChange={(e) => handleStatusChange(conflict.id, e.target.value as ConflictReviewStatus)}
                      className="px-2 py-1 rounded bg-slate-900 border border-slate-700 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
                    >
                      <option value="NEEDS_INVESTIGATION">Needs Investigation</option>
                      <option value="REVIEWED">Mark Reviewed</option>
                      <option value="RESOLVED">Mark Resolved</option>
                    </select>
                  </div>
                </div>

                {/* Explanation */}
                <p className="text-xs text-amber-200/90 leading-relaxed bg-amber-500/10 p-2.5 rounded-lg border border-amber-500/20">
                  <span className="font-semibold text-amber-300">Contradiction Analysis:</span> {conflict.explanation}
                </p>

                {/* SIDE-BY-SIDE STATEMENT COMPARISON */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Document A Statement */}
                  <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                      <span className="text-indigo-400 font-semibold truncate max-w-[200px]">
                        {conflict.document_a_name}
                      </span>
                      <span>Page {conflict.page_a}</span>
                    </div>
                    <div className="text-xs font-medium text-slate-200 bg-slate-950/80 p-2.5 rounded border border-slate-800">
                      &ldquo;{conflict.statement_a}&rdquo;
                    </div>
                    <p className="text-[11px] text-slate-400 italic">
                      Context: &ldquo;{conflict.passage_a}&rdquo;
                    </p>
                  </div>

                  {/* Document B Statement */}
                  <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                      <span className="text-violet-400 font-semibold truncate max-w-[200px]">
                        {conflict.document_b_name}
                      </span>
                      <span>Page {conflict.page_b}</span>
                    </div>
                    <div className="text-xs font-medium text-slate-200 bg-slate-950/80 p-2.5 rounded border border-slate-800">
                      &ldquo;{conflict.statement_b}&rdquo;
                    </div>
                    <p className="text-[11px] text-slate-400 italic">
                      Context: &ldquo;{conflict.passage_b}&rdquo;
                    </p>
                  </div>
                </div>

                {/* Resolution Notes Footer */}
                <div className="pt-2 border-t border-slate-800/60 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                  {editingNotesId === conflict.id ? (
                    <div className="flex-1 flex gap-2">
                      <input
                        type="text"
                        value={notesInput}
                        onChange={(e) => setNotesInput(e.target.value)}
                        placeholder="Add resolution explanation or context..."
                        className="flex-1 px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-xs text-slate-200 focus:outline-none"
                      />
                      <button
                        onClick={() => handleSaveNotes(conflict.id)}
                        className="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-medium"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setEditingNotesId(null)}
                        className="px-2 py-1 rounded bg-slate-800 text-slate-400 hover:text-slate-200"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between w-full">
                      <span className="text-slate-400 text-[11px]">
                        {conflict.resolution_notes ? (
                          <span><strong className="text-slate-300">Resolution Note:</strong> {conflict.resolution_notes}</span>
                        ) : (
                          "No resolution notes added."
                        )}
                      </span>
                      <button
                        onClick={() => {
                          setEditingNotesId(conflict.id);
                          setNotesInput(conflict.resolution_notes || "");
                        }}
                        className="text-xs text-indigo-400 hover:text-indigo-300 font-medium ml-2"
                      >
                        {conflict.resolution_notes ? "Edit Note" : "+ Add Note"}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
