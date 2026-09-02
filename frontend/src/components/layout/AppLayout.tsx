import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { 
  Bot, LayoutDashboard, MessageSquare, FileText, CheckCircle2, 
  Workflow, Network, Sliders, Shield, Bell, BarChart3, Radio
} from 'lucide-react';

export default function AppLayout() {
  const location = useLocation();
  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Multimodal Chat', path: '/chat', icon: MessageSquare },
    { name: 'Documents', path: '/documents', icon: FileText },
    { name: 'Image Analysis', path: '/image-analysis', icon: Radio },
    { name: 'Agents', path: '/agents', icon: Bot },
    { name: 'Workflows', path: '/workflows', icon: Workflow },
    { name: 'Approvals', path: '/approvals', icon: CheckCircle2 },
    { name: 'Agent Runs', path: '/agent-runs', icon: Network },
    { name: 'Analytics', path: '/analytics', icon: BarChart3 },
    { name: 'Settings', path: '/settings', icon: Sliders },
    { name: 'Admin', path: '/admin', icon: Shield },
  ];

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800 flex flex-col justify-between p-4 bg-slate-900/50">
        <div>
          <div className="flex items-center gap-3 px-3 py-4 mb-4 border-b border-slate-800">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white">Ω</div>
            <span className="font-semibold text-lg tracking-tight">OmniAgent AI</span>
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                    isActive 
                      ? 'bg-indigo-600/20 text-indigo-400 font-medium border border-indigo-500/30' 
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-xs text-slate-400">
          <div className="font-medium text-slate-300">OmniCorp Enterprise</div>
          <div>Tenant ID: 00000001</div>
        </div>
      </aside>

      {/* Main View Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <header className="h-16 border-b border-slate-800 px-6 flex items-center justify-between bg-slate-900/30">
          <h1 className="text-sm font-medium text-slate-400">Enterprise AI Employee Portal</h1>
          <div className="flex items-center gap-4">
            <Link to="/notifications" className="text-slate-400 hover:text-slate-200">
              <Bell className="w-5 h-5" />
            </Link>
            <div className="w-8 h-8 rounded-full bg-indigo-600/30 border border-indigo-500 text-indigo-300 flex items-center justify-center font-medium text-xs">
              AD
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
