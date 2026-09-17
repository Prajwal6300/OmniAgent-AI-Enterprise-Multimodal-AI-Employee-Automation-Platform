import React, { useState, useRef } from 'react';
import {
  Eye,
  Upload,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Scan,
  ShieldCheck,
  ShieldAlert,
  Sparkles,
  Layers,
  FileText,
  X,
  Target,
  Maximize2,
  Sliders,
  Tag,
  Check,
  Info,
  Clock
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { visionService } from '@/services/vision/visionService';
import {
  ImageArtifact,
  VisionAnalysisData,
  VisionDetection,
  VisualFindingData,
  OCRRegion
} from '@/types';

const ENTERPRISE_PROMPT_SUGGESTIONS = [
  "Are there any visible damaged components?",
  "Analyze this machine inspection image.",
  "Read the serial number from this image.",
  "What components are present?",
  "Identify safety issues visible in this image.",
  "Compare the visible condition against the provided inspection criteria.",
];

export default function ImageAnalysisPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploadedArtifact, setUploadedArtifact] = useState<ImageArtifact | null>(null);
  const [analysisResult, setAnalysisResult] = useState<VisionAnalysisData | null>(null);

  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const [question, setQuestion] = useState('');
  const [taskType, setTaskType] = useState<string>('');
  const [showOverlays, setShowOverlays] = useState<boolean>(true);
  const [activeHighlight, setActiveHighlight] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageContainerRef = useRef<HTMLDivElement>(null);

  // Handle File Selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Reset previous state
    setSelectedFile(file);
    setUploadedArtifact(null);
    setAnalysisResult(null);
    setUploadError(null);
    setAnalysisError(null);

    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
  };

  const handleClearImage = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setUploadedArtifact(null);
    setAnalysisResult(null);
    setUploadError(null);
    setAnalysisError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Upload and execute analysis
  const handleAnalyze = async () => {
    if (!selectedFile && !uploadedArtifact) {
      setUploadError("Please select or upload an image first.");
      return;
    }

    const queryText = question.trim() || "Analyze visible machine components, defects, and inscriptions.";
    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      let imageId = uploadedArtifact?.id;

      // 1. Upload if not already uploaded
      if (!imageId && selectedFile) {
        setIsUploading(true);
        const uploaded = await visionService.uploadImage(selectedFile);
        setUploadedArtifact(uploaded);
        imageId = uploaded.id;
        setIsUploading(false);
      }

      if (!imageId) {
        throw new Error("Unable to establish image artifact identity.");
      }

      // 2. Execute Vision Agent LangGraph Analysis
      const result = await visionService.analyzeImage(
        imageId,
        queryText,
        taskType || undefined
      );

      setAnalysisResult(result);
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || err.message || "Vision analysis failed.";
      setAnalysisError(msg);
    } finally {
      setIsUploading(false);
      setIsAnalyzing(false);
    }
  };

  const getSeverityBadge = (severity?: string) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-rose-950/80 text-rose-300 border border-rose-800/80">CRITICAL</span>;
      case 'HIGH':
        return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-orange-950/80 text-orange-300 border border-orange-800/80">HIGH</span>;
      case 'MEDIUM':
        return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-amber-950/80 text-amber-300 border border-amber-800/80">MEDIUM</span>;
      case 'LOW':
        return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800/80">LOW</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-blue-950/80 text-blue-300 border border-blue-800/80">INFO</span>;
    }
  };

  const getStatusBadge = (status?: string) => {
    switch (status?.toUpperCase()) {
      case 'SUCCESS':
      case 'AVAILABLE':
        return <span className="inline-flex items-center gap-1 text-xs text-emerald-400 font-medium"><Check className="w-3 h-3" /> Available</span>;
      case 'SKIPPED':
        return <span className="inline-flex items-center gap-1 text-xs text-slate-400 font-medium"><Clock className="w-3 h-3" /> Skipped</span>;
      case 'UNAVAILABLE':
      default:
        return <span className="inline-flex items-center gap-1 text-xs text-amber-400 font-medium"><Info className="w-3 h-3" /> Unavailable</span>;
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
              <Eye className="w-7 h-7 text-indigo-400" />
              Vision Intelligence & Industrial Inspection
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-medium bg-indigo-950 text-indigo-300 border border-indigo-800 rounded-full">
              Day 5 Agent
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Multimodal visual inspection, damage assessment, OCR inscription reading, and component localization.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {previewUrl && (
            <Button variant="outline" size="sm" onClick={handleClearImage}>
              <X className="w-4 h-4 mr-1.5" /> Clear Image
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Image Ingestion & Visual Workspace */}
        <div className="lg:col-span-6 space-y-6">
          <Card className="relative overflow-hidden">
            <div className="flex items-center justify-between mb-4 border-b border-slate-800/80 pb-3">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <Scan className="w-4 h-4 text-indigo-400" />
                Image Artifact Workspace
              </h2>
              {previewUrl && (
                <div className="flex items-center gap-2">
                  <label className="text-xs text-slate-400 flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={showOverlays}
                      onChange={(e) => setShowOverlays(e.target.checked)}
                      className="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-0"
                    />
                    Show Annotations
                  </label>
                </div>
              )}
            </div>

            {/* Ingestion Dropzone or Image Preview */}
            {!previewUrl ? (
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-700/80 hover:border-indigo-500/80 rounded-xl p-8 text-center cursor-pointer transition-colors bg-slate-900/40 hover:bg-slate-800/30 group"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".jpg,.jpeg,.png,.webp"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <div className="mx-auto w-14 h-14 rounded-full bg-slate-800 flex items-center justify-center text-slate-400 group-hover:text-indigo-400 group-hover:bg-indigo-950/60 transition-colors mb-4 border border-slate-700">
                  <Upload className="w-6 h-6" />
                </div>
                <h3 className="text-base font-medium text-slate-200">Upload an inspection image</h3>
                <p className="text-xs text-slate-400 mt-1.5 max-w-sm mx-auto">
                  Drag and drop JPEG, PNG, or WEBP inspection photos, schematics, or machine nameplates (up to 10 MB).
                </p>
                <div className="mt-4 flex items-center justify-center gap-2">
                  <span className="px-2 py-0.5 text-[11px] bg-slate-800 text-slate-300 rounded border border-slate-700">JPEG</span>
                  <span className="px-2 py-0.5 text-[11px] bg-slate-800 text-slate-300 rounded border border-slate-700">PNG</span>
                  <span className="px-2 py-0.5 text-[11px] bg-slate-800 text-slate-300 rounded border border-slate-700">WEBP</span>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {/* Visual Canvas Container with Coordinates Overlay */}
                <div
                  ref={imageContainerRef}
                  className="relative rounded-lg overflow-hidden bg-slate-950 border border-slate-800 flex items-center justify-center max-h-[460px]"
                >
                  <img
                    src={previewUrl}
                    alt="Artifact under inspection"
                    className="max-h-[460px] w-auto object-contain select-none"
                  />

                  {/* Grounded Object Bounding Boxes Overlay */}
                  {showOverlays && analysisResult && analysisResult.detected_objects && (
                    <div className="absolute inset-0 pointer-events-none">
                      {analysisResult.detected_objects.map((obj, idx) => {
                        if (!obj.bbox || obj.bbox.length < 4) return null;
                        const [ymin, xmin, ymax, xmax] = obj.bbox;
                        // Determine whether coordinates are normalized (0-1) or pixel-based
                        const isNormalized = ymax <= 1.0 && xmax <= 1.0;
                        const top = isNormalized ? `${ymin * 100}%` : `${ymin}px`;
                        const left = isNormalized ? `${xmin * 100}%` : `${xmin}px`;
                        const height = isNormalized ? `${(ymax - ymin) * 100}%` : `${ymax - ymin}px`;
                        const width = isNormalized ? `${(xmax - xmin) * 100}%` : `${xmax - xmin}px`;

                        const isActive = activeHighlight === obj.label;

                        return (
                          <div
                            key={idx}
                            style={{ top, left, width, height }}
                            className={`absolute border-2 transition-all ${
                              isActive
                                ? 'border-amber-400 bg-amber-400/20 shadow-lg shadow-amber-500/30 z-20'
                                : 'border-indigo-400/80 bg-indigo-500/10'
                            }`}
                          >
                            <span className="absolute -top-5 left-0 bg-slate-900/90 text-indigo-300 border border-indigo-500/50 text-[10px] font-semibold px-1.5 py-0.5 rounded shadow whitespace-nowrap">
                              {obj.label} ({(obj.confidence * 100).toFixed(0)}%)
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Metadata Details Bar */}
                <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 text-xs text-slate-400">
                  <div className="flex items-center gap-2 truncate">
                    <span className="font-medium text-slate-200 truncate">
                      {selectedFile?.name || uploadedArtifact?.file_name || "image.jpg"}
                    </span>
                    {selectedFile && (
                      <span className="text-slate-500">
                        ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    {uploadedArtifact && (
                      <span className="text-emerald-400 font-mono text-[11px] flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> ID: {uploadedArtifact.id.slice(0, 8)}...
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )}

            {uploadError && (
              <div className="mt-3 p-3 rounded-lg bg-rose-950/40 border border-rose-800/80 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}
          </Card>

          {/* Prompt & Task Controls Card */}
          <Card>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5 flex items-center justify-between">
                  <span>Inquiry & Task Configuration</span>
                  <span className="text-slate-500 font-normal">Step 2</span>
                </label>

                {/* Task Selector */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
                  {[
                    { id: '', label: 'Auto-Detect' },
                    { id: 'VISUAL_INSPECTION', label: 'Inspection' },
                    { id: 'DAMAGE_ANALYSIS', label: 'Damage' },
                    { id: 'OCR', label: 'Read Text' },
                    { id: 'COMPONENT_IDENTIFICATION', label: 'Components' },
                    { id: 'SAFETY_ANALYSIS', label: 'Safety' },
                    { id: 'OBJECT_DETECTION', label: 'Objects' },
                    { id: 'GENERAL_IMAGE_ANALYSIS', label: 'General' },
                  ].map((t) => (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setTaskType(t.id)}
                      className={`px-2.5 py-1.5 text-xs rounded-lg border font-medium transition-colors text-center truncate ${
                        taskType === t.id
                          ? 'bg-indigo-600 text-white border-indigo-500 shadow-sm'
                          : 'bg-slate-800/80 text-slate-300 border-slate-700 hover:bg-slate-800'
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>

                {/* Question Input */}
                <div className="relative">
                  <textarea
                    rows={3}
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Enter your inspection question, e.g. Are there any visible cracks, corrosion, or damaged components?"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 transition-colors resize-none"
                  />
                </div>
              </div>

              {/* Quick Enterprise Prompts */}
              <div>
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block mb-2">
                  Sample Enterprise Inquiries:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {ENTERPRISE_PROMPT_SUGGESTIONS.map((promptText, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setQuestion(promptText)}
                      className="text-left px-2.5 py-1 text-xs rounded-md bg-slate-800/60 hover:bg-slate-800 text-slate-300 border border-slate-700/60 transition-colors"
                    >
                      {promptText}
                    </button>
                  ))}
                </div>
              </div>

              <div className="pt-2">
                <Button
                  onClick={handleAnalyze}
                  disabled={isAnalyzing || isUploading || (!selectedFile && !uploadedArtifact)}
                  className="w-full py-2.5 font-semibold text-sm shadow-md"
                >
                  {isAnalyzing ? (
                    <span className="flex items-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Analyzing image…
                    </span>
                  ) : isUploading ? (
                    <span className="flex items-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Persisting image artifact…
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4" />
                      Execute Vision Analysis
                    </span>
                  )}
                </Button>
              </div>

              {analysisError && (
                <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800/80 text-rose-300 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{analysisError}</span>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Right Column: Structured Intelligence & Findings */}
        <div className="lg:col-span-6 space-y-6">
          {/* Processor Capabilities & Partial Failure Status */}
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Engine Statuses
              </span>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-slate-400">Vision:</span>
                  {getStatusBadge(analysisResult?.component_statuses?.vision_model || 'AVAILABLE')}
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-slate-400">OCR:</span>
                  {getStatusBadge(analysisResult?.component_statuses?.ocr || 'AVAILABLE')}
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-slate-400">Detector:</span>
                  {getStatusBadge(analysisResult?.component_statuses?.object_detection || 'UNAVAILABLE')}
                </div>
              </div>
            </div>
          </Card>

          {/* Analysis Results View */}
          {analysisResult ? (
            <div className="space-y-6">
              {/* Executive Answer Card */}
              <Card className="border-indigo-950/80 bg-slate-900/90 shadow-md">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400">
                      Vision Analysis
                    </span>
                    <span className="px-2 py-0.5 text-[11px] rounded font-medium bg-slate-800 text-slate-300 border border-slate-700">
                      {analysisResult.task_type}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-slate-400">
                    <span>Confidence:</span>
                    <span className="font-semibold text-emerald-400">
                      {(analysisResult.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                <div className="prose prose-invert max-w-none text-sm text-slate-200 whitespace-pre-line leading-relaxed font-sans">
                  {analysisResult.answer}
                </div>

                {analysisResult.summary && analysisResult.summary !== analysisResult.answer && (
                  <p className="mt-3 text-xs text-slate-400 italic border-t border-slate-800/80 pt-2">
                    Summary: {analysisResult.summary}
                  </p>
                )}
              </Card>

              {/* Structured Findings List */}
              {analysisResult.findings && analysisResult.findings.length > 0 && (
                <Card>
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
                    <Layers className="w-4 h-4 text-indigo-400" />
                    Inspection Findings ({analysisResult.findings.length})
                  </h3>
                  <div className="space-y-2.5">
                    {analysisResult.findings.map((f, i) => (
                      <div
                        key={i}
                        className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-colors"
                      >
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <span className="text-sm font-semibold text-slate-200">{f.title}</span>
                          <div className="flex items-center gap-2">
                            {f.category && (
                              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono">
                                {f.category}
                              </span>
                            )}
                            {getSeverityBadge(f.severity)}
                          </div>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed">{f.description}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Detected Objects Grid */}
              {analysisResult.detected_objects && analysisResult.detected_objects.length > 0 && (
                <Card>
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
                    <Target className="w-4 h-4 text-indigo-400" />
                    Detected Objects & Classes ({analysisResult.detected_objects.length})
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {analysisResult.detected_objects.map((obj, i) => (
                      <button
                        key={i}
                        type="button"
                        onMouseEnter={() => setActiveHighlight(obj.label)}
                        onMouseLeave={() => setActiveHighlight(null)}
                        className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-indigo-500 text-xs text-slate-200 flex items-center gap-2 transition-colors cursor-pointer"
                      >
                        <span className="font-medium">{obj.label}</span>
                        <span className="text-slate-400 font-mono text-[11px]">
                          {(obj.confidence * 100).toFixed(0)}%
                        </span>
                      </button>
                    ))}
                  </div>
                </Card>
              )}

              {/* OCR Inscriptions View */}
              {analysisResult.ocr_result && analysisResult.ocr_result.text && (
                <Card>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-indigo-400" />
                      Detected Text (OCR)
                    </h3>
                    <span className="text-xs text-slate-400">
                      Confidence: {(analysisResult.ocr_result.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-slate-200 whitespace-pre-wrap leading-relaxed">
                    {analysisResult.ocr_result.text}
                  </div>
                </Card>
              )}

              {/* Evidence Citations */}
              {analysisResult.citations && analysisResult.citations.length > 0 && (
                <Card>
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-indigo-400" />
                    Grounded Visual Evidence ({analysisResult.citations.length})
                  </h3>
                  <div className="space-y-2">
                    {analysisResult.citations.map((c, i) => (
                      <div
                        key={i}
                        className="text-xs p-2.5 rounded bg-slate-950/40 border border-slate-800 text-slate-300 flex items-start gap-2.5"
                      >
                        <Tag className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0 mt-0.5" />
                        <div>
                          <span className="font-semibold text-slate-200">{c.label}</span>
                          {c.details && <p className="text-slate-400 mt-0.5">{c.details}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Security Notices / Warnings */}
              {analysisResult.warnings && analysisResult.warnings.length > 0 && (
                <Card className="border-amber-900/50 bg-amber-950/20">
                  <h4 className="text-xs font-semibold uppercase text-amber-300 mb-2 flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4 text-amber-400" />
                    Operational & Security Notices
                  </h4>
                  <ul className="text-xs text-amber-200/90 space-y-1 list-disc pl-4">
                    {analysisResult.warnings.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </Card>
              )}
            </div>
          ) : (
            <Card className="h-64 flex flex-col items-center justify-center text-center p-8 text-slate-400">
              <Eye className="w-12 h-12 text-slate-700 mb-3" />
              <h3 className="text-sm font-medium text-slate-300">Ready for Image Analysis</h3>
              <p className="text-xs text-slate-500 max-w-sm mt-1">
                Upload an image on the left, choose an inquiry prompt or type your custom question, then click Analyze.
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
