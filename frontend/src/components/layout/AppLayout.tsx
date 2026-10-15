import React, { useState } from 'react';
import { cn } from '@/utils/cn';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { 
  Bot, LayoutDashboard, MessageSquare, FileText, CheckCircle2, 
  Workflow, Network, Sliders, Shield, Bell, BarChart3, Radio
} from 'lucide-react';
import { BrandMark } from '@/components/ui/BrandMark';
import { SidebarNavItem } from '@/components/ui/SidebarNavItem';
import { TopNavLink } from '@/components/ui/TopNavLink';
import { GhostButton } from '@/components/ui/GhostButton';
import { FilledActionButton } from '@/components/ui/FilledActionButton';
import { BadgeTag } from '@/components/ui/BadgeTag';

export default function AppLayout() {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Multimodal Chat', path: '/chat', icon: MessageSquare },
    { name: 'Documents', path: '/documents', icon: FileText },
    { name: 'Image Analysis', path: '/image-analysis', icon: Radio },
    { name: 'Workflows', path: '/workflows', icon: Workflow },
    { name: 'Approvals', path: '/approvals', icon: CheckCircle2 },
    { name: 'Agent Runs', path: '/agent-runs', icon: Network },
    { name: 'Analytics', path: '/analytics', icon: BarChart3 },
    { name: 'Settings', path: '/settings', icon: Sliders },
    { name: 'Admin', path: '/admin', icon: Shield },
  ];

  return (
    <div className="flex min-h-screen bg-parchment overflow-hidden">
      {/* Sidebar */}
      <aside className={cn("w-64 border-r border-warm-mist flex flex-col justify-between p-6 bg-softPaper max-w-full", {
        'md:': sidebarOpen,
        '': !sidebarOpen,
      })}>
        <div className="flex items-center gap-3 px-3 py-4 mb-4 border-b border-warm-mist">
          <BrandMark />
          <span className="font-medium text-lg tracking-tight text-ink">OmniAgent AI</span>
        </div>
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <SidebarNavItem
                key={item.path}
                name={item.name}
                path={item.path}
                icon={Icon}
                isActive={isActive}
              />
            );
          })}
        </nav>
        <div className="p-3 bg-slate-200/30 rounded-lg border border-warm-mist text-xs text-slate-500">
          <div className="font-medium">OmniCorp Enterprise</div>
          <div>Tenant ID: 00000001</div>
        </div>
      </aside>

      {/* Main View Area */}
      <div className={cn("flex-1 flex flex-col min-w-0 overflow-hidden md:ml-64", {
        'md:': sidebarOpen,
        '': !sidebarOpen,
      })}>
        <header className="h-16 border-b border-warm-mist px-6 flex items-center justify-between bg-softPaper/50">
          <h1 className="text-sm font-medium text-slate-500">Enterprise AI Employee Portal</h1>
          <div className="flex items-center gap-4">
            <TopNavLink name="Notifications" path="/notifications" isActive={location.pathname.startsWith('/notifications')} />
            <div className="w-8 h-8 rounded-full bg-brand-accent/20 border border-brand-accent text-brand-accent/30 flex items-center justify-center font-medium text-xs">
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
