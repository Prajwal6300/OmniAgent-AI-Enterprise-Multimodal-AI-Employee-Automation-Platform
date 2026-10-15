import React, { useState, useEffect, useRef } from 'react';
import { cn } from '@/utils/cn';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { 
  Bot, LayoutDashboard, MessageSquare, FileText, CheckCircle2, 
  Workflow, Network, Sliders, Shield, Bell, BarChart3, Radio, Menu
} from 'lucide-react';
import { ToastProvider, Toaster } from '@/hooks/useToast';
import { BrandMark } from '@/components/ui/BrandMark';
import { SidebarNavItem } from '@/components/ui/SidebarNavItem';
import { TopNavLink } from '@/components/ui/TopNavLink';
import { GhostButton } from '@/components/ui/GhostButton';
import { FilledActionButton } from '@/components/ui/FilledActionButton';
import { BadgeTag } from '@/components/ui/BadgeTag';

export default function AppLayout() {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const drawerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleKeydown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && sidebarOpen) {
        setSidebarOpen(false);
        if (drawerRef.current) {
          drawerRef.current.focus();
        }
      }
    };
    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  }, [sidebarOpen]);

  const handleOutsideClick = (e: MouseEvent) => {
    const target = e.target as Node | null;
    if (drawerRef.current && drawerRef.current !== target && !drawerRef.current.contains(target)) {
      setSidebarOpen(false);
    }
  };

  useEffect(() => {
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, [sidebarOpen]);

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
      <aside
        className={cn("w-64 border-r border-warm-mist flex flex-col justify-between p-6 bg-softPaper max-w-full", {
          'md': sidebarOpen,
          '': !sidebarOpen,
        })}
        aria-label="Main navigation"
      >
        <div className="flex items-center gap-3 px-3 py-4 mb-4 border-b border-warm-mist">
          <BrandMark to="/" />
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
        'md': sidebarOpen,
        '': !sidebarOpen,
      })}>
        {/* Mobile Hamburger Button - only shows below md */}
        <button
          onClick={() => setSidebarOpen(true)}
          aria-label="Open navigation menu"
          aria-expanded={!sidebarOpen}
          className="md:hidden p-2 rounded-lg hover:bg-warm-mist/20 transition-colors absolute left-4 top-1/2 -translate-y-1/2 z-20"
        >
          <Menu className="w-5 h-5 text-slate-600" />
        </button>

        {/* Mobile Slide-in Drawer */}
        {sidebarOpen && (
          <div
            ref={drawerRef}
            className="fixed inset-0 z-40 bg-parchment/80"
            onClick={e => e.stopPropagation()}
          >
            <aside
              className="fixed inset-0 right-0 top-0 w-64 h-screen bg-softPaper border-l border-warm-mist transform translate-x-full md:translate-x0 transition-transform duration-300 ease-out"
              aria-label="Main navigation"
              aria-expanded="true"
              onClick={e => e.stopPropagation()}
            >
              <div className="h-full flex flex-col">
                <nav className="flex-1 px-6 py-4 space-y-2">
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
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                aria-label="Close navigation menu"
                className="absolute top-4 right-4 p-2 rounded-lg hover:bg-warm-mist/20 transition-colors z-30"
              >
                <Menu className="w-5 h-5 text-slate-600" />
              </button>
            </aside>
          </div>
        )}

        {/* Header */}
        <header className="h-16 border-b border-warm-mist px-6 flex items-center justify-between bg-softPaper/50">
          <h1 className="text-sm font-medium text-slate-500">Enterprise AI Employee Portal</h1>
          <div className="flex items-center gap-4">
            <TopNavLink name="Notifications" path="/notifications" isActive={location.pathname.startsWith('/notifications')} />
            <BrandMark to="/" aria-label="OmniAgent AI home page" />
            <div className="w-8 h-8 rounded-full bg-brand-accent/20 border border-brand-accent text-brand-accent/30 flex items-center justify-center font-medium text-xs">
              AD
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
        <footer className="mt-6 border-t border-warm-mist p-4 text-center text-sm text-slate-400">
          © {new Date().getFullYear()} OmniAgent AI. All rights reserved.{import.meta.env.VITE_CONTACT_PHONE && (
            <span className="mx-2">
              <a href={`tel:${import.meta.env.VITE_CONTACT_PHONE.replace(/[- space]/g, '')}`} className="text-slate-300 hover:text-slate-100">
                {import.meta.env.VITE_CONTACT_PHONE}
              </a>
            </span>
          )}
          {import.meta.env.VITE_CONTACT_EMAIL && (
            <span className="mx-2">
              <a href={`mailto:${import.meta.env.VITE_CONTACT_EMAIL}`} className="text-slate-300 hover:text-slate-100">
                {import.meta.env.VITE_CONTACT_EMAIL}
              </a>
            </span>
          )}
        </footer>
        <Toaster />
      </div>
    </div>
  );
}