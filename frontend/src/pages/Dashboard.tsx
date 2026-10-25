import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '../api/client';
import type { DashboardStats } from '../types';
import { useAuth } from '../auth/AuthContext';
import {
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Upload,
  ArrowRight,
  TrendingUp,
  Activity,
  FileSearch
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  Legend
} from 'recharts';

export const Dashboard: React.FC = () => {
  const { user, isReviewer } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await apiClient.get<DashboardStats>('/dashboard/stats');
        setStats(res.data);
      } catch (err) {
        console.error('Failed to load dashboard statistics', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-10 h-10 border-4 border-brand-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const workflowChartData = [
    { name: 'Draft', count: stats?.draft_count || 0, color: '#f59e0b' },
    { name: 'Awaiting Review', count: stats?.awaiting_review || 0, color: '#3b82f6' },
    { name: 'Approved', count: stats?.approved_count || 0, color: '#10b981' },
    { name: 'Rejected', count: stats?.rejected_count || 0, color: '#ef4444' },
  ];

  const processingChartData = [
    { name: 'Extracted', count: stats?.completed_processing || 0, color: '#10b981' },
    { name: 'Processing', count: stats?.processing_count || 0, color: '#6366f1' },
    { name: 'Pending', count: stats?.pending_processing || 0, color: '#94a3b8' },
    { name: 'Failed', count: stats?.failed_processing || 0, color: '#f43f5e' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-brand-900 to-slate-900 rounded-3xl p-6 sm:p-8 text-white shadow-xl flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-500/20 text-brand-300 border border-brand-400/30">
              {isReviewer ? 'Reviewer Workspace' : 'Submitter Workspace'}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Welcome back, {user?.name}
          </h1>
          <p className="mt-1 text-slate-300 text-sm max-w-2xl">
            {isReviewer
              ? 'Review pending vendor invoices, verify 3-way matching against purchase orders, and record compliance decisions.'
              : 'Upload vendor invoices for AI document extraction, resolve validation alerts, and submit for reviewer approval.'}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Link
            to="/documents/upload"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-semibold text-sm transition-all shadow-md shadow-brand-500/25"
          >
            <Upload className="w-4 h-4" />
            Upload New Invoice
          </Link>
          <Link
            to="/documents"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-sm transition-all border border-white/15"
          >
            <FileText className="w-4 h-4" />
            View Documents
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Documents */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Invoices</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{stats?.total_documents ?? 0}</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center text-slate-600">
            <FileText className="w-6 h-6" />
          </div>
        </div>

        {/* Awaiting Review */}
        <div className="bg-white p-5 rounded-2xl border border-blue-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-blue-600">Awaiting Review</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{stats?.awaiting_review ?? 0}</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
            <Clock className="w-6 h-6" />
          </div>
        </div>

        {/* In Draft */}
        <div className="bg-white p-5 rounded-2xl border border-amber-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-amber-600">Draft / Corrections</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{stats?.draft_count ?? 0}</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-50 flex items-center justify-center text-amber-600">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>

        {/* Approved */}
        <div className="bg-white p-5 rounded-2xl border border-emerald-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-emerald-600">Approved</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{stats?.approved_count ?? 0}</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>

        {/* Rejected */}
        <div className="bg-white p-5 rounded-2xl border border-rose-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-rose-600">Rejected</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{stats?.rejected_count ?? 0}</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-rose-50 flex items-center justify-center text-rose-600">
            <XCircle className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Visual Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Workflow State Distribution Bar Chart */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-brand-600" />
                Workflow Pipeline Distribution
              </h3>
              <p className="text-xs text-slate-500">Current state of documents in the audit pipeline</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={workflowChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#64748b' }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                <Tooltip
                  cursor={{ fill: '#f1f5f9' }}
                  contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0' }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {workflowChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* OCR / Document Processing Status Breakdown */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <FileSearch className="w-4 h-4 text-brand-600" />
                OCR & Processing Status
              </h3>
              <p className="text-xs text-slate-500">PyMuPDF digital extraction & OCR health</p>
            </div>
          </div>
          <div className="h-64 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={processingChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="count"
                >
                  {processingChartData.map((entry, index) => (
                    <Cell key={`cell-pie-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0' }} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Workflow Activity Log */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="p-6 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-brand-600" />
            <h3 className="text-base font-bold text-slate-900">Recent Audit Trail Activity</h3>
          </div>
          <Link
            to="/documents"
            className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1"
          >
            View all documents <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="divide-y divide-slate-100">
          {stats?.recent_activity && stats.recent_activity.length > 0 ? (
            stats.recent_activity.map((act) => (
              <div key={act.id} className="p-4 sm:px-6 flex items-start justify-between hover:bg-slate-50/70 transition-colors">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-600 mt-0.5 text-xs font-bold">
                    {act.actor_name?.charAt(0) || 'U'}
                  </div>
                  <div>
                    <p className="text-sm text-slate-900 font-medium">
                      <span className="font-semibold text-slate-950">{act.actor_name}</span>{' '}
                      transitioned Document #{act.document_id} from{' '}
                      <span className="capitalize font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded text-slate-700">
                        {act.previous_status || 'Initial'}
                      </span>{' '}
                      to{' '}
                      <span className="capitalize font-mono text-xs bg-brand-50 px-1.5 py-0.5 rounded text-brand-700 font-bold">
                        {act.new_status}
                      </span>
                    </p>
                    {act.reason && (
                      <p className="text-xs text-slate-500 mt-1 italic">
                        "{act.reason}"
                      </p>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <Link
                    to={`/documents/${act.document_id}`}
                    className="inline-flex items-center gap-1 text-xs font-medium text-brand-600 hover:text-brand-800"
                  >
                    Inspect <ArrowRight className="w-3 h-3" />
                  </Link>
                  <p className="text-[11px] text-slate-400 mt-1">
                    {new Date(act.created_at).toLocaleDateString()} {new Date(act.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-sm text-slate-500">
              No recent workflow actions logged.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
