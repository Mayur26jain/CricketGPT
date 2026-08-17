import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../App'
import { Trophy, AlertCircle, ArrowRight, CheckCircle2 } from 'lucide-react'

export default function Auth() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("demo@cricketgpt.com");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    
    const success = await login(email, password);
    setLoading(false);
    
    if (success) {
      navigate("/dashboard");
    } else {
      setError("Invalid login credentials. Please use the default demo credentials below.");
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-slate-100 flex items-center justify-center overflow-x-hidden dot-bg relative p-4">
      {/* Ambients */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[350px] h-[350px] bg-primary-600/10 rounded-full blur-[80px] pointer-events-none" />
      
      <div className="w-full max-w-md relative z-10 animate-slide-up">
        {/* Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="bg-gradient-to-tr from-primary-600 to-pink-500 p-3 rounded-2xl text-white shadow-xl glow-indigo mb-4">
            <Trophy className="h-6 w-6" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white font-sans">Welcome to CricketGPT</h2>
          <p className="text-sm text-zinc-400 mt-1.5">Sign in to your analytical dashboard</p>
        </div>

        {/* Card Form */}
        <div className="glass-panel p-8 rounded-2xl border border-zinc-800 shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="flex items-start space-x-2.5 p-3 rounded-lg border border-red-900/30 bg-red-950/15 text-xs text-red-400">
                <AlertCircle className="h-4.5 w-4.5 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 rounded-xl premium-input text-sm text-white"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 rounded-xl premium-input text-sm text-white"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 px-4 rounded-xl text-sm font-semibold bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-500 hover:to-indigo-500 text-white shadow-lg transition-all duration-200 flex items-center justify-center space-x-2 transform hover:-translate-y-0.5"
            >
              <span>{loading ? "Authenticating..." : "Sign In"}</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>
        </div>

        {/* Onboarding Tips Card */}
        <div className="mt-6 p-4 rounded-xl border border-zinc-800/60 bg-zinc-900/20 text-xs text-zinc-400 flex items-start space-x-3">
          <CheckCircle2 className="h-4.5 w-4.5 text-primary-400 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-zinc-300">Sandbox Trial Mode Active</p>
            <p className="mt-1 leading-relaxed">
              We have pre-configured a demo account for you. Simply leave the fields as they are and click **Sign In** to explore the entire interface.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
