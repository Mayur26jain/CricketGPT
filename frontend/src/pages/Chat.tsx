import React, { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { 
  Send, 
  Mic, 
  MicOff, 
  Bot, 
  User as UserIcon, 
  BookMarked,
  Sparkles, 
  Loader2, 
  BarChart2, 
  Compass, 
  TrendingUp, 
  FileText,
  AlertCircle
} from 'lucide-react'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, PieChart, Pie, Cell } from 'recharts'

interface Message {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  isStreaming?: boolean;
  visualization_data?: any;
  trace?: string;
}

export default function Chat() {
  const [searchParams] = useSearchParams()
  const [conversations, setConversations] = useState<any[]>([])
  const [activeConvId, setActiveConvId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isRecording, setIsRecording] = useState(false)
  const [statusText, setStatusText] = useState("")
  const [traceText, setTraceText] = useState("")
  const [loading, setLoading] = useState(false)
  
  const chatEndRef = useRef<HTMLDivElement>(null)
  const socketRef = useRef<WebSocket | null>(null)
  const recognitionRef = useRef<any>(null)

  // Suggestion chips
  const suggestions = [
    { text: "Compare Virat Kohli and Joe Root.", label: "Comparison" },
    { text: "Who has the highest batting average in Tests?", label: "Stats" },
    { text: "Explain LBW with examples.", label: "Rules" },
    { text: "Predict today's match winner.", label: "Prediction" }
  ]

  // Fetch initial conversations list and process URL query search params
  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const res = await fetch("/api/v1/chat/conversations")
        if (res.ok) {
          const list = await res.json()
          setConversations(list)
          
          let convId = null
          if (list.length > 0) {
            convId = list[0].id
            setActiveConvId(convId)
            await loadMessages(convId)
          } else {
            // Create a default first conversation
            const defaultConv = await createFirstConversation()
            if (defaultConv) {
              convId = defaultConv.id
            }
          }
          
          // Trigger search query parameter immediately if present
          const q = searchParams.get("q")
          if (q && convId) {
            startWebSocketStream(q, convId)
          }
        }
      } catch (e) {
        console.error("Failed to load conversations", e)
      }
    }
    fetchConversations()
  }, [searchParams])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, statusText, traceText])

  const createFirstConversation = async () => {
    try {
      const res = await fetch("/api/v1/chat/conversations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "🏏 New Analysis" })
      })
      if (res.ok) {
        const conv = await res.json()
        setConversations([conv])
        setActiveConvId(conv.id)
        loadMessages(conv.id)
        return conv
      }
    } catch (e) {
      console.error(e)
    }
    return null
  }

  const loadMessages = async (convId: string) => {
    try {
      const res = await fetch(`/api/v1/chat/conversations/${convId}/messages`)
      if (res.ok) {
        const msgs = await res.json()
        setMessages(msgs)
      }
    } catch (e) {
      console.error(e)
    }
  }

  // Handle Websocket Streaming
  const startWebSocketStream = (queryStr: string, convIdOverride?: string) => {
    const targetConvId = convIdOverride || activeConvId;
    if (!targetConvId) return;

    if (socketRef.current) {
      socketRef.current.close()
    }

    // Set layout/loading state
    setLoading(true)
    setTraceText("")
    setStatusText("Initializing Connection...")
    
    // Add user message locally
    const userMsg: Message = { role: 'user', content: queryStr };
    setMessages(prev => [...prev, userMsg])
    
    // Build robust ws target host mapping
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host.includes('3000') ? window.location.host.replace('3000', '8001') : window.location.host;
    const wsUrl = `${wsProtocol}//${wsHost}/api/v1/chat/ws/${targetConvId}`;
    
    const socket = new WebSocket(wsUrl)
    socketRef.current = socket

    let streamingMessageAdded = false;

    socket.onopen = () => {
      setStatusText("Connected. Parsing query...")
      socket.send(jsonPayload({ query: queryStr }))
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === "status") {
        setStatusText(data.content)
      } 
      else if (data.type === "trace") {
        setTraceText(data.content)
      }
      else if (data.type === "stream_start") {
        setStatusText("")
        setLoading(false)
        if (!streamingMessageAdded) {
          setMessages(prev => [...prev, { role: 'assistant', content: "", isStreaming: true }]);
          streamingMessageAdded = true;
        }
      }
      else if (data.type === "chunk") {
        setMessages(prev => {
          const list = [...prev];
          const last = list[list.length - 1];
          if (last && last.role === 'assistant' && last.isStreaming) {
            last.content += data.content;
          }
          return list;
        });
      }
      else if (data.type === "completed") {
        setMessages(prev => {
          const list = [...prev];
          const last = list[list.length - 1];
          if (last && last.role === 'assistant') {
            last.id = data.message_id;
            last.isStreaming = false;
            last.visualization_data = data.visualization_data;
          }
          return list;
        });
        // Reset trace & stats
        setStatusText("")
        setTraceText("")
        setLoading(false)
        socket.close()
      }
    };

    socket.onerror = (err) => {
      console.error(err)
      setErrorState("WebSocket connection error. Checking server status.")
    };

    socket.onclose = () => {
      setLoading(false)
    };
  };

  const setErrorState = (txt: string) => {
    setStatusText("")
    setTraceText("")
    setLoading(false)
    setMessages(prev => [...prev, { role: 'system', content: txt }])
  }

  const jsonPayload = (obj: any) => {
    return JSON.stringify(obj);
  };

  const handleSend = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim()) return;
    const query = input;
    setInput("");
    startWebSocketStream(query);
  };

  // Voice Search / Web Speech API Integration
  const toggleRecording = () => {
    if (isRecording) {
      recognitionRef.current?.stop();
      setIsRecording(false);
    } else {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (!SpeechRecognition) {
        alert("Speech Recognition API is not supported in this browser. Try Google Chrome.");
        return;
      }
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';
      
      recognition.onstart = () => {
        setIsRecording(true);
      };
      
      recognition.onresult = (event: any) => {
        const text = event.results[0][0].transcript;
        setInput(text);
      };
      
      recognition.onerror = (e: any) => {
        console.error(e);
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    }
  };

  // Bookmark a message
  const handleBookmark = async (msg: Message) => {
    if (!msg.id) return;
    try {
      const res = await fetch("/api/v1/chat/bookmarks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message_id: msg.id, title: msg.content.slice(0, 30) })
      })
      if (res.ok) {
        alert("Response bookmarked successfully!")
      }
    } catch (e) {
      console.error(e)
    }
  }

  // Chart Rendering Switch
  const renderChart = (schema: any) => {
    if (!schema || !schema.data) return null;
    
    return (
      <div className="mt-6 p-5 glass-panel rounded-2xl border border-zinc-800/80 w-full max-w-lg">
        <div className="flex items-center justify-between mb-4 border-b border-zinc-800 pb-2">
          <span className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
            <BarChart2 className="h-4 w-4 text-primary-400" />
            AI Visual Chart
          </span>
          <span className="text-[10px] text-zinc-500 font-mono">Recharts Engine</span>
        </div>
        
        <div className="h-56 w-full">
          {schema.type === "bar" && (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={schema.data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey={schema.xKey} stroke="#71717a" fontSize={10} />
                <YAxis stroke="#71717a" fontSize={10} />
                <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a' }} />
                <Bar dataKey={schema.yKey} fill="#4f73ff" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}

          {schema.type === "radar" && (
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="75%" data={schema.data}>
                <PolarGrid stroke="#27272a" />
                <PolarAngleAxis dataKey={schema.indexBy} stroke="#71717a" fontSize={9} />
                <PolarRadiusAxis domain={[0, 100]} tick={false} stroke="#27272a" />
                {schema.keys.map((key: string, idx: number) => (
                  <Radar
                    key={key}
                    name={key}
                    dataKey={key}
                    stroke={idx === 0 ? "#4f73ff" : "#db2777"}
                    fill={idx === 0 ? "#4f73ff" : "#db2777"}
                    fillOpacity={0.2}
                  />
                ))}
                <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a' }} />
              </RadarChart>
            </ResponsiveContainer>
          )}

          {schema.type === "pie" && (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={schema.data}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {schema.data.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={entry.color || (index === 0 ? "#4f73ff" : "#db2777")} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a' }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-screen bg-zinc-950/40 relative">
      
      {/* Messages Window */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
        
        {messages.length === 0 ? (
          /* Suggestion screen when no messages */
          <div className="h-full flex flex-col justify-center items-center max-w-2xl mx-auto text-center space-y-8 animate-fade-in">
            <div className="bg-gradient-to-tr from-primary-600 to-pink-500 p-4 rounded-3xl text-white shadow-xl glow-indigo">
              <Bot className="h-10 w-10" />
            </div>
            
            <div>
              <h2 className="text-3xl font-extrabold tracking-tight text-white font-sans">CricketGPT Assistant</h2>
              <p className="text-zinc-400 mt-2 max-w-md font-light leading-normal">
                Ask about scores, comparisons, rules, or forecasts. Supported by SQL Agents and RAG.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full pt-4">
              {suggestions.map((sug, idx) => (
                <button
                  key={idx}
                  onClick={() => { setInput(sug.text); startWebSocketStream(sug.text); }}
                  className="glass-card p-4 rounded-xl text-left border border-zinc-800/80 hover:border-zinc-700/80 flex flex-col justify-between"
                >
                  <span className="text-xs text-primary-400 font-semibold uppercase tracking-wider mb-1.5">{sug.label}</span>
                  <p className="text-sm font-medium text-white leading-snug">{sug.text}</p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Normal chat conversation messages list */
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((msg, idx) => (
              <div 
                key={idx} 
                className={`flex gap-4 animate-fade-in ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role !== 'user' && (
                  <div className="h-9 w-9 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-primary-400">
                    <Bot className="h-5 w-5" />
                  </div>
                )}
                
                <div className={`max-w-[85%] rounded-2xl p-5 ${
                  msg.role === 'user' 
                     ? 'bg-primary-600 text-white shadow-lg glow-indigo rounded-tr-none' 
                    : 'glass-panel text-slate-100 rounded-tl-none border border-zinc-800/50'
                }`}>
                  <div className="whitespace-pre-wrap leading-relaxed text-sm">
                    {msg.content}
                  </div>
                  
                  {/* Render visualization chart if schema present */}
                  {msg.visualization_data && renderChart(msg.visualization_data)}

                  {/* Bookmark Button */}
                  {msg.role === 'assistant' && !msg.isStreaming && msg.id && (
                    <button 
                      onClick={() => handleBookmark(msg)}
                      className="mt-3 flex items-center gap-1 text-[10px] text-zinc-500 hover:text-zinc-300 font-mono tracking-wider transition-colors"
                    >
                      <BookMarked className="h-3.5 w-3.5" />
                      <span>BOOKMARK REPORT</span>
                    </button>
                  )}
                </div>

                {msg.role === 'user' && (
                  <div className="h-9 w-9 rounded-full bg-primary-500/10 border border-primary-500/20 flex items-center justify-center text-primary-400">
                    <UserIcon className="h-5 w-5" />
                  </div>
                )}
              </div>
            ))}

            {/* Displaying AI Traces / Running Sub-agents steps */}
            {loading && (
              <div className="flex gap-4 animate-fade-in">
                <div className="h-9 w-9 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-primary-400">
                  <Bot className="h-5 w-5 animate-spin" />
                </div>
                
                <div className="glass-panel p-5 rounded-2xl border border-zinc-800/50 flex flex-col gap-3 min-w-[280px]">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4.5 w-4.5 text-primary-400 animate-spin" />
                    <span className="text-xs text-zinc-400 font-semibold">{statusText}</span>
                  </div>
                  {traceText && (
                    <div className="p-3 bg-zinc-950 rounded-xl border border-zinc-800/60 font-mono text-[10px] text-zinc-500 leading-normal">
                      {traceText}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input Form Box */}
      <div className="border-t border-zinc-900 bg-zinc-950/80 backdrop-blur-md p-4">
        <form onSubmit={handleSend} className="max-w-3xl mx-auto flex items-center gap-3 relative">
          
          <button
            type="button"
            onClick={toggleRecording}
            className={`p-3 rounded-xl border transition-all duration-200 ${
              isRecording 
                ? 'bg-pink-600 border-pink-500 text-white animate-pulse' 
                : 'bg-zinc-900/60 border-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-800'
            }`}
            title="Search with Voice"
          >
            {isRecording ? <MicOff className="h-4.5 w-4.5" /> : <Mic className="h-4.5 w-4.5" />}
          </button>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Compare players, explore live scores, query test statistics..."
            className="flex-1 py-3.5 px-4 rounded-xl border border-zinc-800 bg-zinc-900/40 text-white text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500/20 focus:outline-none"
            disabled={loading}
          />

          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="p-3.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-white disabled:bg-zinc-800 disabled:text-zinc-600 shadow-lg glow-indigo transition-all duration-200"
          >
            <Send className="h-4.5 w-4.5" />
          </button>
        </form>
      </div>

    </div>
  )
}
