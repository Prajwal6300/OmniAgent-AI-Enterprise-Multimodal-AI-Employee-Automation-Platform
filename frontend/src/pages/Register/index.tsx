import React from 'react';
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/services/api/client';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { SearchInput } from '@/components/ui/SearchInput';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { login, isLoading } = useAuth();

  const [errors, setErrors] = useState<{ organization_name?: string; admin_email?: string; password?: string }>({});

  const handleRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setErrors({});

    const orgInput = e.currentTarget.elements.namedItem('organization_name') as HTMLInputElement;
    const emailInput = e.currentTarget.elements.namedItem('admin_email') as HTMLInputElement;
    const passwordInput = e.currentTarget.elements.namedItem('password') as HTMLInputElement;

    if (!orgInput?.value) setErrors({ organization_name: 'Enter organization name' });
    if (!emailInput?.value) setErrors({ admin_email: 'Enter admin email' });
    if (!passwordInput?.value) setErrors({ password: 'Enter password' });

    if (Object.keys(errors).length > 0) return;

    try {
      await apiClient.post('/auth/register', {
        organization_name: orgInput.value.trim(),
        admin_email: emailInput.value.trim(),
        password: passwordInput.value.trim(),
      });
      login(emailInput.value.trim(), passwordInput.value.trim());
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Registration failed';
      setErrors({ organization_name: message, admin_email: message, password: message });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-parchment p-4">
      <Card className="w-full max-w-md">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-ink">Register Enterprise</h2>
          <p className="text-sm text-slate-500 mt-1">Create organization tenant & administrator</p>
        </div>
        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Organization Name</label>
            <input
              type="text"
              defaultValue="Acme Global Inc"
              className="w-full px-3 py-2 bg-slate-100 border border-warm-mist rounded-lg text-sm text-ink focus:outline-none focus:border-brand-accent"
              required
            />
            {errors.organization_name && (
              <p className="text-xs text-brand-accent mt-1">{errors.organization_name}</p>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Admin Email</label>
            <input
              type="email"
              defaultValue="admin@acme.com"
              className="w-full px-3 py-2 bg-slate-100 border border-warm-mist rounded-lg text-sm text-ink focus:outline-none focus:border-brand-accent"
              required
            />
            {errors.admin_email && (
              <p className="text-xs text-brand-accent mt-1">{errors.admin_email}</p>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Password</label>
            <input
              type="password"
              className="w-full px-3 py-2 bg-slate-100 border border-warm-mist rounded-lg text-sm text-ink focus:outline-none focus:border-brand-accent"
              required
            />
            {errors.password && (
              <p className="text-xs text-brand-accent mt-1">{errors.password}</p>
            )}
          </div>
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Creating...' : 'Create Tenant'}
          </Button>
        </form>
        <div className="mt-4 text-center text-xs text-slate-500">
          Already registered? <Link to="/login" className="text-brand-accent hover:underline">Sign in</Link>
        </div>
      </Card>
    </div>
  );
}