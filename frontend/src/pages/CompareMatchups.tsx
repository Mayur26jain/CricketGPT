import React, { useState, useEffect } from 'react'
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts'
import { Search, ShieldAlert, Zap, ArrowLeftRight } from 'lucide-react'

export default function CompareMatchups() {
  const [batsmanId, setBatsmanId] = useState<number>(1) // Virat Kohli
  const [bowlerId, setBowlerId] = useState<number>(2) // Joe Root
  const [matchupData, setMatchupData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  // Search autocomplete states
  const [searchBatsman, setSearchBatsman] = useState("")
  const [searchBowler, setSearchBowler] = useState("")
  const [sugBatsman, setSugBatsman] = useState<any[]>([])
  const [sugBowler, setSugBowler] = useState<any[]>([])
  const [showSugBatsman, setShowSugBatsman] = useState(false)
  const [showSugBowler, setShowSugBowler] = useState(false)

  // Fetch initial details
  const [p1, setP1] = useState<any>(null)
  const [p2, setP2] = useState<any>(null)

  useEffect(() => {
    const fetchPlayerInfo = async () => {
      try {
        const [r1, r2] = await Promise.all([
          fetch(`/api/v1/stats/players/${batsmanId}`),
          fetch(`/api/v1/stats/players/${bowlerId}`)
        ])
        if (r1.ok && r2.ok) {
          const d1 = await r1.json()
          const d2 = await r2.json()
          setP1(d1)
          setP2(d2)
        }
      } catch (e) {
        console.error(e)
      }
    }
    fetchPlayerInfo()
  }, [batsmanId, bowlerId])

  // Initialize/Update search inputs ONLY when the loaded player data matches the selected ID
  useEffect(() => {
    if (p1 && p1.id === batsmanId) {
      setSearchBatsman(p1.name)
    }
  }, [p1, batsmanId])

  useEffect(() => {
    if (p2 && p2.id === bowlerId) {
      setSearchBowler(p2.name)
    }
  }, [p2, bowlerId])

  // Debounced search for Batsman
  useEffect(() => {
    if (!searchBatsman.trim() || (p1 && searchBatsman === p1.name)) {
      setSugBatsman([])
      return
    }
    const t = setTimeout(async () => {
      try {
        const res = await fetch(`/api/v1/stats/players?search=${encodeURIComponent(searchBatsman)}`)
        if (res.ok) {
          setSugBatsman(await res.json())
        }
      } catch (e) {
        console.error(e)
      }
    }, 250)
    return () => clearTimeout(t)
  }, [searchBatsman, p1])

  // Debounced search for Bowler
  useEffect(() => {
    if (!searchBowler.trim() || (p2 && searchBowler === p2.name)) {
      setSugBowler([])
      return
    }
    const t = setTimeout(async () => {
      try {
        const res = await fetch(`/api/v1/stats/players?search=${encodeURIComponent(searchBowler)}`)
        if (res.ok) {
          setSugBowler(await res.json())
        }
      } catch (e) {
        console.error(e)
      }
    }, 250)
    return () => clearTimeout(t)
  }, [searchBowler, p2])

  // Fetch matchup statistics when selected IDs change
  useEffect(() => {
    const fetchMatchup = async () => {
      setLoading(true)
      try {
        const res = await fetch(`/api/v1/stats/matchup?batsman_id=${batsmanId}&bowler_id=${bowlerId}`)
        if (res.ok) {
          setMatchupData(await res.json())
        }
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchMatchup()
  }, [batsmanId, bowlerId])

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white font-sans">Batsman vs Bowler Matchup Analytics</h1>
        <p className="text-sm text-zinc-400 mt-1">Explore head-to-head metrics: Runs scored, balls faced, strike rate, and bowler dismissals on-the-fly.</p>
      </div>

      {/* Selectors */}
      <div className="glass-panel p-6 rounded-2xl flex flex-col md:flex-row gap-6 justify-between items-center relative z-20">
        
        {/* Batsman Selector */}
        <div className="w-full md:w-2/5 relative">
          <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Batsman</label>
          <div className="relative">
            <Search className="absolute left-3.5 top-3.5 h-4 w-4 text-zinc-500" />
            <input
              type="text"
              value={searchBatsman}
              onChange={(e) => setSearchBatsman(e.target.value)}
              onFocus={() => setShowSugBatsman(true)}
              onBlur={() => setTimeout(() => setShowSugBatsman(false), 200)}
              onKeyDown={async (e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  if (sugBatsman.length > 0) {
                    const top = sugBatsman[0];
                    if (top.id === 0) {
                      try {
                        const res = await fetch(`/api/v1/stats/players?search=${encodeURIComponent(top.name)}&ingest=true`);
                        if (res.ok) {
                          const list = await res.json();
                          if (list.length > 0) {
                            setBatsmanId(list[0].id);
                            setSearchBatsman(list[0].name);
                          }
                        }
                      } catch (err) {
                        console.error(err);
                      }
                    } else {
                      setBatsmanId(top.id);
                      setSearchBatsman(top.name);
                    }
                    setShowSugBatsman(false);
                  } else if (searchBatsman.trim()) {
                    try {
                      const res = await fetch(`/api/v1/stats/players?search=${encodeURIComponent(searchBatsman)}&ingest=true`);
                      if (res.ok) {
                        const list = await res.json();
                        if (list.length > 0) {
                          setBatsmanId(list[0].id);
                          setSearchBatsman(list[0].name);
                          setShowSugBatsman(false);
                        }
                      }
                    } catch (err) {
                      console.error(err);
                    }
                  }
                }
              }}
              placeholder="Search Batsman (e.g. Virat Kohli)"
              spellCheck="false"
              className="w-full pl-10 pr-4 py-3 rounded-xl premium-input text-sm text-white"
            />
          </div>

          {showSugBatsman && (sugBatsman.length > 0 || (searchBatsman && searchBatsman !== p1?.name)) && (
            <div className="absolute top-[76px] left-0 w-full glass-panel border border-zinc-800 rounded-xl overflow-hidden shadow-2xl max-h-56 overflow-y-auto z-30">
              {sugBatsman.map(p => (
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
                            setBatsmanId(list[0].id);
                            setSearchBatsman(list[0].name);
                          }
                        }
                      } catch (err) {
                        console.error(err);
                      }
                    } else {
                      setBatsmanId(p.id);
                      setSearchBatsman(p.name);
                    }
                    setShowSugBatsman(false);
                  }}
                  className="w-full text-left px-4 py-2.5 hover:bg-zinc-800 text-xs text-white transition-colors border-b border-zinc-800/40"
                >
                  <p className="font-semibold">{p.name}</p>
                  <p className="text-[10px] text-zinc-400 mt-0.5">{p.country} • {p.batting_style}</p>
                </button>
              ))}
              {sugBatsman.length === 0 && searchBatsman.trim() && (
                <button
                  onMouseDown={async (e) => {
                    e.preventDefault();
                    try {
                      const res = await fetch(`/api/v1/stats/players?search=${encodeURIComponent(searchBatsman)}&ingest=true`)
                      if (res.ok) {
                        const list = await res.json()
                        if (list.length > 0) {
                          setBatsmanId(list[0].id)
                          setSearchBatsman(list[0].name)
                          setShowSugBatsman(false)
                        }
                      }
                    } catch (err) {
                      console.error(err)
                    }
                  }}
                  className="w-full text-left px-4 py-3 hover:bg-primary-950/20 text-xs text-primary-400 font-semibold"
                >
                  + Add & Ingest "{searchBatsman}" on-the-fly
                </button>
              )}
            </div>
          )}
        </div>

        {/* VS Separator */}
        <div className="bg-gradient-to-tr from-rose-500 to-amber-500 p-3 rounded-full text-white shadow-lg glow-indigo hidden md:block">
          <ArrowLeftRight className="h-5 w-5" />
        </div>

        {/* Bowler Selector */}
        <div className="w-full md:w-2/5 relative">
          <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Bowler</label>
          <div className="relative">
            <Search className="absolute left-3.5 top-3.5 h-4 w-4 text-zinc-500" />
            <input
              type="text"
              value={searchBowler}
              onChange={(e) => setSearchBowler(e.target.value)}
              onFocus={() => setShowSugBowler(true)}
              onBlur={() => setTimeout(() => setShowSugBowler(false), 200)}
              onKeyDown={async (e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  if (sugBowler.length > 0) {
                    const top = sugBowler[0];
                    if (top.id === 0) {
                      try {
                        const res = await fetch(`/api/v1/stats/players?search=${encodeURIComponent(top.name)}&ingest=true`);
                        if (res.ok) {
                          const list = await res.json();
                          if (list.length > 0) {
                            setBowlerId(list[0].id);
                            setSearchBowler(list[0].name);
                          }
                        }
                      } catch (err) {
                        console.error(err);
                      }
                    } else {
                      setBowlerId(top.id);
                      setSearchBowler(top.name);
                    }
                    setShowSugBowler(false);
                  } else if (searchBowler.trim()) {
                    try {
                      const res = await fetch(`/api/v1/stats/players?search=${encodeURIComponent(searchBowler)}&ingest=true`);
                      if (res.ok) {
                        const list = await res.json();
                        if (list.length > 0) {
                          setBowlerId(list[0].id);
                          setSearchBowler(list[0].name);
                          setShowSugBowler(false);
                        }
                      }
                    } catch (err) {
                      console.error(err);
                    }
                  }
                }
              }}
              placeholder="Search Bowler (e.g. Jasprit Bumrah)"
              spellCheck="false"
              className="w-full pl-10 pr-4 py-3 rounded-xl premium-input text-sm text-white"
            />
          </div>

          {showSugBowler && (sugBowler.length > 0 || (searchBowler && searchBowler !== p2?.name)) && (
            <div className="absolute top-[76px] left-0 w-full glass-panel border border-zinc-800 rounded-xl overflow-hidden shadow-2xl max-h-56 overflow-y-auto z-30">
              {sugBowler.map(p => (
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
                            setBowlerId(list[0].id);
                            setSearchBowler(list[0].name);
                          }
                        }
                      } catch (err) {
                        console.error(err);
                      }
                    } else {
                      setBowlerId(p.id);
                      setSearchBowler(p.name);
                    }
                    setShowSugBowler(false);
                  }}
                  className="w-full text-left px-4 py-2.5 hover:bg-zinc-800 text-xs text-white transition-colors border-b border-zinc-800/40"
                >
                  <p className="font-semibold">{p.name}</p>
                  <p className="text-[10px] text-zinc-400 mt-0.5">{p.country} • {p.bowling_style}</p>
                </button>
              ))}
              {sugBowler.length === 0 && searchBowler.trim() && (
                <button
                  onMouseDown={async (e) => {
                    e.preventDefault();
                    try {
                      const res = await fetch(`/api/v1/stats/players?search=${encodeURIComponent(searchBowler)}&ingest=true`)
                      if (res.ok) {
                        const list = await res.json()
                        if (list.length > 0) {
                          setBowlerId(list[0].id)
                          setSearchBowler(list[0].name)
                          setShowSugBowler(false)
                        }
                      }
                    } catch (err) {
                      console.error(err)
                    }
                  }}
                  className="w-full text-left px-4 py-3 hover:bg-rose-950/20 text-xs text-rose-400 font-semibold"
                >
                  + Add & Ingest "{searchBowler}" on-the-fly
                </button>
              )}
            </div>
          )}
        </div>

      </div>

      {loading ? (
        <div className="text-center py-12 text-zinc-500">Calculating matchup dynamics...</div>
      ) : matchupData ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Detailed Matchup Stats Card */}
          <div className="glass-panel p-6 rounded-2xl lg:col-span-2 space-y-6">
            <div className="flex justify-between items-center border-b border-zinc-800 pb-4">
              <h2 className="text-xl font-bold text-white">Matchup Statistics</h2>
              <span className="bg-rose-500/10 text-rose-400 px-3 py-1 rounded-full text-xs font-mono">Head-to-Head</span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="bg-zinc-900/40 p-4 rounded-xl border border-zinc-800/40">
                <span className="text-xs text-zinc-500 block">Runs Scored</span>
                <p className="text-2xl font-extrabold text-white mt-1">{matchupData.runs}</p>
              </div>
              <div className="bg-zinc-900/40 p-4 rounded-xl border border-zinc-800/40">
                <span className="text-xs text-zinc-500 block">Balls Faced</span>
                <p className="text-2xl font-extrabold text-white mt-1">{matchupData.balls}</p>
              </div>
              <div className="bg-zinc-900/40 p-4 rounded-xl border border-zinc-800/40">
                <span className="text-xs text-zinc-500 block">Strike Rate</span>
                <p className="text-2xl font-extrabold text-primary-400 mt-1">{matchupData.strike_rate}</p>
              </div>
              <div className="bg-zinc-900/40 p-4 rounded-xl border border-zinc-800/40">
                <span className="text-xs text-zinc-500 block">Bowler Dismissals</span>
                <p className="text-2xl font-extrabold text-rose-400 mt-1">{matchupData.dismissals}</p>
              </div>
            </div>

            {/* Sub-indicators */}
            <div className="border-t border-zinc-800 pt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="flex justify-between items-center py-2 border-b border-zinc-800/40">
                <span className="text-xs text-zinc-500">Batting Average</span>
                <span className="text-sm font-semibold text-zinc-200">{matchupData.average}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-zinc-800/40">
                <span className="text-xs text-zinc-500">Dot Ball %</span>
                <span className="text-sm font-semibold text-zinc-200">{matchupData.dots_pct}%</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-zinc-800/40">
                <span className="text-xs text-zinc-500">Fours / Sixes</span>
                <span className="text-sm font-semibold text-zinc-200">{matchupData.fours} / {matchupData.sixes}</span>
              </div>
            </div>

            {/* Tactical Advice */}
            <div className="bg-gradient-to-r from-primary-950/20 to-zinc-900/40 p-5 rounded-2xl border border-primary-500/20 flex gap-4">
              <Zap className="h-6 w-6 text-primary-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-bold text-zinc-200">AI Tactical Summary</h4>
                <p className="text-xs text-zinc-400 mt-1 leading-relaxed">
                  {matchupData.batsman} has scoring options against {matchupData.bowler} with a strike rate of {matchupData.strike_rate}. However, {matchupData.bowler} has claimed their wicket {matchupData.dismissals} times, showing clear tactical battles in the middle overs.
                </p>
              </div>
            </div>
          </div>

          {/* Dismissal Types Distribution Pie Chart */}
          <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-300 mb-2">Dismissal Distribution</h3>
              <p className="text-[11px] text-zinc-500">Breakdown of bowler dismissals against this batsman</p>
            </div>
            
            <div className="h-52 w-full flex items-center justify-center my-4">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={matchupData.dismissal_types || []}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={75}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {(matchupData.dismissal_types || []).map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '12px' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="space-y-2 border-t border-zinc-800/60 pt-4 text-xs">
              {(matchupData.dismissal_types || []).map((d: any, i: number) => (
                <div key={i} className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }}></span>
                    <span className="text-zinc-400">{d.name}</span>
                  </div>
                  <span className="font-semibold text-zinc-200">{d.value}</span>
                </div>
              ))}
            </div>
          </div>

        </div>
      ) : (
        <div className="text-center py-12 text-zinc-500 flex flex-col items-center gap-3">
          <ShieldAlert className="h-8 w-8 text-zinc-600" />
          <span>No matchup data found. Please select or ingest players above.</span>
        </div>
      )}

    </div>
  )
}
