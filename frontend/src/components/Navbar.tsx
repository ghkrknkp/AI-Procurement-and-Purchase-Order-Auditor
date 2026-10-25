import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import {
  FileText,
  LayoutDashboard,
  Upload,
  LogOut,
  UserCheck,
  ShieldCheck,
  RefreshCw
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleQuickSwitch = async () => {
    if (user?.role === 'submitter') {
      await login('reviewer@edvexa.com', 'Reviewer123!');
    } else {
      await login('submitter@edvexa.com', 'Submitter123!');
    }
    navigate('/dashboard');
  };

  const navItemClass = (path: string) => {
    const isActive = location.pathname === path;
    return `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-brand-50 text-brand-700 font-semibold'
        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
    }`;
  };

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center gap-8">
            <Link to="/dashboard" className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-700 to-blue-500 flex items-center justify-center text-white shadow-sm shadow-brand-500/30">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div className="flex flex-col">
                <span className="text-base font-bold text-slate-900 tracking-tight leading-none">
                  ProcureAudit
                </span>
                <span className="text-[10px] text-brand-600 font-semibold uppercase tracking-wider mt-0.5">
                  AI Invoice & PO Verifier
                </span>
              </div>
            </Link>

            {/* Main Navigation Links */}
            <nav className="hidden md:flex items-center gap-1.5">
              <Link to="/dashboard" className={navItemClass('/dashboard')}>
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </Link>
              <Link to="/documents" className={navItemClass('/documents')}>
                <FileText className="w-4 h-4" />
                Invoices & Queue
              </Link>
              <Link to="/documents/upload" className={navItemClass('/documents/upload')}>
                <Upload className="w-4 h-4" />
                Upload Invoice
              </Link>
            </nav>
          </div>

          {/* User Profile, Demo Switcher & Logout */}
          <div className="flex items-center gap-3">
            {/* Quick Demo Switcher button */}
            <button
              onClick={handleQuickSwitch}
              title="Toggle between Submitter and Reviewer demo accounts"
              className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 text-xs font-medium transition-all shadow-2xs"
            >
              <RefreshCw className="w-3.5 h-3.5 text-brand-600" />
              <span>Switch to {user?.role === 'submitter' ? 'Reviewer' : 'Submitter'}</span>
            </button>

            {/* Current Role Pill */}
            <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
              <div className="flex flex-col text-right">
                <span className="text-xs font-semibold text-slate-800">{user?.name}</span>
                <span className="text-[11px] text-slate-500">{user?.email}</span>
              </div>
              <span
                className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wide border ${
                  user?.role === 'reviewer'
                    ? 'bg-purple-50 text-purple-700 border-purple-200'
                    : 'bg-blue-50 text-brand-700 border-blue-200'
                }`}
              >
                {user?.role === 'reviewer' ? (
                  <ShieldCheck className="w-3 h-3 text-purple-600" />
                ) : (
                  <UserCheck className="w-3 h-3 text-brand-600" />
                )}
                {user?.role}
              </span>
            </div>

            {/* Logout button */}
            <button
              onClick={handleLogout}
              className="p-2 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors ml-1"
              title="Log out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
