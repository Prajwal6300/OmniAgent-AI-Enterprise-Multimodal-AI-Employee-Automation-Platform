import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

export default function RegisterPage() {
  const navigate = useNavigate();

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
      <Card className="w-full max-w-md">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-slate-100">Register Enterprise</h2>
          <p className="text-sm text-slate-400 mt-1">Create organization tenant & administrator</p>
        </div>
        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Organization Name</label>
            <input 
              type="text" 
              defaultValue="Acme Global Inc"
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
              required 
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Admin Email</label>
            <input 
              type="email" 
              defaultValue="admin@acme.com"
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
              required 
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
            <input 
              type="password" 
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
              required 
            />
          </div>
          <Button type="submit" className="w-full">Create Tenant</Button>
        </form>
        <div className="mt-4 text-center text-xs text-slate-400">
          Already registered? <Link to="/login" className="text-indigo-400 hover:underline">Sign in</Link>
        </div>
      </Card>
    </div>
  );
}
