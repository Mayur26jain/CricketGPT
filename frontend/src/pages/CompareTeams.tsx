import React, { useState, useEffect } from 'react'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'
import { Trophy, Activity, ArrowLeftRight, Search, ShieldAlert } from 'lucide-react'

export default function CompareTeams() {
  const [team1Id, setTeam1Id] = useState<number>(1)
  const [team2Id, setTeam2Id] = useState<number>(2)
  const [teams, setTeams] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  // Autocomplete search states
  const [search1, setSearch1] = useState("")
  const [search2, setSearch2] = useState("")
  const [sug1, setSug1] = useState<any[]>([])
  const [sug2, setSug2] = useState<any[]>([])
  const [showSug1, setShowSug1] = useState(false)
  const [showSug2, setShowSug2] = useState(false)

  // Track last selected team IDs to prevent reset overwrites
  // Team Rankings States
  const [t1Rank, setT1Rank] = useState<any>(null)
  const [t2Rank, setT2Rank] = useState<any>(null)

  // Load all initial teams for seeding defaults
  useEffect(() => {
    const fetchInitial = async () => {
      try {
        const res = await fetch("/api/v1/stats/teams")
        if (res.ok) {
          const list = await res.json()
          setTeams(list)
        }
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchInitial()
  }, [])

  const t1 = teams.find(t => t.id === team1Id)
  const t2 = teams.find(t => t.id === team2Id)

  // Populate search bars ONLY when team IDs change
  useEffect(() => {
    if (t1 && t1.id === team1Id) {
      setSearch1(t1.name)
    }
  }, [t1, team1Id])

  useEffect(() => {
    if (t2 && t2.id === team2Id) {
      setSearch2(t2.name)
    }
  }, [t2, team2Id])

  // Fetch Team Rankings details when compared IDs change
  useEffect(() => {
    const fetchRankings = async () => {
      try {
        const [r1, r2] = await Promise.all([
          fetch(`/api/v1/stats/teams/${team1Id}/rankings`),
          fetch(`/api/v1/stats/teams/${team2Id}/rankings`)
        ])
        if (r1.ok && r2.ok) {
          setT1Rank(await r1.json())
          setT2Rank(await r2.json())
        }
      } catch (e) {
        console.error(e)
      }
    }
    fetchRankings()
  }, [team1Id, team2Id])

  // Debounced search for Team 1
  useEffect(() => {
    if (!search1.trim() || (t1 && search1 === t1.name)) {
      setSug1([])
      return
    }
    const t = setTimeout(async () => {
      try {
        const res = await fetch(`/api/v1/stats/teams?search=${encodeURIComponent(search1)}`)
        if (res.ok) {
          setSug1(await res.json())
        }
      } catch (e) {
        console.error(e)
      }
    }, 250)
    return () => clearTimeout(t)
  }, [search1, t1])

  // Debounced search for Team 2
  useEffect(() => {
    if (!search2.trim() || (t2 && search2 === t2.name)) {
      setSug2([])
      return
    }
    const t = setTimeout(async () => {
      try {
        const res = await fetch(`/api/v1/stats/teams?search=${encodeURIComponent(search2)}`)
        if (res.ok) {
          setSug2(await res.json())
        }
      } catch (e) {
        console.error(e)
      }
    }, 250)
    return () => clearTimeout(t)
  }, [search2, t2])

  // Reload the teams list when a new team is created
  const refreshTeams = async (selectId: number, setSelectId: (id: number) => void, setSearchText: (name: string) => void) => {
    try {
      const res = await fetch("/api/v1/stats/teams")
      if (res.ok) {
        const list = await res.json()
        setTeams(list)
        setSelectId(selectId)
        const found = list.find((t: any) => t.id === selectId)
        if (found) {
          setSearchText(found.name)
        }
      }
    } catch (e) {
      console.error(e)
    }
  }

  // Construct comparison data dynamically from backend rankings
  const data = [
    { name: 'ICC Test Points', [t1?.name || 'Team 1']: t1Rank?.Test?.points || 0, [t2?.name || 'Team 2']: t2Rank?.Test?.points || 0 },
    { name: 'ICC ODI Points', [t1?.name || 'Team 1']: t1Rank?.ODI?.points || 0, [t2?.name || 'Team 2']: t2Rank?.ODI?.points || 0 },
    { name: 'ODI Win Rate %', [t1?.name || 'Team 1']: t1Rank?.win_rate || 0, [t2?.name || 'Team 2']: t2Rank?.win_rate || 0 },
    { name: 'World Cups', [t1?.name || 'Team 1']: t1Rank?.world_cups || 0, [t2?.name || 'Team 2']: t2Rank?.world_cups || 0 },
    { name: 'WTC Finals', [t1?.name || 'Team 1']: t1Rank?.wtc_finals || 0, [t2?.name || 'Team 2']: t2Rank?.wtc_finals || 0 }
  ]

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white font-sans">Team Analytics comparison</h1>
        <p className="text-sm text-zinc-400 mt-1">Cross-compare win rates, points, and milestones for any team globally</p>
      </div>

      {/* Selectors */}
      <div className="glass-panel p-6 rounded-2xl flex flex-col md:flex-row gap-6 justify-between items-center relative z-20">
        
        {/* Team A Autocomplete */}
        <div className="w-full md:w-1/3 relative">
          <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Team A</label>
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
                        const res = await fetch(`/api/v1/stats/teams?search=${encodeURIComponent(top.name)}&ingest=true`);
                        if (res.ok) {
                          const list = await res.json();
                          if (list.length > 0) {
                            await refreshTeams(list[0].id, setTeam1Id, setSearch1);
                          }
                        }
                      } catch (err) {
                        console.error(err);
                      }
                    } else {
                      setTeam1Id(top.id);
                      setSearch1(top.name);
                    }
                    setShowSug1(false);
                  } else if (search1.trim()) {
                    try {
                      const res = await fetch(`/api/v1/stats/teams?search=${encodeURIComponent(search1)}&ingest=true`);
                      if (res.ok) {
                        const list = await res.json();
                        if (list.length > 0) {
                          await refreshTeams(list[0].id, setTeam1Id, setSearch1);
                          setShowSug1(false);
                        }
                      }
                    } catch (err) {
                      console.error(err);
                    }
                  }
                }
              }}
              placeholder="Search e.g. South Africa"
              spellCheck="false"
              className="w-full pl-10 pr-4 py-3 rounded-xl premium-input text-sm text-white"
            />
          </div>

          {showSug1 && (sug1.length > 0 || (search1 && search1 !== t1?.name)) && (
            <div className="absolute top-[76px] left-0 w-full glass-panel border border-zinc-800 rounded-xl overflow-hidden shadow-2xl max-h-56 overflow-y-auto z-30">
              {sug1.map(t => (
                <button
                  key={t.id}
                  onMouseDown={async (e) => {
                    e.preventDefault();
                    if (t.id === 0) {
                      try {
                        const res = await fetch(`/api/v1/stats/teams?search=${encodeURIComponent(t.name)}&ingest=true`);
                        if (res.ok) {
                          const list = await res.json();
                          if (list.length > 0) {
                            await refreshTeams(list[0].id, setTeam1Id, setSearch1);
                          }
                        }
                      } catch (err) {
                        console.error(err);
                      }
                    } else {
                      setTeam1Id(t.id);
                      setSearch1(t.name);
                    }
                    setShowSug1(false);
                  }}
                  className="w-full text-left px-4 py-2.5 hover:bg-zinc-800 text-xs text-white transition-colors border-b border-zinc-800/40"
                >
                  <p className="font-semibold">{t.name}</p>
                  <p className="text-[10px] text-zinc-400 mt-0.5">{t.team_type} League</p>
                </button>
              ))}
              {sug1.length === 0 && search1.trim() && (
                <button
                  onMouseDown={async (e) => {
                    e.preventDefault();
                    try {
                      const res = await fetch(`/api/v1/stats/teams?search=${encodeURIComponent(search1)}&ingest=true`)
                      if (res.ok) {
                        const list = await res.json()
                        if (list.length > 0) {
                          await refreshTeams(list[0].id, setTeam1Id, setSearch1)
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

        <div className="bg-gradient-to-tr from-primary-600 to-pink-500 p-3 rounded-full text-white shadow-lg glow-indigo hidden md:block">
          <ArrowLeftRight className="h-5 w-5" />
        </div>

        {/* Team B Autocomplete */}
        <div className="w-full md:w-1/3 relative">
          <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Team B</label>
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
                        const res = await fetch(`/api/v1/stats/teams?search=${encodeURIComponent(top.name)}&ingest=true`);
                        if (res.ok) {
                          const list = await res.json();
                          if (list.length > 0) {
                            await refreshTeams(list[0].id, setTeam2Id, setSearch2);
                          }
                        }
                      } catch (err) {
                        console.error(err);
                      }
                    } else {
                      setTeam2Id(top.id);
                      setSearch2(top.name);
                    }
                    setShowSug2(false);
                  } else if (search2.trim()) {
                    try {
                      const res = await fetch(`/api/v1/stats/teams?search=${encodeURIComponent(search2)}&ingest=true`);
                      if (res.ok) {
                        const list = await res.json();
                        if (list.length > 0) {
                          await refreshTeams(list[0].id, setTeam2Id, setSearch2);
                          setShowSug2(false);
                        }
                      }
                    } catch (err) {
                      console.error(err);
                    }
                  }
                }
              }}
              placeholder="Search e.g. New Zealand"
              spellCheck="false"
              className="w-full pl-10 pr-4 py-3 rounded-xl premium-input text-sm text-white"
            />
          </div>

          {showSug2 && (sug2.length > 0 || (search2 && search2 !== t2?.name)) && (
            <div className="absolute top-[76px] left-0 w-full glass-panel border border-zinc-800 rounded-xl overflow-hidden shadow-2xl max-h-56 overflow-y-auto z-30">
              {sug2.map(t => (
                <button
                  key={t.id}
                  onMouseDown={async (e) => {
                    e.preventDefault();
                    if (t.id === 0) {
                      try {
                        const res = await fetch(`/api/v1/stats/teams?search=${encodeURIComponent(t.name)}&ingest=true`);
                        if (res.ok) {
                          const list = await res.json();
                          if (list.length > 0) {
                            await refreshTeams(list[0].id, setTeam2Id, setSearch2);
                          }
                        }
                      } catch (err) {
                        console.error(err);
                      }
                    } else {
                      setTeam2Id(t.id);
                      setSearch2(t.name);
                    }
                    setShowSug2(false);
                  }}
                  className="w-full text-left px-4 py-2.5 hover:bg-zinc-800 text-xs text-white transition-colors border-b border-zinc-800/40"
                >
                  <p className="font-semibold">{t.name}</p>
                  <p className="text-[10px] text-zinc-400 mt-0.5">{t.team_type} League</p>
                </button>
              ))}
              {sug2.length === 0 && search2.trim() && (
                <button
                  onMouseDown={async (e) => {
                    e.preventDefault();
                    try {
                      const res = await fetch(`/api/v1/stats/teams?search=${encodeURIComponent(search2)}&ingest=true`)
                      if (res.ok) {
                        const list = await res.json()
                        if (list.length > 0) {
                          await refreshTeams(list[0].id, setTeam2Id, setSearch2)
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
      </div>

      {loading ? (
        <div className="text-center py-12 text-zinc-500">Compiling team statistics...</div>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative z-10">
            
            {/* Team A Details Card */}
            <div className="glass-panel p-6 rounded-2xl border-t-4 border-primary-500 flex justify-between items-center">
              <div>
                <span className="text-[10px] uppercase font-mono tracking-widest text-primary-400">{t1?.team_type} League</span>
                <h3 className="text-2xl font-bold text-white mt-1">{t1?.name}</h3>
                <p className="text-xs text-zinc-400 mt-2 font-mono">Abbreviation: {t1?.short_name}</p>
              </div>
            </div>

            {/* Team B Details Card */}
            <div className="glass-panel p-6 rounded-2xl border-t-4 border-pink-500 flex justify-between items-center">
              <div>
                <span className="text-[10px] uppercase font-mono tracking-widest text-pink-400">{t2?.team_type} League</span>
                <h3 className="text-2xl font-bold text-white mt-1">{t2?.name}</h3>
                <p className="text-xs text-zinc-400 mt-2 font-mono">Abbreviation: {t2?.short_name}</p>
              </div>
            </div>

          </div>

          {/* ICC Rankings Comparison Panel */}
          <div className="glass-panel p-6 rounded-2xl relative z-10">
            <div className="flex items-center space-x-2 mb-6">
              <Trophy className="h-4.5 w-4.5 text-yellow-500" />
              <span className="text-sm font-bold uppercase tracking-wider text-zinc-300">ICC Rankings Head-to-Head</span>
            </div>
            
            {!t1Rank || !t2Rank ? (
              <div className="py-4 text-center text-xs text-zinc-500">Retrieving ranking statistics...</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs text-zinc-300">
                {/* Test */}
                <div className="p-4 bg-zinc-900/60 rounded-xl border border-zinc-800/80">
                  <span className="text-zinc-500 block uppercase font-mono tracking-wider mb-2">Test Format</span>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>{t1?.name}</span>
                      <span className="font-semibold text-primary-400">Rank {t1Rank.Test.rank} ({t1Rank.Test.points} pts)</span>
                    </div>
                    <div className="flex justify-between border-t border-zinc-800/40 pt-2">
                      <span>{t2?.name}</span>
                      <span className="font-semibold text-pink-400">Rank {t2Rank.Test.rank} ({t2Rank.Test.points} pts)</span>
                    </div>
                  </div>
                </div>

                {/* ODI */}
                <div className="p-4 bg-zinc-900/60 rounded-xl border border-zinc-800/80">
                  <span className="text-zinc-500 block uppercase font-mono tracking-wider mb-2">ODI Format</span>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>{t1?.name}</span>
                      <span className="font-semibold text-primary-400">Rank {t1Rank.ODI.rank} ({t1Rank.ODI.points} pts)</span>
                    </div>
                    <div className="flex justify-between border-t border-zinc-800/40 pt-2">
                      <span>{t2?.name}</span>
                      <span className="font-semibold text-pink-400">Rank {t2Rank.ODI.rank} ({t2Rank.ODI.points} pts)</span>
                    </div>
                  </div>
                </div>

                {/* T20 */}
                <div className="p-4 bg-zinc-900/60 rounded-xl border border-zinc-800/80">
                  <span className="text-zinc-500 block uppercase font-mono tracking-wider mb-2">T20 Format</span>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>{t1?.name}</span>
                      <span className="font-semibold text-primary-400">Rank {t1Rank.T20.rank} ({t1Rank.T20.points} pts)</span>
                    </div>
                    <div className="flex justify-between border-t border-zinc-800/40 pt-2">
                      <span>{t2?.name}</span>
                      <span className="font-semibold text-pink-400">Rank {t2Rank.T20.rank} ({t2Rank.T20.points} pts)</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Bar Chart comparing metrics */}
          <div className="glass-panel p-6 rounded-2xl">
            <div className="flex items-center space-x-2 mb-6">
              <Activity className="h-4.5 w-4.5 text-indigo-400" />
              <span className="text-sm font-bold uppercase tracking-wider text-zinc-300">Milestone Comparison Bar Chart</span>
            </div>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis dataKey="name" stroke="#71717a" fontSize={11} />
                  <YAxis stroke="#71717a" fontSize={11} />
                  <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a' }} />
                  <Legend />
                  <Bar dataKey={t1?.name || 'Team 1'} fill="#4f73ff" radius={[4, 4, 0, 0]} />
                  <Bar dataKey={t2?.name || 'Team 2'} fill="#db2777" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}
