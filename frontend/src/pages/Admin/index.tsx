import React from 'react';
import { Card } from '@/components/ui/Card';

export default function AdminConsolePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">Admin Console</h1>
        <p className="text-sm text-slate-400 mt-1">Enterprise user management, RBAC roles, and tenant configuration.</p>
      </div>
      <Card>
        <div className="py-8 text-center text-slate-400">
          <p className="text-sm">Admin Console module active and ready.</p>
        </div>
      </Card>
    </div>
  );
}
