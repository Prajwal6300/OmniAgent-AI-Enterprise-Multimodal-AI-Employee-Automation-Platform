import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Home, Grid, AlertTriangle } from 'lucide-react';

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-parchment flex items-center justify-center p-4">
      <Card className="w-full max-w-md p-8 bg-slate-100 border-warm-mist border">
        <AlertTriangle className="w-12 h-12 text-warm-mist mb-6 mx-auto" />
        <h1 className="text-2xl font-bold tracking-tight text-warm-mist mb-4">Page Not Found</h1>
        <p className="text-slate-600 mb-8">
          The page you&apos;re looking for does not exist or has been removed.
        </p>
        <div className="flex gap-4">
          <Link to="/" className="flex-1">
            <Button variant="outline" size="lg">
              <Home className="mr-2" /> Home
            </Button>
          </Link>
          <Link to="/dashboard" className="flex-1">
            <Button variant="outline" size="lg" disabled>
              <Grid className="mr-2" /> Dashboard
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}