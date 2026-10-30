"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  Terminal,
  ChevronDown,
  ChevronRight,
  Filter,
  RefreshCw,
  Loader2,
  FileText,
  Search,
  Sparkles
} from "lucide-react";
import { fetchActivities } from "../../services/api";
import { ActivityItem } from "../../types";

export const ActivityWorkspace: React.FC = () => {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [eventTypeFilter, setEventTypeFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [loading, setLoading] = useState(true);
  const [expandedRowId, setExpandedRowId] = useState<string | null>(null);

  const loadActivities = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchActivities(eventTypeFilter, statusFilter);
      setActivities(data);
    } catch (err) {
      console.error("Error loading activity logs:", err);
    } finally {
      setLoading(false);
    }
  }, [eventTypeFilter, statusFilter]);

  useEffect(() => {
    loadActivities();
  }, [loadActivities]);

  const toggleRow = (id: string) => {
    setExpandedRowId(prev => (prev === id ? null : id));
  };

  const getEventBadge = (type: string) => {
    switch (type) {
      case "PDF_EXTRACTION":
      case "CHUNK_GENERATION":
        return "bg-blue-500/15 text-blue-400 border-blue-500/20";
      case "EMBEDDING_GENERATION":
      case "INDEXING":
        return "bg-indigo-500/15 text-indigo-400 border-indigo-500/20";
      case "USER_QUERY":
      case "ANSWER_GENERATION":
        return "bg-violet-500/15 text-violet-400 border-violet-500/20";
      case "CONFLICT_DETECTION":
        return "bg-amber-500/15 text-amber-400 border-amber-500/20";
      case "FAILURE":
        return "bg-rose-500/15 text-rose-400 border-rose-500/20";
      default:
        return "bg-slate-700/50 text-slate-300 border-slate-700";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "SUCCESS":
        return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />;
      case "FAILED":
        return <XCircle className="h-3.5 w-3.5 text-rose-400" />;
      case "WARNING":
        return <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />;
      default:
        return <Clock className="h-3.5 w-3.5 text-indigo-400 animate-pulse" />;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* HEADER */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            Operations & Ingestion Activity Monitor
            <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
              Relay Ops Philosophy
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time pipeline event telemetry: document parsing, chunking, vector embeddings, query executions, and verification audits.
          </p>
        </div>

        <button
          onClick={loadActivities}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 transition"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Events</span>
        </button>
      </div>

      {/* FILTER CONTROLS */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Event Type Filter */}
        <select
          value={eventTypeFilter}
          onChange={(e) => setEventTypeFilter(e.target.value)}
          className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
        >
          <option value="ALL">All Event Types</option>
          <option value="DOCUMENT_UPLOAD">DOCUMENT_UPLOAD</option>
          <option value="PDF_EXTRACTION">PDF_EXTRACTION</option>
          <option value="CHUNK_GENERATION">CHUNK_GENERATION</option>
          <option value="EMBEDDING_GENERATION">EMBEDDING_GENERATION</option>
          <option value="INDEXING">INDEXING</option>
          <option value="USER_QUERY">USER_QUERY</option>
          <option value="CONFLICT_DETECTION">CONFLICT_DETECTION</option>
          <option value="FAILURE">FAILURE</option>
        </select>

        {/* Status Filter */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
        >
          <option value="ALL">All Statuses</option>
          <option value="SUCCESS">SUCCESS</option>
          <option value="PENDING">PENDING</option>
          <option value="WARNING">WARNING</option>
          <option value="FAILED">FAILED</option>
        </select>
      </div>

      {/* ACTIVITY EVENT TABLE */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="bg-slate-900/80 border-b border-slate-800 text-slate-400 font-mono uppercase text-[10px] tracking-wider">
              <th className="py-3 px-4 w-8"></th>
              <th className="py-3 px-4">Event Type</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Subject / Document</th>
              <th className="py-3 px-4">Duration</th>
              <th className="py-3 px-4 text-right">Timestamp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {loading ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-slate-500">
                  <Loader2 className="h-5 w-5 animate-spin mx-auto mb-2 text-indigo-400" />
                  <span>Loading operations events...</span>
                </td>
              </tr>
            ) : activities.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500">
                  No activity events found matching the selected filters.
                </td>
              </tr>
            ) : (
              activities.map((act) => {
                const isExpanded = expandedRowId === act.id;
                let parsedDetails = null;
                if (act.details_json) {
                  try {
                    parsedDetails = JSON.parse(act.details_json);
                  } catch {}
                }

                return (
                  <React.Fragment key={act.id}>
                    <tr
                      onClick={() => toggleRow(act.id)}
                      className="hover:bg-slate-800/30 cursor-pointer transition select-none"
                    >
                      <td className="py-3 px-4 text-slate-500">
                        {isExpanded ? (
                          <ChevronDown className="h-3.5 w-3.5 text-indigo-400" />
                        ) : (
                          <ChevronRight className="h-3.5 w-3.5" />
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-block px-2 py-0.5 rounded font-mono text-[10px] font-semibold border ${getEventBadge(
                            act.event_type
                          )}`}
                        >
                          {act.event_type}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-1.5 font-mono text-[11px]">
                          {getStatusIcon(act.status)}
                          <span>{act.status}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4 font-medium text-slate-200 truncate max-w-xs">
                        {act.document_name || (parsedDetails?.query ? `"${parsedDetails.query}"` : "System Engine")}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-400">
                        {act.duration_ms > 0 ? `${act.duration_ms} ms` : "Instant"}
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-slate-400 text-[11px]">
                        {new Date(act.created_at).toLocaleTimeString()}
                      </td>
                    </tr>

                    {/* EXPANDABLE ROW JSON DETAILS */}
                    {isExpanded && (
                      <tr className="bg-slate-950/80 border-b border-slate-800">
                        <td colSpan={6} className="p-4 pl-12 text-xs">
                          <div className="space-y-2">
                            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                              <span>Event ID: {act.id}</span>
                              {act.document_id && <span>Document ID: {act.document_id}</span>}
                            </div>
                            {parsedDetails ? (
                              <pre className="p-3 rounded-lg bg-[#070A12] border border-slate-800 text-indigo-300 font-mono text-[11px] overflow-x-auto leading-relaxed">
                                {JSON.stringify(parsedDetails, null, 2)}
                              </pre>
                            ) : (
                              <p className="text-slate-500 italic">No structured details metadata recorded for this event.</p>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
