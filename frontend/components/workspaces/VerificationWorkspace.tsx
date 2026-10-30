"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Search,
  Filter,
  FileText,
  Sparkles,
  ArrowRight,
  Loader2,
  Play
} from "lucide-react";
import { fetchVerifiedClaims, verifyCustomClaim } from "../../services/api";
import { VerificationClaimItem, VerificationStatus } from "../../types";

export const VerificationWorkspace: React.FC = () => {
  const [claims, setClaims] = useState<VerificationClaimItem[]>([]);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [loading, setLoading] = useState(true);

  // Ad-hoc claim verification tester state
  const [testClaimText, setTestClaimText] = useState("");
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<VerificationClaimItem | null>(null);

  const loadClaims = async () => {
    setLoading(true);
    try {
      const data = await fetchVerifiedClaims(statusFilter);
      setClaims(data);
    } catch (err) {
      console.error("Error loading verification claims:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadClaims();
  }, [statusFilter]);

  const handleTestClaim = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testClaimText.trim() || testing) return;
    setTesting(true);
    setTestResult(null);
    try {
      const res = await verifyCustomClaim(testClaimText.trim());
      setTestResult(res);
      // Also reload claims list to show updated history
      loadClaims();
    } catch (err: any) {
      alert(`Verification failed: ${err.message}`);
    } finally {
      setTesting(false);
    }
  };

  const getStatusBadge = (status: VerificationStatus) => {
    switch (status) {
      case "SUPPORTED":
        return {
          icon: CheckCircle2,
          color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
          label: "Supported",
        };
      case "PARTIALLY_SUPPORTED":
        return {
          icon: AlertTriangle,
          color: "text-amber-400 bg-amber-500/10 border-amber-500/20",
          label: "Partially Supported",
        };
      case "CONTRADICTED":
        return {
          icon: XCircle,
          color: "text-rose-400 bg-rose-500/10 border-rose-500/20",
          label: "Contradicted",
        };
      default:
        return {
          icon: HelpCircle,
          color: "text-slate-400 bg-slate-500/10 border-slate-500/20",
          label: "Not Supported",
        };
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* HEADER */}
      <div className="pb-4 border-b border-slate-800/80">
        <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          Evidence Verification Engine
          <span className="text-xs px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 font-mono">
            NLI Entailment
          </span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Deconstructs model responses and statements into atomic factual claims, independently verifying each against underlying document passages.
        </p>
      </div>

      {/* INTERACTIVE CLAIM TEST BENCH */}
      <div className="bg-[#0D1322] border border-slate-800 rounded-xl p-5 shadow-xl">
        <div className="flex items-center space-x-2 mb-3">
          <Sparkles className="h-4 w-4 text-indigo-400" />
          <h2 className="text-sm font-semibold text-white">Ad-Hoc Claim Verification Bench</h2>
        </div>
        <form onSubmit={handleTestClaim} className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={testClaimText}
            onChange={(e) => setTestClaimText(e.target.value)}
            placeholder="Type any factual assertion (e.g., 'Acme Technologies reported revenue of $42.5 million in Q3 2024')..."
            className="flex-1 px-3.5 py-2.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            disabled={!testClaimText.trim() || testing}
            className="inline-flex items-center justify-center space-x-2 px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-xs font-medium text-white shadow-md shadow-indigo-600/30 transition flex-shrink-0"
          >
            {testing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            <span>Verify Claim</span>
          </button>
        </form>

        {/* Live Test Result Banner */}
        {testResult && (
          <div className="mt-4 p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-2 animate-fadeIn">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200">Verification Result</span>
              {(() => {
                const badge = getStatusBadge(testResult.status);
                const Icon = badge.icon;
                return (
                  <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${badge.color}`}>
                    <Icon className="h-3.5 w-3.5" />
                    {badge.label}
                  </span>
                );
              })()}
            </div>
            <p className="text-xs text-slate-300 font-medium">&ldquo;{testResult.claim_text}&rdquo;</p>
            {testResult.supporting_passage && (
              <div className="p-2.5 rounded bg-slate-950/80 border border-slate-800 text-xs text-slate-300">
                <span className="text-[10px] text-slate-500 font-mono block mb-1">
                  Supporting Passage ({testResult.document_name} • Page {testResult.page_number}):
                </span>
                <p className="italic">&ldquo;{testResult.supporting_passage}&rdquo;</p>
              </div>
            )}
            <p className="text-[11px] text-slate-400">
              <span className="text-slate-300 font-medium">Analysis Rationale:</span> {testResult.rationale}
            </p>
          </div>
        )}
      </div>

      {/* STATUS TABS FILTER */}
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-2 overflow-x-auto">
        {[
          { id: "ALL", label: "All Claims" },
          { id: "SUPPORTED", label: "Supported", count: claims.filter(c => c.status === "SUPPORTED").length },
          { id: "PARTIALLY_SUPPORTED", label: "Partially Supported", count: claims.filter(c => c.status === "PARTIALLY_SUPPORTED").length },
          { id: "CONTRADICTED", label: "Contradicted", count: claims.filter(c => c.status === "CONTRADICTED").length },
          { id: "NOT_SUPPORTED", label: "Not Supported", count: claims.filter(c => c.status === "NOT_SUPPORTED").length },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setStatusFilter(tab.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5 ${
              statusFilter === tab.id
                ? "bg-slate-800 text-white border border-slate-700"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
            }`}
          >
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-700/60 font-mono">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* CLAIMS STREAM LIST */}
      <div className="space-y-3">
        {loading ? (
          <div className="py-12 text-center text-slate-500">
            <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2 text-indigo-400" />
            <p className="text-xs">Loading verified claims...</p>
          </div>
        ) : claims.length === 0 ? (
          <div className="py-12 text-center text-slate-500 bg-[#0D1322] border border-slate-800 rounded-xl">
            <ShieldCheck className="h-8 w-8 mx-auto mb-2 text-slate-600" />
            <p className="text-xs">No claims verified under this filter yet.</p>
          </div>
        ) : (
          claims.map((claim) => {
            const badge = getStatusBadge(claim.status);
            const Icon = badge.icon;
            return (
              <div
                key={claim.id}
                className="bg-[#0D1322] border border-slate-800/80 rounded-xl p-4 shadow-md hover:border-slate-700 transition space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-start space-x-2.5">
                    <div className="mt-0.5">
                      <Icon className={`h-4 w-4 ${badge.color.split(" ")[0]}`} />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-100">{claim.claim_text}</p>
                      {claim.document_name && (
                        <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                          Source: {claim.document_name} • Page {claim.page_number}
                        </p>
                      )}
                    </div>
                  </div>

                  <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider font-mono border self-start sm:self-center ${badge.color}`}>
                    {badge.label}
                  </span>
                </div>

                {claim.supporting_passage && (
                  <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800/80 text-xs text-slate-300">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider font-mono block mb-1">
                      Attributed Passage:
                    </span>
                    <p className="italic leading-relaxed">&ldquo;{claim.supporting_passage}&rdquo;</p>
                  </div>
                )}

                {claim.rationale && (
                  <p className="text-[11px] text-slate-400">
                    <span className="text-slate-300 font-medium">Verification Rationale:</span> {claim.rationale}
                  </p>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
