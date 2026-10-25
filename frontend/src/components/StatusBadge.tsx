import React from 'react';

interface StatusBadgeProps {
  status: string;
  type?: 'workflow' | 'processing' | 'match';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, type = 'workflow' }) => {
  const norm = (status || '').toLowerCase();

  let styles = 'bg-slate-100 text-slate-700 border-slate-300';
  let label = status;

  if (type === 'workflow') {
    switch (norm) {
      case 'draft':
        styles = 'bg-amber-50 text-amber-800 border-amber-300';
        label = 'Draft (Editable)';
        break;
      case 'submitted':
        styles = 'bg-blue-50 text-blue-800 border-blue-300';
        label = 'Awaiting Review';
        break;
      case 'approved':
        styles = 'bg-emerald-50 text-emerald-800 border-emerald-300';
        label = 'Approved';
        break;
      case 'rejected':
        styles = 'bg-rose-50 text-rose-800 border-rose-300';
        label = 'Rejected';
        break;
    }
  } else if (type === 'processing') {
    switch (norm) {
      case 'completed':
        styles = 'bg-emerald-50 text-emerald-700 border-emerald-200';
        label = 'Extracted';
        break;
      case 'processing':
        styles = 'bg-indigo-50 text-indigo-700 border-indigo-200 animate-pulse';
        label = 'Processing OCR';
        break;
      case 'pending':
        styles = 'bg-slate-100 text-slate-600 border-slate-200';
        label = 'Queued';
        break;
      case 'failed':
        styles = 'bg-rose-50 text-rose-700 border-rose-200';
        label = 'Extraction Failed';
        break;
    }
  } else if (type === 'match') {
    switch (norm) {
      case 'matched':
      case 'match':
        styles = 'bg-emerald-50 text-emerald-700 border-emerald-300';
        label = 'Match';
        break;
      case 'mismatch':
        styles = 'bg-rose-50 text-rose-700 border-rose-300 font-semibold';
        label = 'Mismatch';
        break;
      case 'warning':
        styles = 'bg-amber-50 text-amber-700 border-amber-300';
        label = 'Warning';
        break;
      case 'unmatched_po':
        styles = 'bg-orange-50 text-orange-700 border-orange-300';
        label = 'Missing on Invoice';
        break;
      case 'unmatched_invoice':
        styles = 'bg-purple-50 text-purple-700 border-purple-300';
        label = 'Extra on Invoice';
        break;
    }
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles}`}>
      {label}
    </span>
  );
};
