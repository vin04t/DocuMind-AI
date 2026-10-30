"use client";

import React, { useState, useEffect } from "react";
import {
  BarChart3,
  Clock,
  ShieldCheck,
  Files,
  HelpCircle,
  TrendingUp,
  Activity,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Loader2
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  Legend,
  BarChart,
  Bar
} from "recharts";
import { fetchAnalyticsSummary } from "../../services/api";
import { AnalyticsSummary } from "../../types";

const VERIFICATION_COLORS = ["#10b981", "#f59e0b", "#f43f5e", "#64748b"];

export const AnalyticsWorkspace: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await fetchAnalyticsSummary();
        setAnalytics(data);
      } catch (err) {
        console.error("Error loading analytics:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading || !analytics) {
    return (
      <div className="h-full flex items-center justify-center p-12 text-slate-500">
        <Loader2 className="h-6 w-6 animate-spin mr-2 text-indigo-400" />
        <span className="text-xs">Computing research analytics...</span>
      </div>
    );
  }

  const pieData = [
    { name: "Supported", value: analytics.verification_stats.supported },
    { name: "Partially Supported", value: analytics.verification_stats.partially_supported },
    { name: "Contradicted", value: analytics.verification_stats.contradicted },
    { name: "Not Supported", value: analytics.verification_stats.not_supported },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* HEADER */}
      <div className="pb-4 border-b border-slate-800/80">
        <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          Research & Retrieval Analytics
          <span className="text-xs px-2 py-0.5 rounded bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 font-mono">
            Operational Telemetry
          </span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Real-time metrics on retrieval latency, answer generation speed, evidence grounding coverage, and verification distributions.
        </p>
      </div>

      {/* METRIC KPI TILES */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-4">
          <span className="text-xs text-slate-400 font-medium">Total Research Questions</span>
          <p className="text-2xl font-bold text-white mt-2 font-mono">{analytics.total_questions}</p>
          <p className="text-[11px] text-slate-500 mt-1">Direct, numerical & multi-doc queries</p>
        </div>

        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-4">
          <span className="text-xs text-slate-400 font-medium">Avg Retrieval Latency</span>
          <p className="text-2xl font-bold text-emerald-400 mt-2 font-mono">
            {analytics.avg_retrieval_latency_ms} <span className="text-xs text-slate-400">ms</span>
          </p>
          <p className="text-[11px] text-emerald-500/80 mt-1 font-mono">BM25 + Cosine Dense RRF</p>
        </div>

        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-4">
          <span className="text-xs text-slate-400 font-medium">Avg Answer Latency</span>
          <p className="text-2xl font-bold text-indigo-400 mt-2 font-mono">
            {analytics.avg_answer_latency_ms} <span className="text-xs text-slate-400">ms</span>
          </p>
          <p className="text-[11px] text-indigo-400/80 mt-1">Evidence assembly & generation</p>
        </div>

        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-4">
          <span className="text-xs text-slate-400 font-medium">Evidence Grounding Rate</span>
          <p className="text-2xl font-bold text-violet-400 mt-2 font-mono">
            {analytics.evidence_coverage_percentage}%
          </p>
          <p className="text-[11px] text-violet-400/80 mt-1 font-mono">Citations to passage attribution</p>
        </div>
      </div>

      {/* CHARTS GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Queries Over Time */}
        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800/60">
            <h3 className="text-xs font-semibold text-slate-200">Query Volume Trend (Last 7 Days)</h3>
            <span className="text-[10px] font-mono text-indigo-400">Actual Sessions</span>
          </div>
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={analytics.queries_over_time}>
                <defs>
                  <linearGradient id="qGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.6} />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: 8, fontSize: 11 }}
                />
                <Area type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={2} fill="url(#qGrad)" name="Queries" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Latency Comparison */}
        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800/60">
            <h3 className="text-xs font-semibold text-slate-200">Latency Dynamics (ms)</h3>
            <span className="text-[10px] font-mono text-emerald-400">Sub-Second RAG</span>
          </div>
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={analytics.latency_trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.6} />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: 8, fontSize: 11 }}
                />
                <Line type="monotone" dataKey="avg_retrieval_ms" stroke="#10b981" strokeWidth={2} dot={{ r: 3 }} name="Retrieval (ms)" />
                <Line type="monotone" dataKey="avg_answer_ms" stroke="#818cf8" strokeWidth={2} dot={{ r: 3 }} name="Generation (ms)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Verification Outcomes Breakdown */}
        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800/60">
            <h3 className="text-xs font-semibold text-slate-200">Verification Outcome Distribution</h3>
            <span className="text-[10px] font-mono text-slate-400">Claim Entailment</span>
          </div>
          <div className="h-60 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={VERIFICATION_COLORS[index % VERIFICATION_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: 8, fontSize: 11 }}
                />
                <Legend
                  wrapperStyle={{ fontSize: 11 }}
                  formatter={(value) => <span className="text-slate-300">{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Frequently Queried Documents */}
        <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800/60">
            <h3 className="text-xs font-semibold text-slate-200">Document Corpus Utilization</h3>
            <span className="text-[10px] font-mono text-slate-400">Indexed Corpora</span>
          </div>
          <div className="space-y-3 pt-2">
            {analytics.frequently_queried_documents.map((doc, idx) => (
              <div key={doc.id} className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-slate-900 border border-slate-800/80">
                <div className="flex items-center space-x-2 truncate max-w-xs">
                  <span className="font-mono text-[10px] text-slate-500">#{idx + 1}</span>
                  <Files className="h-3.5 w-3.5 text-indigo-400 flex-shrink-0" />
                  <span className="truncate text-slate-200 font-medium">{doc.filename}</span>
                </div>
                <div className="flex items-center space-x-2 font-mono text-[11px]">
                  <span className="text-indigo-400 font-semibold">{doc.queries_count} Queries</span>
                  <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[9px] uppercase font-bold">
                    {doc.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
