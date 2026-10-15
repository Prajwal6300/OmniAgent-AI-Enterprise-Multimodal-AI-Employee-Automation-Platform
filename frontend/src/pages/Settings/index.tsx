import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Loader2, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function SettingsPage() {
  const [state, setState] = useState<'loading' | 'empty' | 'error' | 'success'>('loading');

  const loadingState = (
    <Card className="p-8 text-center text-slate-500">
      <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3 text-brand-accent" />
      <p className="text-sm">Loading settings...</p>
    </Card>
  );

  const emptyState = (
    <Card className="p-12 text-center text-slate-500">
      <CheckCircle2 className="w-10 h-10 text-brand-accent mx-auto mb-3" />
      <h3 className="text-base font-medium text-ink">No settings configured</h3>
      <p className="text-sm text-slate-500 mt-1">
        Organization profiles, model selection, and API preferences will appear here.
      </p>
    </Card>
  );

  const errorState = (
    <Card className="p-8 text-center border border-warm-mist">
      <AlertTriangle className="w-8 h-8 text-warm-mist mb-3" />
      <h3 className="text-base font-semibold text-graphite">Error loading settings</h3>
      <p className="text-sm text-slate-400 mt-1">Could not retrieve settings data.</p>
      <Button variant="outline" size="sm" onClick={() => setState('loading')}>
        Retry
      </Button>
    </Card>
  );

  const successState = (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-ink">Settings</h1>
        <p className="text-sm text-slate-500 mt-1">Organization profiles, model selection, and API preferences.</p>
      </div>

      <Card className="space-y-4">
        <div className="py-8 text-center text-slate-500">
          <p className="text-sm">Settings module active and ready.</p>
        </div>
      </Card>
    </div>
  );

  return (
    <div className="space-y-6">
      {state === 'loading' && <div>{loadingState}</div>}
      {state === 'empty' && <div>{emptyState}</div>}
      {state === 'error' && <div>{errorState}</div>}
      {state === 'success' && <div>{successState}</div>}
    </div>
  );
}
