import React, { useEffect, useState, useRef } from 'react';
import {
  FileText,
  Upload,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Clock,
  Search,
  ChevronRight,
  ShieldAlert,
  Sparkles,
  Layers,
  FileCheck,
  Tag,
  Hash
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { documentService } from '@/services/documents/documentService';
import { Document, DocumentAnalysisData } from '@/types';

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [analysisResult, setAnalysisResult] = useState<DocumentAnalysisData | null>(null);

  const [isLoadingList, setIsLoadingList] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const [uploadError, setUploadError] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const [selectedTask, setSelectedTask] = useState<string>('summarize');
  const [customQuery, setCustomQuery] = useState<string>('');

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadDocuments = async () => {
    setIsLoadingList(true);
    try {
      const docs = await documentService.listDocuments();
      setDocuments(docs);
      if (docs.length > 0 && !selectedDoc) {
        setSelectedDoc(docs[0]);
        if (docs[0].metadata?.analysis) {
          setAnalysisResult(docs[0].metadata.analysis);
        }
      }
    } catch (err: any) {
      console.error('Failed to load documents:', err);
    } finally {
      setIsLoadingList(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadError(null);
    setIsUploading(true);

    try {
      const created = await documentService.uploadDocument(file);
      await loadDocuments();
      setSelectedDoc(created);
      setAnalysisResult(null);
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || err.message || 'File upload failed.';
      setUploadError(msg);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleSelectDoc = (doc: Document) => {
    setSelectedDoc(doc);
    setAnalysisError(null);
    if (doc.metadata?.analysis) {
      setAnalysisResult(doc.metadata.analysis);
    } else {
      setAnalysisResult(null);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedDoc) return;
    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      const result = await documentService.analyzeDocument(selectedDoc.id, selectedTask, customQuery || undefined);
      setAnalysisResult(result);
      await loadDocuments();
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || err.message || 'Analysis failed.';
      setAnalysisError(msg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PROCESSED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-800">
            <CheckCircle2 className="w-3 h-3" /> Processed
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-950/80 text-indigo-400 border border-indigo-800 animate-pulse">
            <RefreshCw className="w-3 h-3 animate-spin" /> Processing
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-950/80 text-rose-400 border border-rose-800">
            <AlertCircle className="w-3 h-3" /> Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
            <Clock className="w-3 h-3" /> Uploaded
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <FileText className="w-7 h-7 text-indigo-400" />
            Document Intelligence Hub
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Enterprise multi-format document extraction, classification, and understanding (PDF, DOCX, TXT).
          </p>
        </div>

        <div className="flex items-center gap-3">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf,.docx,.txt"
            className="hidden"
            id="doc-upload-input"
          />
          <Button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-2"
          >
            {isUploading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Upload Document
              </>
            )}
          </Button>
          <Button
            variant="secondary"
            onClick={loadDocuments}
            disabled={isLoadingList}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${isLoadingList ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Upload Error Banner */}
      {uploadError && (
        <div className="p-4 rounded-xl bg-rose-950/50 border border-rose-800 text-rose-200 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-semibold">Upload Validation Failed</p>
            <p className="text-rose-300 mt-0.5">{uploadError}</p>
          </div>
        </div>
      )}

      {/* Main Grid: Document List & Details/Analysis Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Document List */}
        <div className="lg:col-span-5 space-y-4">
          <Card className="p-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
              <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" />
                Enterprise Documents ({documents.length})
              </span>
              <span className="text-xs text-slate-400">PDF, DOCX, TXT</span>
            </div>

            {isLoadingList && documents.length === 0 ? (
              <div className="py-12 text-center text-slate-400">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-400" />
                <p className="text-xs">Loading documents...</p>
              </div>
            ) : documents.length === 0 ? (
              <div className="py-12 text-center border border-dashed border-slate-800 rounded-lg p-6">
                <FileText className="w-10 h-10 mx-auto text-slate-600 mb-2" />
                <p className="text-sm font-medium text-slate-300">No documents uploaded yet</p>
                <p className="text-xs text-slate-500 mt-1 mb-4">
                  Upload an invoice, company policy, technical manual, or report.
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                >
                  Browse Files
                </Button>
              </div>
            ) : (
              <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
                {documents.map((doc) => {
                  const isSelected = selectedDoc?.id === doc.id;
                  const docType = doc.metadata?.document_type || doc.metadata?.analysis?.document_type;
                  return (
                    <div
                      key={doc.id}
                      onClick={() => handleSelectDoc(doc)}
                      className={`p-3.5 rounded-lg border transition-all cursor-pointer flex items-center justify-between ${
                        isSelected
                          ? 'bg-indigo-950/40 border-indigo-600 shadow-sm'
                          : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className="min-w-0 pr-3">
                        <div className="flex items-center gap-2">
                          <FileText className={`w-4 h-4 shrink-0 ${isSelected ? 'text-indigo-400' : 'text-slate-400'}`} />
                          <p className="text-sm font-medium text-slate-200 truncate">{doc.file_name}</p>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                          <span>{formatFileSize(doc.file_size_bytes)}</span>
                          <span>•</span>
                          <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                          {docType && (
                            <>
                              <span>•</span>
                              <span className="text-indigo-400 font-mono text-[11px]">{docType}</span>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="shrink-0 flex items-center gap-2">
                        {getStatusBadge(doc.processing_status)}
                        <ChevronRight className={`w-4 h-4 ${isSelected ? 'text-indigo-400' : 'text-slate-600'}`} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </div>

        {/* Right Column: Document Details & Agent Analysis */}
        <div className="lg:col-span-7 space-y-6">
          {selectedDoc ? (
            <>
              {/* Document Metadata Card */}
              <Card className="space-y-4">
                <div className="flex items-start justify-between pb-3 border-b border-slate-800">
                  <div>
                    <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                      <FileCheck className="w-5 h-5 text-indigo-400" />
                      {selectedDoc.file_name}
                    </h2>
                    <p className="text-xs text-slate-400 mt-0.5">ID: {selectedDoc.id}</p>
                  </div>
                  {getStatusBadge(selectedDoc.processing_status)}
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80">
                    <p className="text-slate-500">File Type</p>
                    <p className="font-medium text-slate-200 mt-0.5 truncate">{selectedDoc.file_type}</p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80">
                    <p className="text-slate-500">Size</p>
                    <p className="font-medium text-slate-200 mt-0.5">{formatFileSize(selectedDoc.file_size_bytes)}</p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80">
                    <p className="text-slate-500">Uploaded</p>
                    <p className="font-medium text-slate-200 mt-0.5">
                      {new Date(selectedDoc.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80">
                    <p className="text-slate-500">Document Type</p>
                    <p className="font-medium text-indigo-400 mt-0.5">
                      {selectedDoc.metadata?.document_type || analysisResult?.document_type || 'PENDING'}
                    </p>
                  </div>
                </div>

                {/* Analysis Action Controls */}
                <div className="pt-2 border-t border-slate-800/80 space-y-3">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="sm:col-span-1">
                      <label className="block text-xs font-medium text-slate-400 mb-1">Select Analysis Task</label>
                      <select
                        value={selectedTask}
                        onChange={(e) => setSelectedTask(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                      >
                        <option value="summarize">Summarize</option>
                        <option value="extract_information">Extract Information</option>
                        <option value="find_key_points">Find Key Points</option>
                        <option value="classify">Classify</option>
                        <option value="analyze_structure">Analyze Structure</option>
                      </select>
                    </div>
                    <div className="sm:col-span-2">
                      <label className="block text-xs font-medium text-slate-400 mb-1">
                        Optional Query or Custom Question
                      </label>
                      <input
                        type="text"
                        value={customQuery}
                        onChange={(e) => setCustomQuery(e.target.value)}
                        placeholder="e.g., Check invoice total and taxes, or safety warnings"
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <Button
                      onClick={handleAnalyze}
                      disabled={isAnalyzing}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-2"
                    >
                      {isAnalyzing ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          Analyzing with Document Agent...
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4 text-indigo-200" />
                          Execute Document Agent
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </Card>

              {/* Analysis Error */}
              {analysisError && (
                <div className="p-4 rounded-xl bg-rose-950/50 border border-rose-800 text-rose-200 flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                  <div className="text-sm">
                    <p className="font-semibold">Analysis Failed</p>
                    <p className="text-rose-300 mt-0.5">{analysisError}</p>
                  </div>
                </div>
              )}

              {/* Structured Analysis Results View */}
              {analysisResult && (
                <div className="space-y-4">
                  {/* OCR Warning Banner if Scanned */}
                  {analysisResult.needs_ocr && (
                    <div className="p-4 rounded-xl bg-amber-950/50 border border-amber-800 text-amber-200 flex items-start gap-3">
                      <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                      <div className="text-sm">
                        <p className="font-semibold">OCR Required</p>
                        <p className="text-amber-300 mt-0.5">
                          This document contains scanned or non-digital image pages with no selectable text layer.
                          Document Agent extracted zero digital characters. An OCR engine is required.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Summary & Classification Card */}
                  <Card className="space-y-4">
                    <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                      <div className="flex items-center gap-2">
                        <Tag className="w-4 h-4 text-indigo-400" />
                        <span className="text-xs uppercase font-mono tracking-wider text-indigo-300 font-semibold">
                          {analysisResult.document_type}
                        </span>
                        <span className="text-xs text-slate-500">•</span>
                        <span className="text-xs text-slate-400">
                          Confidence: {(analysisResult.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      {analysisResult.execution_time_ms && (
                        <span className="text-xs text-slate-500">
                          Latency: {analysisResult.execution_time_ms}ms
                        </span>
                      )}
                    </div>

                    {/* Executive Summary */}
                    <div>
                      <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                        Executive Summary
                      </h3>
                      <p className="text-sm text-slate-200 leading-relaxed bg-slate-950 p-3.5 rounded-lg border border-slate-800/80">
                        {analysisResult.summary || 'No summary available.'}
                      </p>
                    </div>

                    {/* Key Points */}
                    {analysisResult.key_points && analysisResult.key_points.length > 0 && (
                      <div>
                        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                          Key Points & Findings
                        </h3>
                        <ul className="space-y-2">
                          {analysisResult.key_points.map((pt, idx) => (
                            <li
                              key={idx}
                              className="text-xs text-slate-300 flex items-start gap-2 bg-slate-950/60 p-2.5 rounded border border-slate-800/60"
                            >
                              <span className="text-indigo-400 font-bold shrink-0">•</span>
                              <span>{pt}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Domain Structured Data (Invoices, Policies, Manuals) */}
                    {analysisResult.structured_data && Object.keys(analysisResult.structured_data).length > 0 && (
                      <div>
                        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                          Extracted Domain Information
                        </h3>
                        <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800/80 overflow-x-auto">
                          {analysisResult.document_type === 'INVOICE' && analysisResult.structured_data.vendor ? (
                            <div className="space-y-3">
                              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                                <div>
                                  <span className="text-slate-500">Vendor:</span>
                                  <p className="font-semibold text-slate-200">{analysisResult.structured_data.vendor}</p>
                                </div>
                                <div>
                                  <span className="text-slate-500">Invoice #:</span>
                                  <p className="font-semibold text-slate-200">{analysisResult.structured_data.invoice_number}</p>
                                </div>
                                <div>
                                  <span className="text-slate-500">Date:</span>
                                  <p className="font-semibold text-slate-200">{analysisResult.structured_data.date}</p>
                                </div>
                                <div>
                                  <span className="text-slate-500">Subtotal:</span>
                                  <p className="font-semibold text-slate-200">{analysisResult.structured_data.subtotal}</p>
                                </div>
                                <div>
                                  <span className="text-slate-500">Tax:</span>
                                  <p className="font-semibold text-slate-200">{analysisResult.structured_data.tax}</p>
                                </div>
                                <div>
                                  <span className="text-slate-500">Total:</span>
                                  <p className="font-bold text-emerald-400 text-sm">
                                    {analysisResult.structured_data.total} {analysisResult.structured_data.currency}
                                  </p>
                                </div>
                              </div>

                              {analysisResult.structured_data.line_items?.length > 0 && (
                                <div className="mt-3">
                                  <p className="text-xs font-semibold text-slate-400 mb-1.5">Line Items</p>
                                  <table className="w-full text-xs text-left text-slate-300">
                                    <thead className="bg-slate-900 text-slate-400 border-b border-slate-800">
                                      <tr>
                                        <th className="p-2">Description</th>
                                        <th className="p-2 text-right">Qty</th>
                                        <th className="p-2 text-right">Price</th>
                                        <th className="p-2 text-right">Total</th>
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-800/60">
                                      {analysisResult.structured_data.line_items.map((item: any, i: number) => (
                                        <tr key={i}>
                                          <td className="p-2">{item.description}</td>
                                          <td className="p-2 text-right">{item.quantity}</td>
                                          <td className="p-2 text-right">{item.unit_price}</td>
                                          <td className="p-2 text-right font-semibold text-slate-100">{item.total}</td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              )}
                            </div>
                          ) : (
                            <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap">
                              {JSON.stringify(analysisResult.structured_data, null, 2)}
                            </pre>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Source Citations */}
                    {analysisResult.sources && analysisResult.sources.length > 0 && (
                      <div>
                        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                          <Hash className="w-3.5 h-3.5 text-indigo-400" />
                          Source Citations & Provenance
                        </h3>
                        <div className="flex flex-wrap gap-2">
                          {analysisResult.sources.map((src, i) => (
                            <span
                              key={i}
                              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-[11px] text-slate-300"
                            >
                              <span className="font-semibold text-indigo-300">{src.field}:</span>
                              <span>{src.value}</span>
                              {src.source?.page && (
                                <span className="bg-indigo-950/80 text-indigo-400 px-1.5 py-0.2 rounded border border-indigo-800/80 font-mono text-[10px]">
                                  Page {src.source.page}
                                </span>
                              )}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </Card>
                </div>
              )}
            </>
          ) : (
            <Card className="py-24 text-center text-slate-500">
              <Search className="w-10 h-10 mx-auto text-slate-600 mb-3" />
              <p className="text-base font-semibold text-slate-300">No Document Selected</p>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                Select a document from the list on the left or upload a new file to analyze.
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
