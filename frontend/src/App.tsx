import React, { createContext, useContext, useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Link, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { 
  Trophy, 
  MessageSquare, 
  User as UserIcon, 
  Settings as SettingsIcon, 
  ChevronRight, 
  Search, 
  Mic, 
  Send, 
  ArrowLeft, 
  Users, 
  Compass, 
  FileText, 
  CloudSun, 
  Sparkles, 
  TrendingUp, 
  LayoutDashboard,
  Clock, 
  Volume2, 
  LogOut,
  Moon,
  Sun,
  ArrowLeftRight
} from 'lucide-react'

// Create Auth Context
interface AuthContextType {
  isAuthenticated: boolean;
  user: any;
  login: (email: string, pass: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
};

// Pages
import Landing from './pages/Landing'
import Auth from './pages/Auth'
import Dashboard from './pages/Dashboard'
import Chat from './pages/Chat'
import ComparePlayers from './pages/ComparePlayers'
import CompareTeams from './pages/CompareTeams'
import CompareMatchups from './pages/CompareMatchups'
import MatchCenter from './pages/MatchCenter'

function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return localStorage.getItem("is_auth") === "true";
  });
  const [user, setUser] = useState<any>(() => {
    const saved = localStorage.getItem("user_profile");
    return saved ? JSON.parse(saved) : null;
  });

  const login = async (email: string, pass: string): Promise<boolean> => {
    try {
      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password: pass })
      });
      if (res.ok) {
        setIsAuthenticated(true);
        const profile = { 
          email, 
          name: email === "demo@cricketgpt.com" ? "Demo Professional" : "Premium Analyst", 
          role: email === "demo@cricketgpt.com" ? "Cricket Analyst" : "Cricket Fan" 
        };
        setUser(profile);
        localStorage.setItem("is_auth", "true");
        localStorage.setItem("user_profile", JSON.stringify(profile));
        return true;
      }
    } catch (e) {
      console.error(e);
    }
    return false;
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUser(null);
    localStorage.removeItem("is_auth");
    localStorage.removeItem("user_profile");
  };

  useEffect(() => {
    const verifyAuth = async () => {
      if (isAuthenticated) {
        try {
          const res = await fetch("/api/v1/auth/me")
          if (!res.ok) {
            logout();
          }
        } catch (e) {
          console.error("Auth check failed", e);
        }
      }
    }
    verifyAuth();
  }, [isAuthenticated]);

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// Protected Route Guard
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/auth" />;
}

// Sidebar Layout for SaaS Interface
function MainLayout() {
  const { logout, user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [isDark, setIsDark] = useState(true);

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.classList.toggle("dark");
  };

  const navItems = [
    { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { path: "/chat", label: "AI Assistant", icon: MessageSquare },
    { path: "/compare-players", label: "Player Analytics", icon: UserIcon },
    { path: "/compare-teams", label: "Team Analytics", icon: Users },
    { path: "/compare-matchups", label: "Matchup Analytics", icon: ArrowLeftRight },
  ];

  return (
    <div className="flex h-screen bg-zinc-950 text-slate-100 overflow-hidden font-sans dot-bg">
      {/* Sidebar - Perplexity / Linear aesthetic */}
      <aside className="w-64 border-r border-zinc-800/80 bg-zinc-900/50 backdrop-blur-md flex flex-col justify-between p-4 z-20">
        <div>
          {/* Logo */}
          <div className="flex items-center space-x-2 px-2 py-3 mb-6">
            <div className="bg-gradient-to-tr from-primary-600 to-pink-500 p-2 rounded-xl text-white shadow-lg glow-indigo">
              <Trophy className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold font-sans tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                CricketGPT
              </h1>
              <span className="text-[10px] text-zinc-500 font-mono tracking-widest uppercase">PRO EDITION</span>
            </div>
          </div>

          {/* Nav List */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${
                    isActive 
                      ? "bg-zinc-800/75 text-white border-l-2 border-primary-500 font-medium" 
                      : "text-zinc-400 hover:text-white hover:bg-zinc-800/40"
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <Icon className={`h-4.5 w-4.5 ${isActive ? "text-primary-400" : ""}`} />
                    <span>{item.label}</span>
                  </div>
                  {isActive && <ChevronRight className="h-3 w-3 text-zinc-500" />}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Footer Profile & Settings */}
        <div className="space-y-3 border-t border-zinc-800/80 pt-4 px-2">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-full bg-gradient-to-tr from-primary-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold">
              {user?.name?.slice(0, 2).toUpperCase() || "US"}
            </div>
            <div className="flex-1 overflow-hidden">
              <h4 className="text-xs font-semibold text-white truncate">{user?.name || "Premium User"}</h4>
              <p className="text-[10px] text-zinc-400 truncate">{user?.email || "analyst@cricketgpt.com"}</p>
            </div>
          </div>

          <div className="flex items-center justify-between text-zinc-400 text-xs pt-1">
            <button 
              onClick={toggleTheme}
              className="p-1.5 hover:bg-zinc-800 rounded-lg transition-colors hover:text-white"
              title="Toggle theme"
            >
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
            
            <button 
              onClick={() => { logout(); navigate("/"); }}
              className="flex items-center space-x-1.5 p-1.5 hover:bg-red-950/20 hover:text-red-400 rounded-lg transition-colors"
            >
              <LogOut className="h-4 w-4" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Container */}
      <main className="flex-1 overflow-y-auto relative z-10">
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/match-center" element={<MatchCenter />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/compare-players" element={<ComparePlayers />} />
          <Route path="/compare-teams" element={<CompareTeams />} />
          <Route path="/compare-matchups" element={<CompareMatchups />} />
          <Route path="*" element={<Navigate to="/dashboard" />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/auth" element={<Auth />} />
          <Route path="/*" element={<ProtectedRoute><MainLayout /></ProtectedRoute>} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
