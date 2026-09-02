import React from 'react';
import { Card } from '@/components/ui/Card';

export default function Voice&AudioPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">Voice & Audio</h1>
        <p className="text-sm text-slate-400 mt-1">Transcribe, diarize, and summarize voice notes and audio calls.</p>
      </div>
      <Card>
        <div className="py-8 text-center text-slate-400">
          <p className="text-sm">Voice & Audio module active and ready.</p>
        </div>
      </Card>
    </div>
  );
}
