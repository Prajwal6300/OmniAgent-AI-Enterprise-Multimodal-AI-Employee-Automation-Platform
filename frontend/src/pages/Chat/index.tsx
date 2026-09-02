import React from 'react';
import { Card } from '@/components/ui/Card';

export default function MultimodalChatPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">Multimodal Chat</h1>
        <p className="text-sm text-slate-400 mt-1">Converse with Supervisor and specialized agents across text, documents, and media.</p>
      </div>
      <Card>
        <div className="py-8 text-center text-slate-400">
          <p className="text-sm">Multimodal Chat module active and ready.</p>
        </div>
      </Card>
    </div>
  );
}
