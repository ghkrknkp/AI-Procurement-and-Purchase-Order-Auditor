import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import type {
  DocumentDetail,
  ComparisonResponse
} from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { useAuth } from '../auth/AuthContext';
import {
  FileText,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCcw,
  Send,
  Save,
  MessageSquare,
  History,
  GitCompare,
  PlusCircle,
  Info,
  Calendar,
  User,
  ExternalLink,
  Scale
} from 'lucide-react';

export const DocumentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { isReviewer, isSubmitter } = useAuth();

  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'fields' | 'comparison' | 'review' | 'history'>('fields');

  // Form states for editable fields
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [isSavingFields, setIsSavingFields] = useState(false);
  const [fieldSaveMessage, setFieldSaveMessage] = useState<string | null>(null);

  // Reviewer action modals
  const [commentText, setCommentText] = useState('');
  const [actionReason, setActionReason] = useState('');
  const [actionModal, setActionModal] = useState<'approve' | 'reject' | 'correct' | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  // Purchase order modal
  const [showPoModal, setShowPoModal] = useState(false);
  const [poNumber, setPoNumber] = useState('');
  const [poVendor, setPoVendor] = useState('');
  const [poDate, setPoDate] = useState('');
  const [poItems, setPoItems] = useState<{ description: string; quantity: number; unit_price: number; line_total: number }[]>([
    { description: '', quantity: 1, unit_price: 0, line_total: 0 }
  ]);

  const fetchDocument = async () => {
    try {
      const res = await apiClient.get<DocumentDetail>(`/documents/${id}`);
      setDocument(res.data);

      // Populate local field editing state
      const fMap: Record<string, string> = {};
      res.data.extracted_fields.forEach((f) => {
        fMap[f.field_name] = f.field_value || '';
      });
      setFieldValues(fMap);

      // Fetch PO comparison if PO exists or to check comparison status
      fetchComparison();
    } catch (err) {
      console.error('Failed to load document details', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchComparison = async () => {
    try {
      const compRes = await apiClient.get<ComparisonResponse>(`/documents/${id}/comparison`);
      setComparison(compRes.data);
    } catch (err) {
      console.error('Failed to load comparison data', err);
    }
  };

  useEffect(() => {
    fetchDocument();
  }, [id]);

  const handleFieldChange = (fieldName: string, value: string) => {
    setFieldValues((prev) => ({ ...prev, [fieldName]: value }));
  };

  const handleSaveFields = async () => {
    setIsSavingFields(true);
    setFieldSaveMessage(null);
    try {
      const res = await apiClient.patch<DocumentDetail>(`/documents/${id}/fields`, {
        fields: fieldValues,
      });
      setDocument(res.data);
      setFieldSaveMessage('Extracted fields saved successfully.');
      fetchComparison();
    } catch (err: any) {
      setFieldSaveMessage(err.response?.data?.detail || 'Failed to save field changes.');
    } finally {
      setIsSavingFields(false);
      setTimeout(() => setFieldSaveMessage(null), 4000);
    }
  };

  const handleSubmitForReview = async () => {
    if (!window.confirm('Submit this document for official reviewer evaluation?')) return;
    try {
      const res = await apiClient.post<DocumentDetail>(`/documents/${id}/submit`);
      setDocument(res.data);
      alert('Document submitted successfully!');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Submission failed.');
    }
  };

  const handleReprocess = async () => {
    if (!window.confirm('Re-run OCR and extraction on this document?')) return;
    setLoading(true);
    try {
      const res = await apiClient.post<DocumentDetail>(`/documents/${id}/process`);
      setDocument(res.data);
      fetchComparison();
      alert('Extraction re-processed.');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Re-processing failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    try {
      await apiClient.post(`/documents/${id}/reviews`, { comment: commentText.trim() });
      setCommentText('');
      fetchDocument();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to add comment.');
    }
  };

  const handleExecuteReviewAction = async () => {
    setActionLoading(true);
    try {
      if (actionModal === 'approve') {
        const res = await apiClient.post<DocumentDetail>(`/documents/${id}/approve`, {
          reason: actionReason || 'Document approved by reviewer.',
        });
        setDocument(res.data);
      } else if (actionModal === 'reject') {
        const res = await apiClient.post<DocumentDetail>(`/documents/${id}/reject`, {
          reason: actionReason || 'Document rejected by reviewer.',
        });
        setDocument(res.data);
      } else if (actionModal === 'correct') {
        if (!actionReason.trim()) {
          alert('A reason is mandatory when requesting corrections.');
          setActionLoading(false);
          return;
        }
        const res = await apiClient.post<DocumentDetail>(`/documents/${id}/request-corrections`, {
          reason: actionReason,
        });
        setDocument(res.data);
      }
      setActionModal(null);
      setActionReason('');
      fetchComparison();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Action failed.');
    } finally {
      setActionLoading(false);
    }
  };

  const handlePoItemChange = (index: number, key: string, value: any) => {
    const updated = [...poItems];
    (updated[index] as any)[key] = value;
    if (key === 'quantity' || key === 'unit_price') {
      const q = key === 'quantity' ? parseFloat(value) || 0 : updated[index].quantity;
      const p = key === 'unit_price' ? parseFloat(value) || 0 : updated[index].unit_price;
      updated[index].line_total = parseFloat((q * p).toFixed(2));
    }
    setPoItems(updated);
  };

  const handleAddPoItem = () => {
    setPoItems([...poItems, { description: '', quantity: 1, unit_price: 0, line_total: 0 }]);
  };

  const handleRemovePoItem = (index: number) => {
    if (poItems.length > 1) {
      setPoItems(poItems.filter((_, idx) => idx !== index));
    }
  };

  const handleSavePurchaseOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post(`/documents/${id}/purchase-order`, {
        purchase_order_number: poNumber,
        vendor_name: poVendor,
        order_date: poDate,
        currency: 'USD',
        items: poItems,
      });
      setShowPoModal(false);
      fetchDocument();
      fetchComparison();
      setActiveTab('comparison');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to attach purchase order.');
    }
  };

  if (loading || !document) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-10 h-10 border-4 border-brand-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const isEditable = (isSubmitter && document.workflow_status === 'draft') || isReviewer;
  const fileUrl = `${apiClient.defaults.baseURL}/documents/${document.id}/file`;
  const isImage = document.mime_type.startsWith('image/');

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Breadcrumb & Navigation */}
      <div className="flex items-center justify-between">
        <Link
          to="/documents"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Documents Queue
        </Link>

        <div className="flex items-center gap-2">
          <button
            onClick={handleReprocess}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-2xs"
            title="Re-run OCR extraction"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Re-run OCR
          </button>
        </div>
      </div>

      {/* Main Document Summary Card */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center flex-shrink-0 shadow-2xs">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2.5 mb-1">
              <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight">
                {document.original_filename}
              </h1>
              <span className="text-xs font-mono bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md">
                Doc #{document.id}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <User className="w-3.5 h-3.5" /> Submitter: <strong>{document.owner_name}</strong>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" /> Uploaded: {new Date(document.created_at).toLocaleDateString()}
              </span>
              <span>•</span>
              <span>{(document.file_size / 1024).toFixed(1)} KB</span>
            </div>
          </div>
        </div>

        {/* Status Indicators & Action Buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex flex-col items-end gap-1.5">
            <div className="flex items-center gap-2">
              <StatusBadge status={document.processing_status} type="processing" />
              <StatusBadge status={document.workflow_status} type="workflow" />
            </div>
          </div>

          {/* Workflow Action Buttons */}
          {isSubmitter && document.workflow_status === 'draft' && (
            <button
              onClick={handleSubmitForReview}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs transition-all shadow-sm"
            >
              <Send className="w-3.5 h-3.5" />
              Submit for Review
            </button>
          )}

          {isReviewer && document.workflow_status === 'submitted' && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActionModal('approve')}
                className="inline-flex items-center gap-1 px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition-all shadow-sm"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                Approve
              </button>
              <button
                onClick={() => setActionModal('correct')}
                className="inline-flex items-center gap-1 px-3 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-semibold text-xs transition-all shadow-sm"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Request Corrections
              </button>
              <button
                onClick={() => setActionModal('reject')}
                className="inline-flex items-center gap-1 px-3 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs transition-all shadow-sm"
              >
                <XCircle className="w-3.5 h-3.5" />
                Reject
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Split Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Document File Preview (5 cols) */}
        <div className="lg:col-span-5 bg-white rounded-3xl border border-slate-200/80 shadow-xs overflow-hidden sticky top-24">
          <div className="p-4 bg-slate-50/75 border-b border-slate-200 flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-brand-600" />
              Source Document Preview
            </span>
            <a
              href={fileUrl}
              target="_blank"
              rel="noreferrer"
              className="text-xs font-semibold text-brand-600 hover:text-brand-800 flex items-center gap-1"
            >
              Open in new tab <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="h-[620px] bg-slate-100 flex items-center justify-center overflow-auto p-2">
            {isImage ? (
              <img
                src={fileUrl}
                alt="Invoice Preview"
                className="max-h-full max-w-full object-contain rounded-lg shadow-sm"
              />
            ) : (
              <iframe
                src={`${fileUrl}#toolbar=0`}
                title="PDF Preview"
                className="w-full h-full rounded-lg border border-slate-200 bg-white"
              />
            )}
          </div>
        </div>

        {/* Right Column: Tabbed Workspace (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Navigation Tabs */}
          <div className="bg-white p-1.5 rounded-2xl border border-slate-200/80 shadow-xs flex items-center gap-1">
            <button
              onClick={() => setActiveTab('fields')}
              className={`flex-1 py-2 px-3 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                activeTab === 'fields'
                  ? 'bg-brand-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              Invoice Fields & Rules
              {document.validation_warnings.length > 0 && (
                <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-amber-400 text-slate-950 font-bold">
                  {document.validation_warnings.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('comparison')}
              className={`flex-1 py-2 px-3 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                activeTab === 'comparison'
                  ? 'bg-brand-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <GitCompare className="w-3.5 h-3.5" />
              PO Reconciliation
              {comparison?.has_critical_mismatches && (
                <span className="ml-1 w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('review')}
              className={`flex-1 py-2 px-3 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                activeTab === 'review'
                  ? 'bg-brand-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              Comments ({document.review_comments.length})
            </button>

            <button
              onClick={() => setActiveTab('history')}
              className={`flex-1 py-2 px-3 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                activeTab === 'history'
                  ? 'bg-brand-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <History className="w-3.5 h-3.5" />
              Audit Log ({document.workflow_history.length})
            </button>
          </div>

          {/* TAB 1: INVOICE FIELDS & VALIDATION */}
          {activeTab === 'fields' && (
            <div className="space-y-6">
              {/* Validation Warnings Alert Banner */}
              {document.validation_warnings.length > 0 && (
                <div className="bg-amber-50/90 border border-amber-200/90 rounded-2xl p-4 space-y-2">
                  <div className="flex items-center gap-2 text-amber-900 font-bold text-xs uppercase tracking-wider">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    Validation Diagnostic Alerts ({document.validation_warnings.length})
                  </div>
                  <div className="space-y-1.5 pt-1">
                    {document.validation_warnings.map((w, idx) => (
                      <div
                        key={idx}
                        className={`text-xs p-2.5 rounded-xl border flex items-start gap-2 ${
                          w.severity === 'error'
                            ? 'bg-rose-50/80 border-rose-200 text-rose-800'
                            : 'bg-white border-amber-200 text-amber-900'
                        }`}
                      >
                        <span className="font-bold uppercase text-[10px] px-1.5 py-0.5 rounded bg-amber-200/60 text-amber-900">
                          {w.rule.replace('_', ' ')}
                        </span>
                        <span>{w.message}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Editable Fields Form */}
              <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 space-y-6">
                <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                  <div>
                    <h3 className="text-base font-bold text-slate-900">Extracted Invoice Metadata</h3>
                    <p className="text-xs text-slate-500">
                      {isEditable
                        ? 'Review and adjust extracted invoice fields before submission.'
                        : 'Fields are locked while under review or approved.'}
                    </p>
                  </div>

                  {isEditable && (
                    <button
                      onClick={handleSaveFields}
                      disabled={isSavingFields}
                      className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold shadow-2xs transition-all disabled:opacity-50"
                    >
                      <Save className="w-3.5 h-3.5" />
                      {isSavingFields ? 'Saving...' : 'Save Changes'}
                    </button>
                  )}
                </div>

                {fieldSaveMessage && (
                  <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium">
                    {fieldSaveMessage}
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Invoice Number */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-700">Invoice Number</label>
                    <input
                      type="text"
                      disabled={!isEditable}
                      value={fieldValues['invoice_number'] || ''}
                      onChange={(e) => handleFieldChange('invoice_number', e.target.value)}
                      placeholder="e.g. INV-2026-101"
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:bg-slate-50"
                    />
                  </div>

                  {/* Vendor Name */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-700">Vendor Name</label>
                    <input
                      type="text"
                      disabled={!isEditable}
                      value={fieldValues['vendor_name'] || ''}
                      onChange={(e) => handleFieldChange('vendor_name', e.target.value)}
                      placeholder="e.g. TechCorp Solutions Inc"
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:bg-slate-50"
                    />
                  </div>

                  {/* Invoice Date */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-700">Invoice Date</label>
                    <input
                      type="text"
                      disabled={!isEditable}
                      value={fieldValues['invoice_date'] || ''}
                      onChange={(e) => handleFieldChange('invoice_date', e.target.value)}
                      placeholder="YYYY-MM-DD"
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:bg-slate-50"
                    />
                  </div>

                  {/* Currency */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-700">Currency</label>
                    <select
                      disabled={!isEditable}
                      value={fieldValues['currency'] || 'USD'}
                      onChange={(e) => handleFieldChange('currency', e.target.value)}
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:bg-slate-50"
                    >
                      <option value="USD">USD ($)</option>
                      <option value="EUR">EUR (€)</option>
                      <option value="GBP">GBP (£)</option>
                      <option value="CAD">CAD ($)</option>
                    </select>
                  </div>

                  {/* Subtotal */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-700">Subtotal Amount</label>
                    <input
                      type="text"
                      disabled={!isEditable}
                      value={fieldValues['subtotal'] || ''}
                      onChange={(e) => handleFieldChange('subtotal', e.target.value)}
                      placeholder="0.00"
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:bg-slate-50"
                    />
                  </div>

                  {/* Tax Amount */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-700">Tax Amount</label>
                    <input
                      type="text"
                      disabled={!isEditable}
                      value={fieldValues['tax_amount'] || ''}
                      onChange={(e) => handleFieldChange('tax_amount', e.target.value)}
                      placeholder="0.00"
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:bg-slate-50"
                    />
                  </div>

                  {/* Total Amount */}
                  <div className="space-y-1.5 sm:col-span-2">
                    <label className="text-xs font-semibold text-slate-700">Total Billed Amount</label>
                    <input
                      type="text"
                      disabled={!isEditable}
                      value={fieldValues['total_amount'] || ''}
                      onChange={(e) => handleFieldChange('total_amount', e.target.value)}
                      placeholder="0.00"
                      className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-bold text-brand-900 focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:bg-slate-50 text-base"
                    />
                  </div>
                </div>

                {/* Evidence & Confidence Metrics */}
                <div className="pt-4 border-t border-slate-100">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                    OCR Confidence & Extraction Evidence Snippets
                  </h4>
                  <div className="space-y-2">
                    {document.extracted_fields.map((f) => (
                      <div
                        key={f.id}
                        className="p-2.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-800 capitalize">
                            {f.field_name.replace('_', ' ')}:
                          </span>
                          <span className="text-slate-600 font-mono text-[11px] truncate max-w-xs">
                            {f.source_text || f.field_value || 'None'}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-slate-400">P.{f.source_page || 1}</span>
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              (f.confidence || 0) >= 0.85
                                ? 'bg-emerald-100 text-emerald-800'
                                : (f.confidence || 0) >= 0.6
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-rose-100 text-rose-800'
                            }`}
                          >
                            {f.confidence !== null ? `${Math.round(f.confidence * 100)}%` : 'Manual'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: PURCHASE ORDER COMPARISON & RECONCILIATION */}
          {activeTab === 'comparison' && (
            <div className="space-y-6">
              {/* PO Header / Attach PO */}
              <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <Scale className="w-5 h-5 text-brand-600" />
                    <h3 className="text-base font-bold text-slate-900">
                      Purchase Order 3-Way Reconciliation
                    </h3>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    Automated line-item, price, quantity, and vendor verification engine.
                  </p>
                </div>

                <button
                  onClick={() => {
                    if (document.purchase_orders.length > 0) {
                      const existing = document.purchase_orders[0];
                      setPoNumber(existing.purchase_order_number);
                      setPoVendor(existing.vendor_name);
                      setPoDate(existing.order_date || '');
                      setPoItems(
                        existing.items.map((i) => ({
                          description: i.description,
                          quantity: i.quantity,
                          unit_price: i.unit_price,
                          line_total: i.line_total,
                        }))
                      );
                    } else {
                      setPoNumber('PO-2026-');
                      setPoVendor(fieldValues['vendor_name'] || '');
                      setPoDate('2026-10-10');
                      setPoItems([{ description: '', quantity: 1, unit_price: 0, line_total: 0 }]);
                    }
                    setShowPoModal(true);
                  }}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-2xs transition-all"
                >
                  <PlusCircle className="w-4 h-4 text-brand-400" />
                  {document.purchase_orders.length > 0 ? 'Edit Attached PO' : 'Attach Purchase Order'}
                </button>
              </div>

              {/* Comparison Summary Banner */}
              {comparison ? (
                <div
                  className={`rounded-2xl p-5 border shadow-xs ${
                    comparison.overall_match
                      ? 'bg-emerald-50/70 border-emerald-200'
                      : 'bg-rose-50/80 border-rose-200'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {comparison.overall_match ? (
                      <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-0.5" />
                    ) : (
                      <AlertTriangle className="w-6 h-6 text-rose-600 flex-shrink-0 mt-0.5" />
                    )}
                    <div>
                      <div className="flex items-center gap-2">
                        <h4
                          className={`text-sm font-bold ${
                            comparison.overall_match ? 'text-emerald-900' : 'text-rose-900'
                          }`}
                        >
                          {comparison.overall_match
                            ? 'All Specifications Match Purchase Order'
                            : 'PO Reconciliation Mismatches Detected'}
                        </h4>
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-white/70 border text-slate-800">
                          Target PO: {comparison.po_number || 'None'}
                        </span>
                      </div>
                      <p
                        className={`text-xs mt-1 ${
                          comparison.overall_match ? 'text-emerald-800' : 'text-rose-800'
                        }`}
                      >
                        {comparison.summary}
                      </p>
                    </div>
                  </div>
                </div>
              ) : null}

              {/* Field-Level Comparisons */}
              {comparison && comparison.field_comparisons.length > 0 && (
                <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs overflow-hidden">
                  <div className="p-4 bg-slate-50/75 border-b border-slate-200 text-xs font-bold uppercase tracking-wider text-slate-700">
                    Header Level Reconciliations
                  </div>
                  <div className="divide-y divide-slate-100">
                    {comparison.field_comparisons.map((fc, idx) => (
                      <div key={idx} className="p-4 flex items-center justify-between text-xs">
                        <div>
                          <p className="font-semibold text-slate-900 capitalize">
                            {fc.field_name.replace('_', ' ')}
                          </p>
                          <p className="text-slate-500 text-[11px] mt-0.5">{fc.details}</p>
                        </div>
                        <div className="flex items-center gap-4 text-right">
                          <div>
                            <span className="text-[10px] text-slate-400 block uppercase">Expected (PO)</span>
                            <span className="font-mono font-medium text-slate-800">{fc.po_value || '-'}</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-slate-400 block uppercase">Actual (Invoice)</span>
                            <span className="font-mono font-medium text-slate-800">{fc.invoice_value || '-'}</span>
                          </div>
                          <StatusBadge status={fc.severity} type="match" />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Line-Item Comparison Table */}
              {comparison && comparison.line_item_comparisons.length > 0 && (
                <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs overflow-hidden">
                  <div className="p-4 bg-slate-50/75 border-b border-slate-200 text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center justify-between">
                    <span>Line-Item 3-Way Reconciliation</span>
                    <span className="text-[11px] lowercase text-slate-400 font-normal">
                      tolerance: ±$0.05
                    </span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider text-[11px] font-semibold">
                          <th className="py-3 px-4">Item Description</th>
                          <th className="py-3 px-3 text-center">PO Qty vs Inv Qty</th>
                          <th className="py-3 px-3 text-right">PO Unit Price</th>
                          <th className="py-3 px-3 text-right">Inv Unit Price</th>
                          <th className="py-3 px-3 text-right">Line Total</th>
                          <th className="py-3 px-4 text-center">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {comparison.line_item_comparisons.map((item, idx) => (
                          <tr key={idx} className={item.status === 'mismatch' ? 'bg-rose-50/40' : ''}>
                            <td className="py-3.5 px-4">
                              <p className="font-semibold text-slate-900">
                                {item.po_item_desc || item.invoice_item_desc || 'Unidentified item'}
                              </p>
                              {item.details && (
                                <p
                                  className={`text-[11px] mt-0.5 ${
                                    item.status === 'mismatch' ? 'text-rose-700 font-medium' : 'text-slate-400'
                                  }`}
                                >
                                  {item.details}
                                </p>
                              )}
                            </td>

                            <td className="py-3.5 px-3 text-center">
                              <span
                                className={`font-mono px-2 py-0.5 rounded text-xs ${
                                  !item.quantity_match
                                    ? 'bg-rose-100 text-rose-800 font-bold border border-rose-300'
                                    : 'text-slate-800'
                                }`}
                              >
                                {item.po_quantity ?? '-'} / {item.invoice_quantity ?? '-'}
                              </span>
                            </td>

                            <td className="py-3.5 px-3 text-right font-mono text-slate-600">
                              {item.po_unit_price !== null ? `$${item.po_unit_price.toFixed(2)}` : '-'}
                            </td>

                            <td className="py-3.5 px-3 text-right">
                              <span
                                className={`font-mono text-xs ${
                                  !item.price_match
                                    ? 'text-rose-700 font-bold bg-rose-100 px-1.5 py-0.5 rounded'
                                    : 'text-slate-800'
                                }`}
                              >
                                {item.invoice_unit_price !== null
                                  ? `$${item.invoice_unit_price.toFixed(2)}`
                                  : '-'}
                              </span>
                            </td>

                            <td className="py-3.5 px-3 text-right font-mono font-semibold text-slate-900">
                              {item.invoice_line_total !== null
                                ? `$${item.invoice_line_total.toFixed(2)}`
                                : item.po_line_total !== null
                                ? `$${item.po_line_total.toFixed(2)}`
                                : '-'}
                            </td>

                            <td className="py-3.5 px-4 text-center">
                              <StatusBadge status={item.status} type="match" />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Disclaimer */}
              <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 flex items-start gap-2.5 text-xs text-slate-500">
                <Info className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Legal Notice:</strong> {comparison?.disclaimer || 'Automated matching checks are diagnostic tools and do not replace final fiscal authorization.'}
                </span>
              </div>
            </div>
          )}

          {/* TAB 3: REVIEWER COMMENTS & ACTIONS */}
          {activeTab === 'review' && (
            <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">Review Comments & Feedback</h3>
                <span className="text-xs text-slate-400">
                  {document.review_comments.length} comments logged
                </span>
              </div>

              {/* Comments Thread */}
              <div className="space-y-4">
                {document.review_comments.length === 0 ? (
                  <p className="text-xs text-slate-500 text-center py-6">
                    No comments recorded for this invoice yet.
                  </p>
                ) : (
                  document.review_comments.map((c) => (
                    <div
                      key={c.id}
                      className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900">{c.reviewer_name}</span>
                          {c.action && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-brand-100 text-brand-800">
                              {c.action}
                            </span>
                          )}
                        </div>
                        <span className="text-[11px] text-slate-400">
                          {new Date(c.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-xs text-slate-700 whitespace-pre-wrap">{c.comment}</p>
                    </div>
                  ))
                )}
              </div>

              {/* Add Comment Box for Reviewer */}
              {isReviewer && (
                <form onSubmit={handleAddComment} className="pt-4 border-t border-slate-100 space-y-3">
                  <label className="text-xs font-semibold text-slate-700 block">
                    Post Reviewer Comment
                  </label>
                  <textarea
                    rows={3}
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    placeholder="Enter notes or audit observations..."
                    className="w-full px-3 py-2.5 rounded-xl border border-slate-200 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 placeholder:text-slate-400"
                  />
                  <div className="text-right">
                    <button
                      type="submit"
                      disabled={!commentText.trim()}
                      className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs shadow-2xs transition-all disabled:opacity-50"
                    >
                      <Send className="w-3.5 h-3.5" />
                      Post Comment
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}

          {/* TAB 4: WORKFLOW AUDIT LOG */}
          {activeTab === 'history' && (
            <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs p-6 space-y-6">
              <div className="pb-4 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">Immutable Workflow Audit History</h3>
                <p className="text-xs text-slate-500">
                  Full chronological record of all state transitions and review decisions.
                </p>
              </div>

              <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200">
                {document.workflow_history.map((h) => (
                  <div key={h.id} className="relative">
                    <div className="absolute -left-6 top-1 w-3 h-3 rounded-full bg-brand-600 ring-4 ring-white"></div>
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2 text-xs">
                        <span className="font-bold text-slate-900">{h.actor_name}</span>
                        <span className="text-slate-400">•</span>
                        <span className="text-slate-600">
                          {h.previous_status ? (
                            <>
                              Changed from{' '}
                              <strong className="capitalize">{h.previous_status}</strong> to{' '}
                              <strong className="capitalize text-brand-700">{h.new_status}</strong>
                            </>
                          ) : (
                            <>
                              Created document in{' '}
                              <strong className="capitalize text-brand-700">{h.new_status}</strong>
                            </>
                          )}
                        </span>
                      </div>
                      {h.reason && (
                        <p className="text-xs text-slate-500 italic bg-slate-50 p-2.5 rounded-xl border border-slate-200/70">
                          "{h.reason}"
                        </p>
                      )}
                      <p className="text-[11px] text-slate-400">
                        {new Date(h.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Reviewer Action Modal (Approve, Reject, Request Corrections) */}
      {actionModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-slate-900">
              {actionModal === 'approve' && 'Confirm Invoice Approval'}
              {actionModal === 'reject' && 'Confirm Invoice Rejection'}
              {actionModal === 'correct' && 'Request Corrections from Submitter'}
            </h3>

            <p className="text-xs text-slate-600">
              {actionModal === 'approve' &&
                'This will approve the invoice for procurement disbursement and transition it to Approved state.'}
              {actionModal === 'reject' &&
                'This will reject the invoice and permanently mark it as Rejected.'}
              {actionModal === 'correct' &&
                'This will return the document to Draft state so the submitter can revise fields or re-upload.'}
            </p>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                {actionModal === 'correct' ? 'Reason for Corrections (Required)' : 'Audit Note / Reason (Optional)'}
              </label>
              <textarea
                rows={3}
                required={actionModal === 'correct'}
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                placeholder="Explain the decision for the audit log..."
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setActionModal(null)}
                className="px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleExecuteReviewAction}
                disabled={actionLoading}
                className={`px-4 py-2 rounded-xl text-xs font-semibold text-white shadow-xs ${
                  actionModal === 'approve'
                    ? 'bg-emerald-600 hover:bg-emerald-700'
                    : actionModal === 'reject'
                    ? 'bg-rose-600 hover:bg-rose-700'
                    : 'bg-amber-600 hover:bg-amber-700'
                }`}
              >
                {actionLoading ? 'Processing...' : 'Confirm Action'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Attach / Edit Purchase Order Modal */}
      {showPoModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-2xl w-full p-6 sm:p-8 space-y-6 shadow-2xl my-8">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900">
                Attach / Edit Purchase Order Reference
              </h3>
              <button
                onClick={() => setShowPoModal(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSavePurchaseOrder} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    PO Number
                  </label>
                  <input
                    type="text"
                    required
                    value={poNumber}
                    onChange={(e) => setPoNumber(e.target.value)}
                    placeholder="PO-2026-889"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Vendor Name
                  </label>
                  <input
                    type="text"
                    required
                    value={poVendor}
                    onChange={(e) => setPoVendor(e.target.value)}
                    placeholder="TechCorp Solutions Inc"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    PO Date
                  </label>
                  <input
                    type="text"
                    value={poDate}
                    onChange={(e) => setPoDate(e.target.value)}
                    placeholder="2026-10-10"
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>

              {/* PO Line Items */}
              <div className="space-y-2 pt-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-600">
                    Authorized Line Items
                  </label>
                  <button
                    type="button"
                    onClick={handleAddPoItem}
                    className="text-xs font-semibold text-brand-600 hover:text-brand-800"
                  >
                    + Add Item
                  </button>
                </div>

                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {poItems.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <input
                        type="text"
                        required
                        placeholder="Item description"
                        value={item.description}
                        onChange={(e) => handlePoItemChange(idx, 'description', e.target.value)}
                        className="flex-3 px-3 py-1.5 rounded-lg border border-slate-200 text-xs"
                      />
                      <input
                        type="number"
                        step="any"
                        required
                        placeholder="Qty"
                        value={item.quantity}
                        onChange={(e) => handlePoItemChange(idx, 'quantity', e.target.value)}
                        className="w-20 px-2 py-1.5 rounded-lg border border-slate-200 text-xs text-center"
                      />
                      <input
                        type="number"
                        step="any"
                        required
                        placeholder="Unit Price"
                        value={item.unit_price}
                        onChange={(e) => handlePoItemChange(idx, 'unit_price', e.target.value)}
                        className="w-24 px-2 py-1.5 rounded-lg border border-slate-200 text-xs text-right"
                      />
                      <span className="w-24 text-right font-mono text-xs font-bold text-slate-800">
                        ${item.line_total.toFixed(2)}
                      </span>
                      {poItems.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemovePoItem(idx)}
                          className="text-slate-400 hover:text-rose-600 px-1"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                <div className="text-xs text-slate-600 font-semibold">
                  PO Total:{' '}
                  <span className="text-slate-900 font-bold">
                    ${poItems.reduce((acc, i) => acc + i.line_total, 0).toFixed(2)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setShowPoModal(false)}
                    className="px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 shadow-xs"
                  >
                    Save & Compare
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
