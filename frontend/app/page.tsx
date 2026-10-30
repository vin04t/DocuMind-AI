"use client";

import React, { useState } from "react";
import { Shell, WorkspaceTab } from "../components/layout/Shell";
import { OverviewWorkspace } from "../components/workspaces/OverviewWorkspace";
import { DocumentLibraryWorkspace } from "../components/workspaces/DocumentLibraryWorkspace";
import { IntelligenceWorkspace } from "../components/workspaces/IntelligenceWorkspace";
import { VerificationWorkspace } from "../components/workspaces/VerificationWorkspace";
import { ConflictsWorkspace } from "../components/workspaces/ConflictsWorkspace";
import { AnalyticsWorkspace } from "../components/workspaces/AnalyticsWorkspace";
import { ActivityWorkspace } from "../components/workspaces/ActivityWorkspace";

export default function Home() {
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("overview");
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  const handleNavigateWithDoc = (tab: WorkspaceTab, docId?: string) => {
    if (docId) setSelectedDocId(docId);
    setActiveTab(tab);
  };

  return (
    <Shell activeTab={activeTab} onTabChange={setActiveTab}>
      {activeTab === "overview" && (
        <OverviewWorkspace onNavigate={handleNavigateWithDoc} />
      )}
      {activeTab === "documents" && (
        <DocumentLibraryWorkspace onOpenViewer={(id) => handleNavigateWithDoc("chat", id)} />
      )}
      {activeTab === "chat" && (
        <IntelligenceWorkspace initialDocId={selectedDocId} />
      )}
      {activeTab === "verification" && (
        <VerificationWorkspace />
      )}
      {activeTab === "conflicts" && (
        <ConflictsWorkspace />
      )}
      {activeTab === "analytics" && (
        <AnalyticsWorkspace />
      )}
      {activeTab === "activity" && (
        <ActivityWorkspace />
      )}
    </Shell>
  );
}
