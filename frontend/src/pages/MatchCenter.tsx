import React, { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend } from 'recharts'
import { ArrowLeft, Activity, CloudSun, Calendar, MessageSquare, ShieldAlert, Award, Sparkles } from 'lucide-react'

export default function MatchCenter() {
  const [searchParams] = useSearchParams()
  const [matchesList, setMatchesList] = useState<any[]>([])
  const [selectedMatchId, setSelectedMatchId] = useState<number>(1)
  const [match, setMatch] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [detailsLoading, setDetailsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'scorecard' | 'commentary' | 'predictor'>('scorecard')

  // Fetch list of matches on mount
  useEffect(() => {
    const fetchMatchesList = async () => {
      try {
        const res = await fetch("/api/v1/matches/live")
        if (res.ok) {
          setMatchesList(await res.json())
        }
      } catch (e) {
        console.error("Failed to fetch matches list", e)
      }
    }
    fetchMatchesList()

    const mId = searchParams.get("match_id")
    if (mId) {
      setSelectedMatchId(parseInt(mId, 10))
    }
  }, [searchParams])

  // Fetch details when selected match changes
  useEffect(() => {
    const fetchMatchDetails = async () => {
      setDetailsLoading(true)
      try {
        const res = await fetch(`/api/v1/matches/live/details?match_id=${selectedMatchId}`)
        if (res.ok) {
          setMatch(await res.json())
        }
      } catch (e) {
        console.error("Failed to fetch match details", e)
      } finally {
        setLoading(false)
        setDetailsLoading(false)
      }
    }
    fetchMatchDetails()
  }, [selectedMatchId])

  if (loading) {
    return <div className="text-center py-20 text-zinc-400">Loading Match Center...</div>
  }

  const activeMatchSummary = matchesList.find(m => m.id === selectedMatchId) || matchesList[0]

  const pColors = {
    HOME: "#4f73ff",
    AWAY: "#db2777"
  }

  const winProbHome = match?.win_probability ? Object.values(match.win_probability)[0] as number : 50.0
  const winProbAway = match?.win_probability ? Object.values(match.win_probability)[1] as number : 50.0

  const pieData = [
    { name: match?.team_home?.name || 'Home Team', value: winProbHome, color: pColors.HOME },
    { name: match?.team_away?.name || 'Away Team', value: winProbAway, color: pColors.AWAY }
  ]

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      
      {/* Back Button Header */}
      <div className="flex items-center justify-between">
        <Link to="/dashboard" className="flex items-center space-x-2 text-sm text-zinc-400 hover:text-white transition-colors">
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Dashboard</span>
        </Link>
        <span className="text-[10px] uppercase font-mono tracking-widest bg-red-950/40 text-red-400 border border-red-900/30 px-3 py-1 rounded-full font-bold animate-pulse">
          Global Match Center
        </span>
      </div>

      {/* Horizontal Scroll Match Selector */}
      <div className="space-y-2">
        <h4 className="text-xs font-bold uppercase tracking-widest text-zinc-400">Matches Today</h4>
        <div className="flex gap-4 overflow-x-auto pb-3 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
          {matchesList.map(m => {
            const isActive = m.id === selectedMatchId
            const isLive = m.status === 'Live'
            const isUpcoming = m.status === 'Upcoming'
            
            return (
              <button
                key={m.id}
                onClick={() => setSelectedMatchId(m.id)}
                className={`flex-shrink-0 w-64 glass-panel p-4 rounded-xl text-left transition-all duration-200 cursor-pointer ${
                  isActive ? 'border-primary-500 bg-primary-950/10 shadow-lg' : 'hover:border-zinc-700 hover:bg-zinc-900/20'
                }`}
              >
                <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-wider mb-2">
                  <span className="text-zinc-500">{m.match_type}</span>
                  <span className={`px-2 py-0.5 rounded ${
                    isLive ? 'bg-red-950/60 text-red-400 border border-red-900/40 animate-pulse' :
                    isUpcoming ? 'bg-blue-950/60 text-blue-400 border border-blue-900/40' :
                    'bg-zinc-800 text-zinc-400'
                  }`}>
                    {m.status}
                  </span>
                </div>
                
                <div className="space-y-1.5">
                  <div className="flex justify-between text-sm font-semibold text-white">
                    <span className="truncate">{m.team_home}</span>
                    {m.scores && (
                      <span>{m.scores.team_home_runs}/{m.scores.team_home_wickets}</span>
                    )}
                  </div>
                  <div className="flex justify-between text-sm font-semibold text-zinc-300">
                    <span className="truncate">{m.team_away}</span>
                    {m.scores && m.scores.team_away_runs > 0 && (
                      <span>{m.scores.team_away_runs}/{m.scores.team_away_wickets}</span>
                    )}
                  </div>
                </div>

                <div className="text-[10px] text-zinc-500 truncate mt-3 border-t border-zinc-800/60 pt-2">
                  {m.result ? m.result : m.venue}
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Match Details HUD Card */}
      {detailsLoading ? (
        <div className="glass-panel p-20 text-center text-zinc-400 rounded-2xl">
          Loading match details...
        </div>
      ) : !match ? (
        <div className="glass-panel p-10 text-center space-y-4 rounded-2xl">
          <ShieldAlert className="h-12 w-12 text-red-500 mx-auto" />
          <h2 className="text-xl font-bold text-white">Match details unavailable</h2>
        </div>
      ) : (
        <>
          {/* Match Header Score HUD */}
          <div className="glass-panel p-6 rounded-2xl relative overflow-hidden bg-gradient-to-br from-zinc-900/60 to-zinc-950/20">
            
            {/* Ground & Format */}
            <div className="flex justify-between items-center text-xs text-zinc-400 mb-6 border-b border-zinc-800/60 pb-3">
              <div className="flex items-center space-x-2">
                <Calendar className="h-4 w-4 text-primary-400" />
                <span>{match.match_type} • Match Day</span>
              </div>
              <div className="flex items-center space-x-2">
                <CloudSun className="h-4 w-4 text-pink-400" />
                <span>{match.venue} ({match.weather.condition}, {match.weather.temp}°C)</span>
              </div>
            </div>

            {/* Live Score Display */}
            <div className="grid grid-cols-1 md:grid-cols-3 items-center gap-6">
              {/* Team Home */}
              <div className="text-left">
                <span className="text-[10px] text-zinc-500 font-bold tracking-widest uppercase">
                  {match.status === 'Completed' ? 'FINAL' : 'BATTING'}
                </span>
                <h2 className="text-3xl font-black text-white mt-1">{match.team_home.name}</h2>
                <div className="flex items-baseline space-x-3 mt-2">
                  <span className="text-4xl font-extrabold text-primary-400">
                    {match.team_home.score || '0/0'}
                  </span>
                  {match.team_home.overs && match.team_home.overs !== '0.0' && (
                    <span className="text-sm text-zinc-400">({match.team_home.overs} Ov)</span>
                  )}
                </div>
                {match.team_home.run_rate && match.team_home.run_rate !== '0.0' && (
                  <span className="text-xs text-zinc-500 block mt-1">Run Rate: {match.team_home.run_rate}</span>
                )}
              </div>

              {/* HUD Mid Status */}
              <div className="flex flex-col justify-center items-center text-center p-4 bg-zinc-900/30 rounded-xl border border-zinc-800/40">
                <span className="text-xs font-bold text-zinc-400">Match Outlook</span>
                <p className="text-sm font-semibold text-white mt-2">
                  {match.status === 'Completed' ? (
                    match.result || 'Match Completed'
                  ) : match.status === 'Upcoming' ? (
                    `Upcoming match at ${match.venue}`
                  ) : (
                    `${match.team_home.name} is playing live in Colombo. Win probability is live.`
                  )}
                </p>
              </div>

              {/* Team Away */}
              <div className="text-right md:border-l md:border-zinc-800/60 md:pl-6">
                <span className="text-[10px] text-zinc-500 font-bold tracking-widest uppercase">
                  {match.status === 'Completed' ? 'FINAL' : match.team_away.score === 'Yet to bat' ? 'YET TO BAT' : 'BATTING'}
                </span>
                <h2 className="text-3xl font-black text-zinc-300 mt-1">{match.team_away.name}</h2>
                <div className="flex items-baseline justify-end space-x-3 mt-2">
                  <span className="text-4xl font-extrabold text-zinc-600">
                    {match.team_away.score || 'Yet to bat'}
                  </span>
                  {match.team_away.overs && match.team_away.overs !== '0.0' && (
                    <span className="text-sm text-zinc-400">({match.team_away.overs} Ov)</span>
                  )}
                </div>
                {match.team_away.run_rate && match.team_away.run_rate !== '0.0' && (
                  <span className="text-xs text-zinc-500 block mt-1">Run Rate: {match.team_away.run_rate}</span>
                )}
              </div>
            </div>

            {/* Current Partnership details */}
            {match.team_home.innings && match.team_home.innings.length > 0 && (
              <div className="mt-6 border-t border-zinc-800/80 pt-4 flex flex-col sm:flex-row gap-6 justify-between text-xs text-zinc-300">
                <div className="flex items-center space-x-4">
                  <span className="text-zinc-500">Batsmen:</span>
                  {match.team_home.innings[0] && (
                    <span className="font-bold text-white">
                      {match.team_home.innings[0].batsman} ({match.team_home.innings[0].runs}*)
                    </span>
                  )}
                  {match.team_home.innings[1] && (
                    <>
                      <span className="text-zinc-600">•</span>
                      <span className="font-bold text-white">
                        {match.team_home.innings[1].batsman} ({match.team_home.innings[1].runs}*)
                      </span>
                    </>
                  )}
                </div>
                {match.team_home.bowlers && match.team_home.bowlers.length > 0 && (
                  <div className="flex items-center space-x-4">
                    <span className="text-zinc-500">Bowler:</span>
                    <span className="font-bold text-pink-400">
                      {match.team_home.bowlers[0].name} ({match.team_home.bowlers[0].wickets}/{match.team_home.bowlers[0].runs} off {match.team_home.bowlers[0].overs} ov)
                    </span>
                  </div>
                )}
              </div>
            )}

          </div>

          {/* Tabs Selector */}
          <div className="flex border-b border-zinc-800 gap-6 text-sm">
            <button
              onClick={() => setActiveTab('scorecard')}
              className={`pb-3 font-semibold uppercase tracking-wider transition-colors ${activeTab === 'scorecard' ? 'border-b-2 border-primary-500 text-white' : 'text-zinc-400 hover:text-white'}`}
            >
              Scorecard
            </button>
            <button
              onClick={() => setActiveTab('commentary')}
              className={`pb-3 font-semibold uppercase tracking-wider transition-colors ${activeTab === 'commentary' ? 'border-b-2 border-primary-500 text-white' : 'text-zinc-400 hover:text-white'}`}
            >
              Commentary
            </button>
            <button
              onClick={() => setActiveTab('predictor')}
              className={`pb-3 font-semibold uppercase tracking-wider transition-colors ${activeTab === 'predictor' ? 'border-b-2 border-primary-500 text-white' : 'text-zinc-400 hover:text-white'}`}
            >
              Win Predictor & Stats
            </button>
          </div>

          {/* Tabs Content */}
          {activeTab === 'scorecard' && (
            <div className="space-y-8 animate-fade-in">
              
              {/* Batting Innings Table */}
              <div className="glass-panel p-6 rounded-2xl">
                <h3 className="text-base font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                  <Activity className="h-4.5 w-4.5 text-primary-400" />
                  {match.team_home.name} Innings
                </h3>
                
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-zinc-800 text-zinc-500 uppercase tracking-wider">
                        <th className="py-3 px-2">Batsman</th>
                        <th className="py-3 px-2">Status</th>
                        <th className="py-3 px-2 text-right">Runs</th>
                        <th className="py-3 px-2 text-right">Balls</th>
                        <th className="py-3 px-2 text-right">4s</th>
                        <th className="py-3 px-2 text-right">6s</th>
                        <th className="py-3 px-2 text-right">SR</th>
                      </tr>
                    </thead>
                    <tbody>
                      {match.team_home.innings && match.team_home.innings.length > 0 ? (
                        match.team_home.innings.map((b: any, idx: number) => (
                          <tr key={idx} className="border-b border-zinc-800/40 hover:bg-zinc-900/30 transition-colors">
                            <td className="py-3.5 px-2 font-semibold text-white">{b.batsman}</td>
                            <td className={`py-3.5 px-2 font-mono ${b.status === 'batting' ? 'text-primary-400 font-bold' : 'text-zinc-500'}`}>
                              {b.status}
                            </td>
                            <td className="py-3.5 px-2 text-right font-bold text-slate-200">{b.runs}</td>
                            <td className="py-3.5 px-2 text-right text-zinc-400">{b.balls}</td>
                            <td className="py-3.5 px-2 text-right text-zinc-400">{b.fours}</td>
                            <td className="py-3.5 px-2 text-right text-zinc-400">{b.sixes}</td>
                            <td className="py-3.5 px-2 text-right text-zinc-400">{b.sr}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={7} className="py-8 text-center text-zinc-500">No innings data available yet.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Bowling Figures Table */}
              <div className="glass-panel p-6 rounded-2xl">
                <h3 className="text-base font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                  <CloudSun className="h-4.5 w-4.5 text-pink-400" />
                  {match.team_away.name} Bowling
                </h3>
                
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-zinc-800 text-zinc-500 uppercase tracking-wider">
                        <th className="py-3 px-2">Bowler</th>
                        <th className="py-3 px-2 text-right">Overs</th>
                        <th className="py-3 px-2 text-right">Maidens</th>
                        <th className="py-3 px-2 text-right">Runs</th>
                        <th className="py-3 px-2 text-right">Wickets</th>
                        <th className="py-3 px-2 text-right">Econ</th>
                      </tr>
                    </thead>
                    <tbody>
                      {match.team_home.bowlers && match.team_home.bowlers.length > 0 ? (
                        match.team_home.bowlers.map((b: any, idx: number) => (
                          <tr key={idx} className="border-b border-zinc-800/40 hover:bg-zinc-900/30 transition-colors">
                            <td className="py-3.5 px-2 font-semibold text-white">{b.name}</td>
                            <td className="py-3.5 px-2 text-right text-zinc-200">{b.overs}</td>
                            <td className="py-3.5 px-2 text-right text-zinc-400">{b.maidens}</td>
                            <td className="py-3.5 px-2 text-right text-zinc-200">{b.runs}</td>
                            <td className="py-3.5 px-2 text-right font-bold text-pink-400">{b.wickets}</td>
                            <td className="py-3.5 px-2 text-right text-zinc-400">{b.econ}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={6} className="py-8 text-center text-zinc-500">No bowling stats available yet.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          )}

          {activeTab === 'commentary' && (
            <div className="glass-panel p-6 rounded-2xl space-y-6 max-w-4xl mx-auto animate-fade-in">
              <h3 className="text-base font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                <Activity className="h-4.5 w-4.5 text-primary-400" />
                Ball-By-Ball Commentary Log
              </h3>

              <div className="space-y-4">
                {match.commentary && match.commentary.length > 0 ? (
                  match.commentary.map((c: any, idx: number) => (
                    <div key={idx} className="flex gap-4 border-b border-zinc-800/40 pb-4">
                      {/* Ball Number Tag */}
                      <span className="w-12 text-center py-1 bg-zinc-900 rounded-lg text-[10px] font-bold text-zinc-400 font-mono shrink-0 h-fit">
                        {c.ball}
                      </span>

                      {/* Event text & Badges */}
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center gap-2">
                          {c.event === 'six' && (
                            <span className="bg-pink-950/40 text-pink-400 border border-pink-900/30 px-2 py-0.5 rounded font-mono text-[9px] font-bold">
                              SIX
                            </span>
                          )}
                          {c.event === 'four' && (
                            <span className="bg-primary-950/40 text-primary-400 border border-primary-900/30 px-2 py-0.5 rounded font-mono text-[9px] font-bold">
                              FOUR
                            </span>
                          )}
                          {c.event === 'century' && (
                            <span className="bg-yellow-950/40 text-yellow-400 border border-yellow-900/30 px-2 py-0.5 rounded font-mono text-[9px] font-bold">
                              MILESTONE
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-zinc-300 leading-relaxed font-sans">{c.description}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="py-8 text-center text-zinc-500 text-sm">No live commentary log available.</div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'predictor' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fade-in">
              
              {/* Win Probability Pie Chart */}
              <div className="glass-panel p-6 rounded-2xl flex flex-col items-center">
                <h3 className="text-base font-bold text-white uppercase tracking-wider mb-6 self-start flex items-center gap-2">
                  <Award className="h-4.5 w-4.5 text-yellow-500" />
                  Live Win Probability Predictor
                </h3>
                
                <div className="h-60 w-60">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={75}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="flex gap-8 text-xs font-mono text-zinc-400 mt-4">
                  <div className="flex items-center gap-2">
                    <span className="h-3.5 w-3.5 rounded-full bg-[#4f73ff]" />
                    <span>{match.team_home.name}: <strong>{match.win_probability[match.team_home.short_name] ?? winProbHome}%</strong></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="h-3.5 w-3.5 rounded-full bg-[#db2777]" />
                    <span>{match.team_away.name}: <strong>{match.win_probability[match.team_away.short_name] ?? winProbAway}%</strong></span>
                  </div>
                </div>
              </div>

              {/* Statistical comparison */}
              <div className="glass-panel p-6 rounded-2xl">
                <h3 className="text-base font-bold text-white uppercase tracking-wider mb-6 flex items-center gap-2">
                  <Activity className="h-4.5 w-4.5 text-green-400" />
                  Match Attributes Comparison
                </h3>

                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={match.stats_comparison}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis dataKey="metric" stroke="#71717a" fontSize={10} />
                      <YAxis stroke="#71717a" fontSize={10} />
                      <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a' }} />
                      <Legend />
                      <Bar dataKey={match.team_home.short_name} fill="#4f73ff" radius={[4, 4, 0, 0]} />
                      <Bar dataKey={match.team_away.short_name} fill="#db2777" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

            </div>
          )}

          {/* AI Assistant Deep Link Panel */}
          <div className="glass-panel p-6 rounded-2xl bg-gradient-to-tr from-indigo-950/20 to-pink-950/15 flex flex-col md:flex-row justify-between items-center gap-6 relative z-10">
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-primary-400" />
                Analyze this live match with AI Assistant
              </h3>
              <p className="text-xs text-zinc-400 mt-1 max-w-xl">
                Ask CricketGPT to run projections, explain historical matchups, analyze seam indexes, or simulate batting innings for this match.
              </p>
            </div>
            <Link
              to={`/chat?q=Give me a complete AI prediction and tactical review of the ${match.team_home.name} vs ${match.team_away.name} live match based on the current score of ${match.team_home.score} after ${match.team_home.overs} overs.`}
              className="px-5 py-3 rounded-xl bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-500 hover:to-indigo-500 text-white font-semibold text-xs transition-all shadow-lg flex items-center space-x-2"
            >
              <Sparkles className="h-4 w-4" />
              <span>Launch AI In-depth Review</span>
            </Link>
          </div>

        </>
      )}

    </div>
  )
}
