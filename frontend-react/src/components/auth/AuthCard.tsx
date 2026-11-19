import React, { useState } from 'react';
import { Sparkles, User, Lock, KeyRound } from 'lucide-react';
import { AuthUser, login } from '../../services/authService';

interface AuthCardProps {
  onLoginSuccess: (user: AuthUser, token: string) => void;
}

export const AuthCard: React.FC<AuthCardProps> = ({ onLoginSuccess }) => {
  const [authTab, setAuthTab] = useState<'signin' | 'register'>('signin');
  const [username, setUsername] = useState('drbhatia');
  const [password, setPassword] = useState('Pass@123');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setAuthError(null);

    try {
      const res = await login(username.trim(), password);
      onLoginSuccess(res.user, res.token);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setAuthError(err.message);
      } else {
        setAuthError('Authentication failed. Please verify credentials.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickFill = (user: string, pass: string) => {
    setUsername(user);
    setPassword(pass);
    setAuthError(null);
  };

  return (
    <div className="w-full max-w-[390px] bg-[#0d1527] border border-cyan-500/25 rounded-2xl p-6 shadow-2xl shadow-cyan-950/40 relative z-10 backdrop-blur-xl">
      {/* Brand Badge */}
      <div className="flex justify-center mb-2">
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-[10px] font-bold tracking-wider uppercase">
          <Sparkles className="w-3 h-3" />
          LeverageDebtAI · Powered by EOLABS.IN
        </span>
      </div>

      <div className="text-center mb-4">
        <h1 className="text-xl font-extrabold text-white tracking-tight">Welcome Back</h1>
        <p className="text-slate-400 text-xs mt-0.5">Evidence-led debt &amp; capital structure intelligence</p>
      </div>

      {/* Segmented Radio Pill */}
      <div className="flex p-1 bg-slate-950/80 border border-slate-800 rounded-lg mb-4">
        <button
          type="button"
          onClick={() => { setAuthTab('signin'); setAuthError(null); }}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all ${
            authTab === 'signin'
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Sign In
        </button>
        <button
          type="button"
          onClick={() => { setAuthTab('register'); setAuthError(null); }}
          className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all ${
            authTab === 'register'
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Create Account
        </button>
      </div>

      {authError && (
        <div className="mb-3 p-2.5 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300 text-xs leading-snug">
          {authError}
        </div>
      )}

      {authTab === 'signin' ? (
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-slate-300 text-xs font-semibold mb-1">Username or Email</label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                placeholder="e.g. drbhatia, skumar"
                className="w-full bg-slate-950/90 border border-slate-700/60 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 font-sans"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-300 text-xs font-semibold mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
                className="w-full bg-slate-950/90 border border-slate-700/60 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 font-sans"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full mt-2 py-2.5 px-4 bg-gradient-to-r from-sky-600 to-cyan-600 hover:from-sky-500 hover:to-cyan-500 text-white text-sm font-bold rounded-lg border border-cyan-400/30 shadow-lg shadow-cyan-900/30 transition-all active:scale-[0.99] flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
          >
            {isSubmitting ? 'Authenticating with Bcrypt...' : 'Sign In to Platform →'}
          </button>
        </form>
      ) : (
        <div className="space-y-3">
          <div>
            <label className="block text-slate-300 text-xs font-semibold mb-1">Full Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Prof. Dawar"
              className="w-full bg-slate-950/90 border border-slate-700/60 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-400"
            />
          </div>
          <div>
            <label className="block text-slate-300 text-xs font-semibold mb-1">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@university.edu"
              className="w-full bg-slate-950/90 border border-slate-700/60 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-400"
            />
          </div>
          <button
            type="button"
            onClick={() => setAuthError('Account registration requests require administrator approval. Contact drbhatiasanjay@gmail.com')}
            className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold rounded-lg border border-slate-600 transition-all cursor-pointer"
          >
            Request Access Verification
          </button>
        </div>
      )}

      {/* Preset Quick-Fill Chips */}
      <div className="mt-4 pt-3 border-t border-slate-800/80">
        <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1">
          <KeyRound className="w-3 h-3 text-cyan-400" />
          Verified Accounts:
        </div>
        <div className="flex flex-wrap gap-1.5">
          <button
            type="button"
            onClick={() => handleQuickFill('drbhatia', 'Pass@123')}
            className="px-2 py-0.5 rounded bg-slate-800/70 hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 text-[11px] font-mono border border-slate-700/50 transition-all cursor-pointer"
          >
            drbhatia (Admin)
          </button>
          <button
            type="button"
            onClick={() => handleQuickFill('skumar', 'Pass@123')}
            className="px-2 py-0.5 rounded bg-slate-800/70 hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 text-[11px] font-mono border border-slate-700/50 transition-all cursor-pointer"
          >
            skumar (Researcher)
          </button>
          <button
            type="button"
            onClick={() => handleQuickFill('profsurkumar', 'Pass@123')}
            className="px-2 py-0.5 rounded bg-slate-800/70 hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 text-[11px] font-mono border border-slate-700/50 transition-all cursor-pointer"
          >
            profsurkumar (Admin)
          </button>
        </div>
      </div>
    </div>
  );
};
