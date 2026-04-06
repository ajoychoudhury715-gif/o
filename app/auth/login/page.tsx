'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

import { storeSession } from '../../../lib/auth';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const checkExistingSession = async () => {
      try {
        const response = await fetch('/api/auth/check', { cache: 'no-store' });
        if (response.ok) {
          router.replace('/dashboard');
        }
      } catch {
        // Ignore session check failures and keep the user on the login page.
      }
    };

    checkExistingSession();
  }, [router]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          password,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        setError(data.error || 'Unable to sign in.');
        return;
      }

      storeSession({
        authenticatedAt: data.authenticatedAt,
        token: data.token,
        user: data.user,
      });

      router.replace('/dashboard');
      router.refresh();
    } catch (requestError) {
      console.error('Login request failed:', requestError);
      setError('Unable to sign in right now. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4 py-10">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <div className="text-5xl mb-4">🦷</div>
          <h1 className="text-4xl font-bold text-slate-900">THE DENTAL BOND</h1>
          <p className="mt-2 text-slate-600">Implant & Micro-dentistry Scheduling</p>
        </div>

        <form
          className="mt-8 space-y-6 rounded-2xl bg-white p-8 shadow-lg"
          onSubmit={handleSubmit}
        >
          {error ? (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          ) : null}

          <div>
            <label htmlFor="username" className="block text-sm font-medium text-slate-700">
              Username
            </label>
            <input
              id="username"
              type="text"
              required
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2.5 shadow-sm outline-none transition focus:border-slate-900"
              placeholder="Enter your username"
              autoComplete="username"
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-slate-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2.5 shadow-sm outline-none transition focus:border-slate-900"
              placeholder="Enter your password"
              autoComplete="current-password"
              disabled={isSubmitting}
            />
          </div>

          <button
            type="submit"
            className="flex w-full justify-center rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-400"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        <div className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 text-sm text-slate-600 shadow-sm">
          <p className="font-medium text-slate-800">Default local admin</p>
          <p>Username: <code>SPOIDERMON</code></p>
          <p>Password: <code>SPOIDERMON123</code></p>
        </div>
      </div>
    </div>
  );
}
