import React, { useState, useEffect } from 'react'
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts'
import { Trophy, Activity, AlertCircle, ArrowLeftRight, Search } from 'lucide-react'

export default function ComparePlayers() {
  const [p1Id, setP1Id] = useState<number>(1)
  const [p2Id, setP2Id] = useState<number>(2)
  const [format, setFormat] = useState<string>("Test")
  const [p1Data, setP1Data] = useState<any>(null)
  const [p2Data, setP2Data] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  // Autocomplete search states
  const [search1, setSearch1] = useState("")
  const [search2, setSearch2] = useState("")
  const [sug1, setSug1] = useState<any[]>([])
  const [sug2, setSug2] = useState<any[]>([])
  const [showSug1, setShowSug1] = useState(false)
  const [showSug2, setShowSug2] = useState(false)

  // Initialize/Update search inputs ONLY when the loaded player data matches the selected ID
  useEffect(() => {
    if (p1Data && p1Data.id === p1Id) {
      setSearch1(p1Data.name)
    }
  }, [p1Data, p1Id])

  useEffect(() => {
    if (p2Data && p2Data.id === p2Id) {
      setSearch2(p2Data.name)
    }
  }, [p2Data, p2Id])

  // Debounced search for Player 1
  useEffect(() => {
    if (!search1.trim() || (p1Data && search1 === p1Data.name)) {
      setSug1([])
      return
    }
    const t = setTimeout(async () => {
      try {
        const res = await fetch(`/api/v1/stats/players?search=${encodeURIComponent(search1)}`)
        if (res.ok) {
          setSug1(await res.json())
        }
      } catch (e) {
        console.error(e)
      }
    }, 250)
    return () => clearTimeout(t)
  }, [search1, p1Data])

  // Debounced search for Player 2
  useEffect(() => {
    if (!search2.trim() || (p2Data && search2 === p2Data.name)) {
      setSug2([])
      return
    }
    const t = setTimeout(async () => {
      try {
        const res = await fetch(`/api/v1/stats/players?search=${encodeURIComponent(search2)}`)
        if (res.ok) {
          setSug2(await res.json())
        }
      } catch (e) {
        console.error(e)
      }
    }, 250)
    return () => clearTimeout(t)
  }, [search2, p2Data])

  // Fetch player details whenever IDs change
  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true)
      try {
        const [r1, r2] = await Promise.all([
          fetch(`/api/v1/stats/players/${p1Id}`),
          fetch(`/api/v1/stats/players/${p2Id}`)
        ])
        if (r1.ok && r2.ok) {
          setP1Data(await r1.json())
          setP2Data(await r2.json())
        }
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchStats()
  }, [p1Id, p2Id])

  const getStatByFormat = (player: any, f: string) => {
    if (!player || !player.stats) return null
    return player.stats.find((s: any) => s.format === f) || null
  }

  const p1FormatStats = getStatByFormat(p1Data, format)
  const p2FormatStats = getStatByFormat(p2Data, format)

  // Construct comparison data dynamically scaling batting & bowling metrics to 0-100 range
  const compareData = [
    {
      metric: 'Batting Avg',
      [p1Data?.name || 'Player 1']: Math.min(100, p1FormatStats?.batting_average || 0),
      [p2Data?.name || 'Player 2']: Math.min(100, p2FormatStats?.batting_average || 0)
    },
    {
      metric: 'Strike Rate (scaled)',
      [p1Data?.name || 'Player 1']: Math.min(100, ((p1FormatStats?.strike_rate || 0) / 160) * 100),
      [p2Data?.name || 'Player 2']: Math.min(100, ((p2FormatStats?.strike_rate || 0) / 160) * 100)
    },
    {
      metric: 'Centuries (scaled)',
      [p1Data?.name || 'Player 1']: Math.min(100, ((p1FormatStats?.centuries || 0) / 40) * 100),
      [p2Data?.name || 'Player 2']: Math.min(100, ((p2FormatStats?.centuries || 0) / 40) * 100)
    },
    {
      metric: 'Wickets (scaled)',
      [p1Data?.name || 'Player 1']: Math.min(100, ((p1FormatStats?.wickets_taken || 0) / 250) * 100),
      [p2Data?.name || 'Player 2']: Math.min(100, ((p2FormatStats?.wickets_taken || 0) / 250) * 100)
    },
    {
      metric: 'Economy (scaled)',
      [p1Data?.name || 'Player 1']: Math.max(0, Math.min(100, (12 - (p1FormatStats?.economy_rate || 12)) * 8.3)),
      [p2Data?.name || 'Player 2']: Math.max(0, Math.min(100, (12 - (p2FormatStats?.economy_rate || 12)) * 8.3))
    }
  ]

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white font-sans">Player comparison Analytics</h1>
        <p className="text-sm text-zinc-400 mt-1">Search any player in the world to dynamically fetch and cross-compare metrics</p>
      </div>

      {/* Select Box Rows */}
      <div className="glass-panel p-6 rounded-2xl flex flex-col md:flex-row gap-6 justify-between items-center relative z-20">
        
        {/* Player 1 Autocomplete */}
        <div className="w-full md:w-1/3 relative">
          <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Player 1</label>
          <div className="relative">
            <Search className="absolute left-3.5 top-3.5 h-4 w-4 text-zinc-500" />
            <input
              type="text"
              value={search1}
              onChange={(e) => setSearch1(e.target.value)}
              onFocus={() => setShowSug1(true)}
              onBlur={() => setTimeout(() => setShowSug1(false), 200)}
              onKeyDown={async (e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  if (sug1.length > 0) {
                    const top = sug1[0];
                    if (top.id === 0) {
                      try {
                        const res = await fetch(`/api/v1/stats/players?search=${encodeURIComponent(top.name)}&ingest=true`);
                        if (res.ok) {
                          const list = await res.json();
                          if (list.length > 0) {
                            setP1Id(list[0].id);
                            setSearch1(list[0].name);
                          }
                        }
                      } catch (err) {
                        console.error(err);
                      }
                    } else {
                      setP1Id(top.id);
                      setSearch1(top.name);
                    }
                    setShowSug1(false);
                  } else if (search1.trim()) {
                    try {
                      const res = await fetch(`/api/v1/stats/players?search=${encodeURIComponent(search1)}&ingest=true`);
                      if (res.ok) {
                        const list = await res.json();
                        if (list.length > 0) {
                          setP1Id(list[0].id);
                          setSearch1(list[0].name);
                          setShowSug1(false);
                        }
                      }
                    } catch (err) {
                      console.error(err);
                    }
                  }
                }
              }}
              placeholder="Search e.g. Babar Azam"
              spellCheck="false"
              className="w-full pl-10 pr-4 py-3 rounded-xl premium-input text-sm text-white"
            />
          </div>
          
          {showSug1 && (sug1.length > 0 || (search1 && search1 !== p1Data?.name)) && (
            <div className="absolute top-[76px] left-0 w-full glass-panel border border-zinc-800 rounded-xl overflow-hidden shadow-2xl max-h-56 overflow-y-auto z-30">
              {sug1.map(p => (
                <button
                  key={p.id}
                  onMouseDown={async (e) => {
                    e.preventDefault();
                    if (p.id === 0) {
                      try {
                        const res = await fetch(`/api/v1/stats/players?search=${encodeURIComponent(p.name)}&ingest=true`);
                        if (res.ok) {
                          const list = await res.json();
                          if (list.length > 0) {
                            setP1Id(list[0].id);
                            setSearch1(list[0].name);
                          }
                        }
                      } catch (err) {
                        console.error(err);
                      }
                    } else {
                      setP1Id(p.id);
                      setSearch1(p.name);
                    }
                    setShowSug1(false);
                  }}
                  className="w-full text-left px-4 py-2.5 hover:bg-zinc-800 text-xs text-white transition-colors border-b border-zinc-800/40"
                >
                  <p className="font-semibold">{p.name}</p>
                  <p className="text-[10px] text-zinc-400 mt-0.5">{p.country} • {p.batting_style}</p>
                </button>
              ))}
              {sug1.length === 0 && search1.trim() && (
                <button
                  onMouseDown={async (e) => {
                    e.preventDefault();
                    try {
                      const res = await fetch(`/api/v1/stats/players?search=${encodeURIComponent(search1)}&ingest=true`)
                      if (res.ok) {
                        const list = await res.json()
                        if (list.length > 0) {
                          setP1Id(list[0].id)
                          setSearch1(list[0].name)
                          setShowSug1(false)
                        }
                      }
                    } catch (err) {
                      console.error(err)
                    }
                  }}
                  className="w-full text-left px-4 py-3 hover:bg-primary-950/20 text-xs text-primary-400 font-semibold"
                >
                  + Add & ingest "{search1}" on-the-fly
                </button>
              )}
            </div>
          )}
        </div>

        {/* Separator badge */}
        <div className="bg-gradient-to-tr from-primary-600 to-pink-500 p-3 rounded-full text-white shadow-lg glow-indigo hidden md:block">
          <ArrowLeftRight className="h-5 w-5" />
        </div>

        {/* Player 2 Autocomplete */}
        <div className="w-full md:w-1/3 relative">
          <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Player 2</label>
          <div className="relative">
            <Search className="absolute left-3.5 top-3.5 h-4 w-4 text-zinc-500" />
            <input
              type="text"
              value={search2}
              onChange={(e) => setSearch2(e.target.value)}
              onFocus={() => setShowSug2(true)}
              onBlur={() => setTimeout(() => setShowSug2(false), 200)}
              onKeyDown={async (e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  if (sug2.length > 0) {
                    const top = sug2[0];
                    if (top.id === 0) {
                      try {
                        const res = await fetch(`/api/v1/stats/players?search=${encodeURIComponent(top.name)}&ingest=true`);
                        if (res.ok) {
                          const list = await res.json();
                          if (list.length > 0) {
                            setP2Id(list[0].id);
                            setSearch2(list[0].name);
                          }
                        }
                      } catch (err) {
                        console.error(err);
                      }
                    } else {
                      setP2Id(top.id);
                      setSearch2(top.name);
                    }
                    setShowSug2(false);
                  } else if (search2.trim()) {
                    try {
                      const res = await fetch(`/api/v1/stats/players?search=${encodeURIComponent(search2)}&ingest=true`);
                      if (res.ok) {
                        const list = await res.json();
                        if (list.length > 0) {
                          setP2Id(list[0].id);
                          setSearch2(list[0].name);
                          setShowSug2(false);
                        }
                      }
                    } catch (err) {
                      console.error(err);
                    }
                  }
                }
              }}
              placeholder="Search e.g. Pat Cummins"
              spellCheck="false"
              className="w-full pl-10 pr-4 py-3 rounded-xl premium-input text-sm text-white"
            />
          </div>

          {showSug2 && (sug2.length > 0 || (search2 && search2 !== p2Data?.name)) && (
            <div className="absolute top-[76px] left-0 w-full glass-panel border border-zinc-800 rounded-xl overflow-hidden shadow-2xl max-h-56 overflow-y-auto z-30">
              {sug2.map(p => (
                <button
                  key={p.id}
                  onMouseDown={async (e) => {
                    e.preventDefault();
                    if (p.id === 0) {
                      try {
                        const res = await fetch(`/api/v1/stats/players?search=${encodeURIComponent(p.name)}&ingest=true`);
                        if (res.ok) {
                          const list = await res.json();
                          if (list.length > 0) {
                            setP2Id(list[0].id);
                            setSearch2(list[0].name);
                          }
                        }
                      } catch (err) {
                        console.error(err);
                      }
                    } else {
                      setP2Id(p.id);
                      setSearch2(p.name);
                    }
                    setShowSug2(false);
                  }}
                  className="w-full text-left px-4 py-2.5 hover:bg-zinc-800 text-xs text-white transition-colors border-b border-zinc-800/40"
                >
                  <p className="font-semibold">{p.name}</p>
                  <p className="text-[10px] text-zinc-400 mt-0.5">{p.country} • {p.batting_style}</p>
                </button>
              ))}
              {sug2.length === 0 && search2.trim() && (
                <button
                  onMouseDown={async (e) => {
                    e.preventDefault();
                    try {
                      const res = await fetch(`/api/v1/stats/players?search=${encodeURIComponent(search2)}&ingest=true`)
                      if (res.ok) {
                        const list = await res.json()
                        if (list.length > 0) {
                          setP2Id(list[0].id)
                          setSearch2(list[0].name)
                          setShowSug2(false)
                        }
                      }
                    } catch (err) {
                      console.error(err)
                    }
                  }}
                  className="w-full text-left px-4 py-3 hover:bg-pink-950/20 text-xs text-pink-400 font-semibold"
                >
                  + Add & ingest "{search2}" on-the-fly
                </button>
              )}
            </div>
          )}
        </div>

        {/* Format Selector */}
        <div className="w-full md:w-1/5">
          <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Format</label>
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value)}
            className="w-full px-4 py-3 rounded-xl premium-input text-sm text-white border-primary-500/40"
          >
            <option value="Test">Test Match</option>
            <option value="ODI">One Day Int (ODI)</option>
            <option value="IPL">IPL T20</option>
          </select>
        </div>

      </div>

      {loading ? (
        <div className="text-center py-12 text-zinc-500">Compiling statistics profiles...</div>
      ) : (
        /* Metrics Comparison Grid */
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Player Cards */}
            <div className="glass-panel p-6 rounded-2xl border-l-4 border-primary-500 relative">
              <span className="text-[10px] uppercase font-mono tracking-widest text-primary-400">{p1Data?.country}</span>
              <h3 className="text-2xl font-bold text-white mt-1">{p1Data?.name}</h3>
              <div className="mt-4 grid grid-cols-2 gap-4 text-sm text-zinc-400 border-t border-zinc-800 pt-4">
                <div>
                  <span>Batting Style</span>
                  <p className="font-semibold text-zinc-200 mt-0.5">{p1Data?.batting_style || "N/A"}</p>
                </div>
                <div>
                  <span>Bowling Style</span>
                  <p className="font-semibold text-zinc-200 mt-0.5">{p1Data?.bowling_style || "N/A"}</p>
                </div>
              </div>
            </div>

            <div className="glass-panel p-6 rounded-2xl border-l-4 border-pink-500 relative">
              <span className="text-[10px] uppercase font-mono tracking-widest text-pink-400">{p2Data?.country}</span>
              <h3 className="text-2xl font-bold text-white mt-1">{p2Data?.name}</h3>
              <div className="mt-4 grid grid-cols-2 gap-4 text-sm text-zinc-400 border-t border-zinc-800 pt-4">
                <div>
                  <span>Batting Style</span>
                  <p className="font-semibold text-zinc-200 mt-0.5">{p2Data?.batting_style || "N/A"}</p>
                </div>
                <div>
                  <span>Bowling Style</span>
                  <p className="font-semibold text-zinc-200 mt-0.5">{p2Data?.bowling_style || "N/A"}</p>
                </div>
              </div>
            </div>

          </div>

          {/* Graphical Comparison Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 relative z-10">
            
            {/* Table layout comparing */}
            <div className="glass-panel p-6 rounded-2xl lg:col-span-1 space-y-4">
              <h4 className="text-sm font-bold uppercase tracking-wider text-zinc-300">Format Metrics</h4>
              
              {!p1FormatStats || !p2FormatStats ? (
                <div className="flex gap-2.5 items-center p-3 rounded-lg border border-yellow-900/30 bg-yellow-950/15 text-xs text-yellow-400">
                  <AlertCircle className="h-4.5 w-4.5 shrink-0" />
                  <span>One of the players lacks statistics records for this format.</span>
                </div>
              ) : (
                <div className="space-y-4.5 pt-2 text-xs">
                  <div className="flex justify-between border-b border-zinc-800 pb-2.5">
                    <span className="text-zinc-500">Matches</span>
                    <span className="font-semibold">{p1FormatStats.matches_played} vs {p2FormatStats.matches_played}</span>
                  </div>
                  <div className="flex justify-between border-b border-zinc-800 pb-2.5">
                    <span className="text-zinc-500">Runs Scored</span>
                    <span className="font-semibold text-white">{p1FormatStats.runs_scored} vs {p2FormatStats.runs_scored}</span>
                  </div>
                  <div className="flex justify-between border-b border-zinc-800 pb-2.5">
                    <span className="text-zinc-500">Batting Average</span>
                    <span className="font-semibold text-primary-400">{p1FormatStats.batting_average} vs {p2FormatStats.batting_average}</span>
                  </div>
                  <div className="flex justify-between border-b border-zinc-800 pb-2.5">
                    <span className="text-zinc-500">Strike Rate</span>
                    <span className="font-semibold">{p1FormatStats.strike_rate} vs {p2FormatStats.strike_rate}</span>
                  </div>
                  <div className="flex justify-between border-b border-zinc-800 pb-2.5">
                    <span className="text-zinc-500">Centuries</span>
                    <span className="font-semibold text-pink-400">{p1FormatStats.centuries} vs {p2FormatStats.centuries}</span>
                  </div>
                  <div className="flex justify-between border-b border-zinc-800 pb-2.5">
                    <span className="text-zinc-500">Wickets</span>
                    <span className="font-semibold text-primary-400">{p1FormatStats.wickets_taken} vs {p2FormatStats.wickets_taken}</span>
                  </div>
                  <div className="flex justify-between border-b border-zinc-800 pb-2.5">
                    <span className="text-zinc-500">Bowl Average</span>
                    <span className="font-semibold">{p1FormatStats.bowling_average} vs {p2FormatStats.bowling_average}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Economy Rate</span>
                    <span className="font-semibold text-pink-400">{p1FormatStats.economy_rate} vs {p2FormatStats.economy_rate}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Radar Comparison Chart */}
            <div className="glass-panel p-6 rounded-2xl lg:col-span-2">
              <h4 className="text-sm font-bold uppercase tracking-wider text-zinc-300 mb-6">Radar Career Attributes</h4>
              <div className="h-72 w-full flex justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="80%" data={compareData}>
                    <PolarGrid stroke="#27272a" />
                    <PolarAngleAxis dataKey="metric" stroke="#71717a" fontSize={10} />
                    <PolarRadiusAxis domain={[0, 100]} tick={false} stroke="#27272a" />
                    <Radar name={p1Data?.name || 'Player 1'} dataKey={p1Data?.name || 'Player 1'} stroke="#4f73ff" fill="#4f73ff" fillOpacity={0.2} />
                    <Radar name={p2Data?.name || 'Player 2'} dataKey={p2Data?.name || 'Player 2'} stroke="#db2777" fill="#db2777" fillOpacity={0.2} />
                    <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '12px' }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>
        </div>
      )}

    </div>
  )
}
