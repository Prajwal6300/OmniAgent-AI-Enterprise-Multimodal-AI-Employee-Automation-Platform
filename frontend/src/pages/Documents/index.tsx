import React from 'react';
import { Card } from '@/components/ui/Card';

export default function DocumentHubPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">Document Hub</h1>
        <p className="text-sm text-slate-400 mt-1">Upload, inspect, and manage enterprise PDFs, DOCX, and scanned artifacts.</p>
      </div>
      <Card>
        <div className="py-8 text-center text-slate-400">
          <p className="text-sm">Document Hub module active and ready.</p>
        </div>
      </Card>
    </div>
  );
}
