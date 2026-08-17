import React from 'react'
import { Link } from 'react-router-dom'
import { Trophy, ArrowRight, Activity, Zap, BarChart2, ShieldCheck } from 'lucide-react'

export default function Landing() {
  return (
    <div className="min-h-screen bg-zinc-950 text-slate-100 flex flex-col justify-between overflow-x-hidden dot-bg relative">
      
      {/* Background ambient glows */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-primary-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-pink-500/10 rounded-full blur-[120px] pointer-events-none" />

      {/* Header */}
      <header className="max-w-7xl mx-auto w-full px-6 py-6 flex justify-between items-center border-b border-zinc-950 relative z-10">
        <div className="flex items-center space-x-2">
          <div className="bg-gradient-to-tr from-primary-600 to-pink-500 p-2 rounded-xl text-white shadow-lg glow-indigo">
            <Trophy className="h-5 w-5" />
          </div>
          <span className="text-xl font-bold font-sans tracking-tight bg-gradient-to-r from-white to-zinc-400 bg-clip-text text-transparent">
            CricketGPT
          </span>
        </div>
        <Link 
          to="/auth" 
          className="px-4 py-2 rounded-lg text-sm font-medium border border-zinc-800 bg-zinc-900/60 hover:bg-zinc-800 hover:border-zinc-700 transition-all duration-200"
        >
          Sign In
        </Link>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-6 py-20 flex-1 flex flex-col items-center justify-center text-center relative z-10">
        
        {/* Animated badge */}
        <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full border border-primary-500/30 bg-primary-500/5 text-xs text-primary-400 font-semibold mb-8 animate-pulse-slow">
          <Zap className="h-3.5 w-3.5" />
          <span>Next-Generation Cricket Analytics</span>
        </div>

        {/* Hero Title */}
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight font-sans mb-6 max-w-4xl leading-tight">
          The AI-Powered Intelligence Platform for{' '}
          <span className="bg-gradient-to-r from-primary-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
            Cricket Stats
          </span>
        </h1>

        {/* Hero Description */}
        <p className="text-lg md:text-xl text-zinc-400 max-w-2xl mb-10 font-light leading-relaxed">
          Ask questions, generate dynamic comparisons, forecast match probabilities, and run advanced SQL database search over legendary cricket history in seconds.
        </p>

        {/* Call to Action buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-4 mb-16">
          <Link
            to="/auth"
            className="flex items-center space-x-2 px-8 py-4 rounded-xl text-base font-semibold bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-500 hover:to-indigo-500 text-white shadow-lg shadow-primary-500/20 transform hover:-translate-y-0.5 transition-all duration-200"
          >
            <span>Launch Platform</span>
            <ArrowRight className="h-4.5 w-4.5" />
          </Link>
          <a
            href="#features"
            className="px-8 py-4 rounded-xl text-base font-semibold border border-zinc-800 bg-zinc-900/30 hover:bg-zinc-900/60 hover:border-zinc-700 transition-all duration-200"
          >
            Explore Features
          </a>
        </div>

        {/* Product Preview Cards Grid */}
        <div id="features" className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mt-10 max-w-6xl">
          <div className="glass-card p-8 rounded-2xl text-left">
            <div className="h-12 w-12 rounded-xl bg-primary-500/10 border border-primary-500/20 flex items-center justify-center text-primary-400 mb-6">
              <Activity className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold mb-3 text-white">Live Real-time Agent</h3>
            <p className="text-zinc-400 text-sm leading-relaxed">
              Streams active scores, forecasts ball-by-ball commentary, and maps live updates instantly.
            </p>
          </div>

          <div className="glass-card p-8 rounded-2xl text-left">
            <div className="h-12 w-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-6">
              <BarChart2 className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold mb-3 text-white">Advanced SQL Databases</h3>
            <p className="text-zinc-400 text-sm leading-relaxed">
              Generates clean schema queries, compiles player metrics, and builds interactive radar comparison charts.
            </p>
          </div>

          <div className="glass-card p-8 rounded-2xl text-left">
            <div className="h-12 w-12 rounded-xl bg-pink-500/10 border border-pink-500/20 flex items-center justify-center text-pink-400 mb-6">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold mb-3 text-white">Semantic RAG Engine</h3>
            <p className="text-zinc-400 text-sm leading-relaxed">
              Explains complex cricket rules, reviews historical context, and summaries matches.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full py-8 border-t border-zinc-900/60 bg-zinc-950 text-center text-xs text-zinc-500 relative z-10">
        <p>© 2026 CricketGPT. Built for professional analysts and cricket fans worldwide.</p>
      </footer>
    </div>
  )
}
