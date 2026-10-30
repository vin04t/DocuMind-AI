"use client";

import React, { useState } from "react";
import {
  LayoutDashboard,
  Files,
  Brain,
  ShieldCheck,
  GitCompare,
  BarChart3,
  Activity,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Search,
  Bell,
  CheckCircle2,
  Menu,
  X,
  FileText
} from "lucide-react";

export type WorkspaceTab =
  | "overview"
  | "documents"
  | "chat"
  | "verification"
  | "conflicts"
  | "analytics"
  | "activity";

interface ShellProps {
  activeTab: WorkspaceTab;
  onTabChange: (tab: WorkspaceTab) => void;
  children: React.ReactNode;
  selectedDocForViewer?: string | null;
  selectedPageForViewer?: number | null;
}

export const Shell: React.FC<ShellProps> = ({
  activeTab,
  onTabChange,
  children,
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  const navItems: Array<{
    id: WorkspaceTab;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    badge?: string;
  }> = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "documents", label: "Document Library", icon: Files },
    { id: "chat", label: "Intelligence Workspace", icon: Brain, badge: "AI" },
    { id: "verification", label: "Evidence Verification", icon: ShieldCheck },
    { id: "conflicts", label: "Conflict Detector", icon: GitCompare },
    { id: "analytics", label: "Research Analytics", icon: BarChart3 },
    { id: "activity", label: "Activity Monitor", icon: Activity },
  ];

  return (
    <div className="flex h-screen w-full bg-[#090D16] text-slate-100 overflow-hidden font-sans">
      {/* SIDEBAR (Desktop) */}
      <aside
        className={`hidden md:flex flex-col border-r border-slate-800/80 bg-[#0B0F19] transition-all duration-300 select-none z-30 ${
          collapsed ? "w-16" : "w-64"
        }`}
      >
        {/* Logo & Platform Brand */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-slate-800/80">
          {!collapsed ? (
            <div className="flex items-center space-x-3 cursor-pointer" onClick={() => onTabChange("overview")}>
              <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                <Brain className="h-5 w-5 text-white" />
              </div>
              <div>
                <span className="font-semibold text-base tracking-tight text-white flex items-center gap-1.5">
                  DocuMind <span className="text-xs px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 font-mono">AI</span>
                </span>
                <p className="text-[10px] text-slate-400 tracking-wider uppercase font-medium">Document Intelligence</p>
              </div>
            </div>
          ) : (
            <div className="mx-auto h-9 w-9 rounded-lg bg-indigo-600 flex items-center justify-center shadow-md shadow-indigo-500/30">
              <Brain className="h-5 w-5 text-white" />
            </div>
          )}

          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800/60 transition"
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        {/* Engine Status Indicator */}
        <div className={`px-4 py-3 border-b border-slate-800/50 ${collapsed ? "text-center" : ""}`}>
          <div className="inline-flex items-center space-x-2 text-xs text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded-md border border-emerald-500/20">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            {!collapsed && <span className="font-medium text-[11px]">Hybrid RAG Engine Online</span>}
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-2.5 py-4 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-all group ${
                  isActive
                    ? "bg-indigo-600 text-white shadow-sm shadow-indigo-600/40"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
                title={collapsed ? item.label : undefined}
              >
                <Icon
                  className={`h-4.5 w-4.5 flex-shrink-0 transition-colors ${
                    isActive ? "text-white" : "text-slate-400 group-hover:text-slate-200"
                  }`}
                />
                {!collapsed && (
                  <span className="ml-3 truncate flex-1 text-left">{item.label}</span>
                )}
                {!collapsed && item.badge && (
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold ${
                    isActive ? "bg-white/20 text-white" : "bg-indigo-500/15 text-indigo-400"
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* User Footer Profile */}
        <div className="p-3 border-t border-slate-800/80 bg-slate-900/40">
          <div className="flex items-center space-x-3">
            <div className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-semibold text-indigo-400">
              LR
            </div>
            {!collapsed && (
              <div className="flex-1 truncate">
                <p className="text-xs font-medium text-slate-200 truncate">Lead Researcher</p>
                <p className="text-[10px] text-slate-400 truncate font-mono">demo@documind.ai</p>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* MOBILE DRAWER */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden bg-black/70 backdrop-blur-sm">
          <div className="w-64 bg-[#0B0F19] h-full flex flex-col p-4 border-r border-slate-800">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <span className="font-semibold text-white">DocuMind AI</span>
              <button onClick={() => setMobileMenuOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>
            <nav className="flex-1 py-4 space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      onTabChange(item.id);
                      setMobileMenuOpen(false);
                    }}
                    className={`w-full flex items-center rounded-lg px-3 py-2.5 text-sm font-medium ${
                      isActive ? "bg-indigo-600 text-white" : "text-slate-400 hover:bg-slate-800/50"
                    }`}
                  >
                    <Icon className="h-4.5 w-4.5" />
                    <span className="ml-3">{item.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>
      )}

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* TOP NAVIGATION BAR */}
        <header className="h-14 border-b border-slate-800/80 bg-[#0B0F19]/90 backdrop-blur px-4 sm:px-6 flex items-center justify-between z-20 flex-shrink-0">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="p-1.5 md:hidden text-slate-400 hover:text-white"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="flex items-center space-x-2 text-xs sm:text-sm">
              <span className="text-slate-500 font-medium">Workspace</span>
              <span className="text-slate-600">/</span>
              <span className="text-slate-200 font-semibold capitalize">
                {activeTab === "chat" ? "Intelligence Workspace" : activeTab.replace("-", " ")}
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {/* Quick Action Button */}
            {activeTab !== "chat" && (
              <button
                onClick={() => onTabChange("chat")}
                className="hidden sm:inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 text-indigo-300 text-xs font-medium transition"
              >
                <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                <span>Ask AI Intelligence</span>
              </button>
            )}

            {/* Notification Bell */}
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition"
              >
                <Bell className="h-4 w-4" />
                <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-indigo-500"></span>
              </button>

              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-4 z-50 text-xs">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                    <span className="font-semibold text-slate-200">System Activity</span>
                    <span className="text-[10px] text-slate-400">Real-time</span>
                  </div>
                  <div className="mt-3 space-y-2.5">
                    <div className="flex items-start space-x-2.5">
                      <CheckCircle2 className="h-4 w-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-slate-200 font-medium">5 Documents Indexed</p>
                        <p className="text-slate-400 text-[11px]">Corporate corpus & technical whitepaper loaded</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-2.5">
                      <Sparkles className="h-4 w-4 text-indigo-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-slate-200 font-medium">BM25 & Vector Index Sync</p>
                        <p className="text-slate-400 text-[11px]">RRF rank fusion calibrated at k=60</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* WORKSPACE CONTENT */}
        <main className="flex-1 overflow-y-auto bg-[#090D16]">
          {children}
        </main>
      </div>
    </div>
  );
};
