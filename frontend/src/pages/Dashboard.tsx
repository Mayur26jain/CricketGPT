import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts'
import { Trophy, Activity, CloudSun, FileText, ChevronRight, MessageSquare, RefreshCw } from 'lucide-react'

export default function Dashboard() {
  const [liveScores, setLiveScores] = useState<any[]>([])
  const [news, setNews] = useState<any[]>([])
  const [weather, setWeather] = useState<any>(null)
  const [weatherVenue, setWeatherVenue] = useState("Colombo (R. Premadasa)")
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [syncMessage, setSyncMessage] = useState("Sync Live Data")

  const handleSync = async () => {
    setSyncing(true)
    setSyncMessage("Syncing...")
    try {
      const res = await fetch("/api/v1/matches/sync", { method: "POST" })
      if (res.ok) {
        setSyncMessage("Synced Successfully!")
        const scoresRes = await fetch("/api/v1/matches/live")
        if (scoresRes.ok) {
          const scores = await scoresRes.json()
          setLiveScores(scores)
        }
      } else {
        setSyncMessage("Sync Failed (Check Key)")
      }
    } catch (e) {
      console.error(e)
      setSyncMessage("Error Syncing")
    } finally {
      setTimeout(() => {
        setSyncing(false)
        setSyncMessage("Sync Live Data")
      }, 2500)
    }
  }

  useEffect(() => {
    // Fetch live scores, news, and weather in parallel
    const fetchData = async () => {
      try {
        const [scoresRes, newsRes, weatherDetail] = await Promise.all([
          fetch("/api/v1/matches/live"),
          // Fetch from static mock endpoints or fallback
          Promise.resolve([
            {
              title: "Virat Kohli slams historic 50th ODI century at Lord's",
              description: "Indian batting maestro Virat Kohli has broken the record for the most ODI centuries, crossing Sachin Tendulkar's tally in front of a packed stadium.",
              source: "ESPN Cricinfo"
            },
            {
              title: "IPL 2026 scheduling announced: MI to face CSK in opener",
              description: "The BCCI has officially released the schedule for IPL 2026. High stakes, modern stadiums, and complete analytics packages await fans.",
              source: "Cricbuzz"
            }
          ]),
          fetch("/api/v1/matches/live/details?match_id=1")
            .then(r => r.ok ? r.json() : null)
            .catch(() => null)
        ])

        const scores = await scoresRes.json()
        setLiveScores(scores)
        setNews(newsRes)
        if (weatherDetail) {
          setWeather(weatherDetail.weather)
          setWeatherVenue(weatherDetail.venue)
        } else {
          setWeather({
            temp: 27.5,
            condition: "Rain Shower / Monsoon clouds",
            humidity: 88,
            rain_prob: "80%"
          })
          setWeatherVenue("Colombo (R. Premadasa)")
        }
      } catch (e) {
        console.error("Dashboard fetch failed", e)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  // Career Runs comparison chart data
  const runsData = [
    { name: 'Tendulkar', Runs: 18426 },
    { name: 'Kohli', Runs: 13848 },
    { name: 'Root', Runs: 6522 },
    { name: 'Smith', Runs: 5446 },
    { name: 'Dhoni', Runs: 10773 }
  ]

  const radarData = [
    { subject: 'Average', A: 85, B: 75, fullMark: 100 },
    { subject: 'Strike Rate', A: 93, B: 86, fullMark: 100 },
    { subject: 'Centuries', A: 100, B: 64, fullMark: 100 },
    { subject: 'Matches', A: 90, B: 58, fullMark: 100 },
    { subject: 'High Score', A: 91, B: 66, fullMark: 100 }
  ]

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white font-sans">Analytical Dashboard</h1>
          <p className="text-sm text-zinc-400 mt-1">Real-time match data, weather widgets, and historical statistics</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-semibold border border-zinc-800 bg-zinc-900/60 hover:bg-zinc-800 text-zinc-300 disabled:opacity-50 transition-all duration-200"
          >
            <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin text-primary-400' : ''}`} />
            <span>{syncMessage}</span>
          </button>
          <Link
            to="/chat"
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-primary-600 to-teal-600 hover:from-primary-500 hover:to-teal-500 text-white shadow-lg shadow-primary-500/10 transition-all duration-200"
          >
            <MessageSquare className="h-4 w-4" />
            <span>Ask AI Assistant</span>
          </Link>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 relative z-10">
        
        {/* Live Match Center Panel */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl flex flex-col justify-between min-h-[250px]">
          <div>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <Activity className="h-4.5 w-4.5 text-primary-400 animate-pulse" />
                <span className="text-sm font-bold uppercase tracking-wider text-zinc-300">Live & Upcoming Matches</span>
              </div>
              <Link to="/match-center" className="text-xs text-primary-400 hover:text-primary-300 font-semibold transition-colors flex items-center gap-1">
                <span>View Match Center</span>
                <ChevronRight className="h-3 w-3" />
              </Link>
            </div>
            
            {liveScores.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {liveScores.slice(0, 4).map((m) => {
                  const isLive = m.status === 'Live'
                  const isUpcoming = m.status === 'Upcoming'
                  
                  return (
                    <Link
                      key={m.id}
                      to={`/match-center?match_id=${m.id}`}
                      className="p-4 bg-zinc-900/40 hover:bg-zinc-900/80 border border-zinc-800/80 hover:border-zinc-700 rounded-xl transition-all duration-200 block group"
                    >
                      <div className="flex justify-between items-center text-[9px] font-bold uppercase tracking-wider mb-2">
                        <span className="text-zinc-500">{m.match_type}</span>
                        <span className={`px-2 py-0.5 rounded ${
                          isLive ? 'bg-red-950/60 text-red-400 border border-red-900/40' :
                          isUpcoming ? 'bg-blue-950/60 text-blue-400 border border-blue-900/40' :
                          'bg-zinc-800 text-zinc-400'
                        }`}>
                          {m.status}
                        </span>
                      </div>
                      
                      <div className="space-y-1.5">
                        <div className="flex justify-between text-xs font-semibold text-white group-hover:text-primary-400 transition-colors">
                          <span className="truncate">{m.team_home}</span>
                          {m.scores && (
                            <span>{m.scores.team_home_runs}/{m.scores.team_home_wickets}</span>
                          )}
                        </div>
                        <div className="flex justify-between text-xs font-semibold text-zinc-300">
                          <span className="truncate">{m.team_away}</span>
                          {m.scores && m.scores.team_away_runs > 0 && (
                            <span>{m.scores.team_away_runs}/{m.scores.team_away_wickets}</span>
                          )}
                        </div>
                      </div>

                      <div className="text-[9px] text-zinc-500 truncate mt-3 border-t border-zinc-800/50 pt-2">
                        {m.result ? m.result : m.venue}
                      </div>
                    </Link>
                  )
                })}
              </div>
            ) : (
              <div className="py-8 text-center text-zinc-500 text-sm">No live matches currently. Check back later.</div>
            )}
          </div>
        </div>

        {/* Venue Weather Card */}
        <Link
          to={`/chat?q=Explain how weather in ${weatherVenue} affects swing index and spin decay based on current weather condition: ${weather ? weather.condition : 'Rain Shower'} and temp: ${weather ? weather.temp : 27.5}°C.`}
          className="glass-panel p-6 rounded-2xl flex flex-col justify-between hover:border-pink-500/50 hover:shadow-lg transition-all duration-250 block cursor-pointer group"
        >
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <CloudSun className="h-4.5 w-4.5 text-pink-400" />
              <span className="text-sm font-bold uppercase tracking-wider text-zinc-300">Venue Weather Update</span>
            </div>
            
            {weather ? (
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <div>
                    <h4 className="text-lg font-bold text-white group-hover:text-pink-400 transition-colors truncate max-w-[200px]">{weatherVenue}</h4>
                    <p className="text-xs text-zinc-400">{weather.condition}</p>
                  </div>
                  <span className="text-3xl font-extrabold text-white">{weather.temp}°C</span>
                </div>
                <div className="grid grid-cols-2 gap-4 pt-3 text-xs border-t border-zinc-800/80 text-zinc-400">
                  <div>
                    <span>Humidity</span>
                    <p className="font-semibold text-zinc-200 mt-0.5">{weather.humidity}%</p>
                  </div>
                  <div>
                    <span>Rain Probability</span>
                    <p className="font-semibold text-zinc-200 mt-0.5">{weather.rain_prob}</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center text-zinc-500 text-sm">Fetching weather...</div>
            )}
          </div>

          <p className="text-[10px] text-zinc-500 leading-normal mt-4 border-t border-zinc-800/80 pt-3 flex justify-between items-center font-semibold text-pink-400">
            <span>Weather influences swing index</span>
            <ChevronRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
          </p>
        </Link>

      </div>

      {/* Analytics Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 relative z-10">
        
        {/* Recharts Bar Chart */}
        <Link
          to="/compare-players"
          className="glass-panel p-6 rounded-2xl block hover:border-yellow-500/50 hover:shadow-lg transition-all duration-250 cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-2">
              <Trophy className="h-4.5 w-4.5 text-yellow-500" />
              <span className="text-sm font-bold uppercase tracking-wider text-zinc-300">Historical ODI Career Runs</span>
            </div>
            <span className="text-xs text-yellow-500 font-semibold flex items-center gap-0.5">
              Compare <ChevronRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
            </span>
          </div>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={runsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="name" stroke="#71717a" fontSize={12} />
                <YAxis stroke="#71717a" fontSize={12} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '12px' }}
                  labelStyle={{ color: '#fff', fontWeight: 'bold' }}
                />
                <Bar dataKey="Runs" fill="#4f73ff" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Link>

        {/* Recharts Radar Chart */}
        <Link
          to="/compare-players"
          className="glass-panel p-6 rounded-2xl block hover:border-green-500/50 hover:shadow-lg transition-all duration-250 cursor-pointer group"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-2">
              <Activity className="h-4.5 w-4.5 text-green-400" />
              <span className="text-sm font-bold uppercase tracking-wider text-zinc-300">Virat Kohli vs Joe Root Profile</span>
            </div>
            <span className="text-xs text-green-400 font-semibold flex items-center gap-0.5">
              Compare <ChevronRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
            </span>
          </div>
          <div className="h-72 w-full flex justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                <PolarGrid stroke="#27272a" />
                <PolarAngleAxis dataKey="subject" stroke="#71717a" fontSize={11} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#27272a" tick={false} />
                <Radar name="Virat Kohli" dataKey="A" stroke="#4f73ff" fill="#4f73ff" fillOpacity={0.25} />
                <Radar name="Joe Root" dataKey="B" stroke="#db2777" fill="#db2777" fillOpacity={0.25} />
                <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '12px' }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </Link>

      </div>

      {/* News Columns */}
      <div className="glass-panel p-6 rounded-2xl relative z-10">
        <div className="flex items-center space-x-2 mb-6">
          <FileText className="h-4.5 w-4.5 text-indigo-400" />
          <span className="text-sm font-bold uppercase tracking-wider text-zinc-300">Featured Cricket News</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {news.map((item, index) => (
            <Link
              key={index}
              to={`/chat?q=Analyze this cricket news headline: ${encodeURIComponent(item.title)}`}
              className="glass-card p-5 rounded-xl border border-zinc-800/80 flex flex-col justify-between hover:border-primary-500/50 hover:bg-zinc-900/40 transition-all duration-200 cursor-pointer group"
            >
              <div>
                <span className="text-[10px] uppercase font-mono tracking-widest text-primary-400">{item.source}</span>
                <h4 className="text-base font-bold text-white mt-1.5 leading-snug group-hover:text-primary-400 transition-colors">{item.title}</h4>
                <p className="text-xs text-zinc-400 mt-2 leading-relaxed">{item.description}</p>
              </div>
              <div className="text-[10px] text-zinc-500 font-mono mt-4 pt-3 border-t border-zinc-800/60 flex items-center justify-between">
                <span>ANALYZED BY AI AGENT</span>
                <ChevronRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </Link>
          ))}
        </div>
      </div>

    </div>
  )
}
