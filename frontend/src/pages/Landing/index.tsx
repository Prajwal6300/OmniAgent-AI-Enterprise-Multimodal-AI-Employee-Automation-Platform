import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/Button';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center px-4 text-center">
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold mb-6">
        Enterprise Multimodal AI Employee & Automation Platform
      </div>
      <h1 className="text-5xl font-extrabold tracking-tight max-w-3xl text-slate-100 mb-4">
        Autonomous Cross-Modal AI for the Modern Enterprise
      </h1>
      <p className="text-lg text-slate-400 max-w-xl mb-8">
        Ingest PDFs, images, spreadsheets, and audio. Reason with multi-agent LangGraph orchestration, and execute verified workflows with human-in-the-loop governance.
      </p>
      <div className="flex gap-4">
        <Link to="/login">
          <Button variant="primary" size="lg">Enterprise Sign In</Button>
        </Link>
        <Link to="/dashboard">
          <Button variant="secondary" size="lg">Live Dashboard</Button>
        </Link>
      </div>
    </div>
  );
}
