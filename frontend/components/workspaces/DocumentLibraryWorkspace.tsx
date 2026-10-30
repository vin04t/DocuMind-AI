"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Upload,
  Files,
  Search,
  Filter,
  Trash2,
  RefreshCw,
  FolderPlus,
  FileText,
  AlertCircle,
  CheckCircle2,
  ExternalLink,
  Loader2,
  Plus
} from "lucide-react";
import {
  fetchDocuments,
  uploadDocument,
  deleteDocument,
  reprocessDocument,
  fetchCollections,
  createCollection
} from "../../services/api";
import { DocumentItem, CollectionItem, DocumentStatus } from "../../types";

interface DocumentLibraryProps {
  onOpenViewer: (docId: string) => void;
}

export const DocumentLibraryWorkspace: React.FC<DocumentLibraryProps> = ({ onOpenViewer }) => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [collections, setCollections] = useState<CollectionItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [collectionFilter, setCollectionFilter] = useState("ALL");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [showCreateCollectionModal, setShowCreateCollectionModal] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState("");

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const loadAll = async () => {
    try {
      const [docs, cols] = await Promise.all([
        fetchDocuments(searchQuery, statusFilter, collectionFilter),
        fetchCollections()
      ]);
      setDocuments(docs);
      setCollections(cols);
    } catch (err) {
      console.error("Error loading library data:", err);
    }
  };

  useEffect(() => {
    loadAll();
  }, [searchQuery, statusFilter, collectionFilter]);

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploading(true);

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        alert(`File ${file.name} is not a PDF.`);
        continue;
      }
      setUploadProgress(`Ingesting ${file.name} (${i + 1}/${files.length})...`);
      try {
        await uploadDocument(file, collectionFilter !== "ALL" ? collectionFilter : undefined);
      } catch (err: any) {
        alert(`Upload error for ${file.name}: ${err.message}`);
      }
    }

    setUploading(false);
    setUploadProgress(null);
    loadAll();
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!confirm(`Are you sure you want to delete ${filename}? This will remove vector indices and chunks.`)) return;
    setActionLoadingId(docId);
    try {
      await deleteDocument(docId);
      setDocuments(prev => prev.filter(d => d.id !== docId));
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleReprocess = async (docId: string) => {
    setActionLoadingId(docId);
    try {
      const updated = await reprocessDocument(docId);
      setDocuments(prev => prev.map(d => d.id === docId ? updated : d));
    } catch (err: any) {
      alert(`Reprocess failed: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleCreateCollection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCollectionName.trim()) return;
    try {
      const col = await createCollection(newCollectionName.trim());
      setCollections(prev => [...prev, col]);
      setNewCollectionName("");
      setShowCreateCollectionModal(false);
    } catch (err: any) {
      alert(`Error creating collection: ${err.message}`);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* HEADER */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            Document Repository & Ingestion
            <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
              {documents.length} Files
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Upload, index, and organize PDF documents for hybrid vector and keyword retrieval.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowCreateCollectionModal(true)}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-xs font-medium text-slate-200 transition"
          >
            <FolderPlus className="h-3.5 w-3.5 text-slate-400" />
            <span>New Collection</span>
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white shadow-md shadow-indigo-600/30 transition disabled:opacity-50"
          >
            {uploading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Upload className="h-3.5 w-3.5" />}
            <span>Upload PDF</span>
          </button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => handleFileUpload(e.target.files)}
            multiple
            accept=".pdf"
            className="hidden"
          />
        </div>
      </div>

      {/* DRAG & DROP UPLOAD ZONE */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragOver(false);
          handleFileUpload(e.dataTransfer.files);
        }}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
          isDragOver
            ? "border-indigo-500 bg-indigo-500/10"
            : "border-slate-800 hover:border-slate-700 bg-slate-900/40"
        }`}
      >
        <div className="h-10 w-10 mx-auto rounded-full bg-indigo-600/10 flex items-center justify-center text-indigo-400 mb-2">
          <Upload className="h-5 w-5" />
        </div>
        <p className="text-sm font-medium text-slate-200">
          {uploading ? uploadProgress : "Drop PDF documents here, or click to browse files"}
        </p>
        <p className="text-xs text-slate-400 mt-1">
          Supports multi-page corporate reports, policies, whitepapers up to 50MB per file
        </p>
      </div>

      {/* FILTER & SEARCH CONTROLS */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        {/* Search */}
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search documents by name..."
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
          />
        </div>

        {/* Status & Collection Filters */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="INDEXED">Indexed Only</option>
            <option value="EXTRACTING">Extracting</option>
            <option value="CHUNKING">Chunking</option>
            <option value="EMBEDDING">Embedding</option>
            <option value="FAILED">Failed</option>
          </select>

          {/* Collection Filter */}
          <select
            value={collectionFilter}
            onChange={(e) => setCollectionFilter(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="ALL">All Collections</option>
            {collections.map(col => (
              <option key={col.id} value={col.id}>{col.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* DOCUMENTS DATA TABLE */}
      <div className="bg-[#0D1322] border border-slate-800/80 rounded-xl overflow-hidden shadow-xl">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="bg-slate-900/80 border-b border-slate-800 text-slate-400 font-mono uppercase text-[10px] tracking-wider">
              <th className="py-3 px-4">Document</th>
              <th className="py-3 px-4">Pages</th>
              <th className="py-3 px-4">Size</th>
              <th className="py-3 px-4">Uploaded</th>
              <th className="py-3 px-4">Processing Pipeline</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {documents.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-400">
                  No documents found matching the selected filters.
                </td>
              </tr>
            ) : (
              documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-slate-800/25 transition">
                  <td className="py-3.5 px-4 font-medium text-slate-200">
                    <div className="flex items-center space-x-2.5">
                      <div className="h-8 w-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 flex-shrink-0">
                        <FileText className="h-4 w-4" />
                      </div>
                      <div className="truncate max-w-xs sm:max-w-md">
                        <p className="truncate text-slate-100 font-medium">{doc.filename}</p>
                        <p className="text-[10px] text-slate-400 font-mono">ID: {doc.id.slice(0, 8)}...</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 font-mono text-slate-300">{doc.page_count} pgs</td>
                  <td className="py-3.5 px-4 font-mono text-slate-400">{(doc.file_size / 1024).toFixed(1)} KB</td>
                  <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium ${
                      doc.status === "INDEXED"
                        ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20"
                        : doc.status === "FAILED"
                        ? "bg-rose-500/15 text-rose-400 border border-rose-500/20"
                        : "bg-indigo-500/15 text-indigo-400 border border-indigo-500/20"
                    }`}>
                      <span className={`h-1.5 w-1.5 rounded-full ${
                        doc.status === "INDEXED" ? "bg-emerald-400" : doc.status === "FAILED" ? "bg-rose-400" : "bg-indigo-400 animate-pulse"
                      }`} />
                      {doc.status}
                    </span>
                    {doc.error_message && (
                      <p className="text-[10px] text-rose-400 mt-1 truncate max-w-xs">{doc.error_message}</p>
                    )}
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <div className="inline-flex items-center space-x-1.5">
                      <button
                        onClick={() => onOpenViewer(doc.id)}
                        className="p-1.5 rounded-md hover:bg-indigo-600/20 text-slate-400 hover:text-indigo-300 transition"
                        title="Open in Split-Screen Intelligence Workspace"
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleReprocess(doc.id)}
                        disabled={actionLoadingId === doc.id}
                        className="p-1.5 rounded-md hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition disabled:opacity-50"
                        title="Reprocess Document"
                      >
                        <RefreshCw className={`h-3.5 w-3.5 ${actionLoadingId === doc.id ? "animate-spin" : ""}`} />
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id, doc.filename)}
                        disabled={actionLoadingId === doc.id}
                        className="p-1.5 rounded-md hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition disabled:opacity-50"
                        title="Delete Document"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* CREATE COLLECTION MODAL */}
      {showCreateCollectionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-[#0D1322] border border-slate-800 rounded-xl p-5 shadow-2xl">
            <h3 className="text-base font-semibold text-white mb-2">Create Document Collection</h3>
            <p className="text-xs text-slate-400 mb-4">
              Group related documents for targeted multi-document research queries.
            </p>
            <form onSubmit={handleCreateCollection} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Collection Name</label>
                <input
                  type="text"
                  required
                  value={newCollectionName}
                  onChange={(e) => setNewCollectionName(e.target.value)}
                  placeholder="e.g., Financial Reports 2024"
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateCollectionModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-xs text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs text-white font-medium shadow-md shadow-indigo-600/30"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
