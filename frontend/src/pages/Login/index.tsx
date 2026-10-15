import React from 'react';
import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { SearchInput } from '@/components/ui/SearchInput';

export default function LoginPage() {
  const navigate = useNavigate();
  const { login, isLoading, isAuthenticated } = useAuth();

  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setErrors({});

    const emailInput = e.currentTarget.elements.namedItem('email') as HTMLInputElement;
    const passwordInput = e.currentTarget.elements.namedItem('password') as HTMLInputElement;

    if (!emailInput?.value.trim() || !passwordInput?.value.trim()) {
      if (!emailInput?.value.trim()) setErrors({ email: 'Enter corporate email' });
      if (!passwordInput?.value.trim()) setErrors({ password: 'Enter password' });
      return;
    }

    try {
      await login(emailInput.value.trim(), passwordInput.value.trim());
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Invalid email or password';
      setErrors({ email: message, password: message });
    }
  };

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-parchment p-4">
      <Card className="w-full max-w-md">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-ink">Sign In to OmniAgent</h2>
          <p className="text-sm text-slate-500 mt-1">Multi-Tenant Corporate Authentication</p>
        </div>
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Corporate Email</label>
            <input
              type="email"
              defaultValue="admin@omnicorp.com"
              className="w-full px-3 py-2 bg-slate-100 border border-warm-mist rounded-lg text-sm text-ink focus:outline-none focus:border-brand-accent"
              required
            />
            {errors.email && (
              <p className="text-xs text-brand-accent mt-1">{errors.email}</p>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Password</label>
            <input
              type="password"
              defaultValue="password"
              className="w-full px-3 py-2 bg-slate-100 border border-warm-mist rounded-lg text-sm text-ink focus:outline-none focus:border-brand-accent"
              required
            />
            {errors.password && (
              <p className="text-xs text-brand-accent mt-1">{errors.password}</p>
            )}
          </div>
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>
        <div className="mt-4 text-center text-xs text-slate-500">
          Need an account? <Link to="/register" className="text-brand-accent hover:underline">Register organization</Link>
        </div>
      </Card>
    </div>
  );
}