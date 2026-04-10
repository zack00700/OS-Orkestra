import { useState, useEffect, useCallback } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area } from "recharts";
import { Search, Bell, Settings, Users, Mail, BarChart3, Zap, Globe, ChevronDown, ArrowUpRight, ArrowDownRight, Activity, Send, Eye, MousePointerClick, AlertTriangle, CheckCircle, RefreshCw, Filter, Plus, LayoutDashboard, Target, Database, Link2, LogOut, Lock, ChevronLeft, ChevronRight } from "lucide-react";

const API = "http://localhost:8000/api/v1";

// ══════════════════════════════════════════════════════════
// API HELPER
// ══════════════════════════════════════════════════════════

async function api(endpoint, options = {}) {
  const token = localStorage.getItem("orkestra_token");
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API}${endpoint}`, { ...options, headers });
  if (res.status === 401) {
    localStorage.removeItem("orkestra_token");
    window.location.reload();
    return null;
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Erreur ${res.status}`);
  }
  return res.json();
}

// ══════════════════════════════════════════════════════════
// LOGIN PAGE
// ══════════════════════════════════════════════════════════

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState("admin@opensid.com");
  const [password, setPassword] = useState("Test1234");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      }).then((r) => r.json());

      if (data.access_token) {
        localStorage.setItem("orkestra_token", data.access_token);
        onLogin(data);
      } else {
        setError(data.detail || "Identifiants incorrects");
      }
    } catch (err) {
      setError("Impossible de se connecter au serveur");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "linear-gradient(135deg, #0a0f1a 0%, #121d33 50%, #0d1524 100%)", fontFamily: "'Outfit', system-ui, sans-serif" }}>
      <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-sky-400 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
              <span className="text-white font-bold text-lg">OS</span>
            </div>
            <div className="text-left">
              <div className="text-white font-bold text-2xl tracking-tight">Orkestra</div>
              <div className="text-sky-400/60 text-xs uppercase tracking-[0.25em]">by OpenSID</div>
            </div>
          </div>
        </div>
        <div className="bg-white/[0.04] backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
          <h2 className="text-white text-lg font-semibold mb-6">Connexion</h2>
          {error && <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 mb-4 text-red-400 text-sm">{error}</div>}
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="text-white/50 text-xs font-medium uppercase tracking-wider mb-2 block">Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/20 focus:outline-none focus:border-sky-400/50 focus:ring-1 focus:ring-sky-400/25 transition-all" />
            </div>
            <div className="mb-6">
              <label className="text-white/50 text-xs font-medium uppercase tracking-wider mb-2 block">Mot de passe</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-white/20 focus:outline-none focus:border-sky-400/50 focus:ring-1 focus:ring-sky-400/25 transition-all" />
            </div>
            <button type="submit" disabled={loading} className="w-full bg-gradient-to-r from-sky-500 to-blue-600 text-white font-medium py-3 rounded-xl hover:from-sky-400 hover:to-blue-500 transition-all disabled:opacity-50 shadow-lg shadow-blue-500/25">
              {loading ? "Connexion..." : "Se connecter"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// COMPONENTS
// ══════════════════════════════════════════════════════════

const StatusBadge = ({ status }) => {
  const styles = {
    RUNNING: "bg-emerald-50 text-emerald-700 border-emerald-200",
    COMPLETED: "bg-slate-100 text-slate-600 border-slate-200",
    SCHEDULED: "bg-amber-50 text-amber-700 border-amber-200",
    DRAFT: "bg-gray-50 text-gray-500 border-gray-200",
    PAUSED: "bg-red-50 text-red-600 border-red-200",
    running: "bg-emerald-50 text-emerald-700 border-emerald-200",
    completed: "bg-slate-100 text-slate-600 border-slate-200",
    scheduled: "bg-amber-50 text-amber-700 border-amber-200",
    draft: "bg-gray-50 text-gray-500 border-gray-200",
  };
  const labels = { RUNNING: "En cours", COMPLETED: "Terminée", SCHEDULED: "Planifiée", DRAFT: "Brouillon", PAUSED: "En pause", running: "En cours", completed: "Terminée", scheduled: "Planifiée", draft: "Brouillon" };
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[status] || "bg-gray-50 text-gray-500 border-gray-200"}`}>
      {labels[status] || status}
    </span>
  );
};

const ChannelIcon = ({ channel }) => {
  if (channel === "whatsapp" || channel === "WHATSAPP") return <span className="text-green-500 text-xs font-bold bg-green-50 px-2 py-0.5 rounded-full">WA</span>;
  if (channel === "sms" || channel === "SMS") return <span className="text-amber-500 text-xs font-bold bg-amber-50 px-2 py-0.5 rounded-full">SMS</span>;
  return <Mail size={14} className="text-slate-400" />;
};

const MetricCard = ({ icon: Icon, label, value, change, changeType, subtitle, loading }) => (
  <div className="bg-white rounded-2xl p-5 border border-slate-100 hover:border-slate-200 transition-all hover:shadow-sm">
    <div className="flex items-start justify-between mb-3">
      <div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center">
        <Icon size={18} className="text-white" />
      </div>
      {change && (
        <div className={`flex items-center gap-0.5 text-xs font-medium ${changeType === "up" ? "text-emerald-600" : "text-red-500"}`}>
          {changeType === "up" ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
          {change}
        </div>
      )}
    </div>
    <div className="text-2xl font-bold text-slate-900 tracking-tight">
      {loading ? <div className="h-8 w-24 bg-slate-100 rounded-lg animate-pulse" /> : value}
    </div>
    <div className="text-sm text-slate-500 mt-0.5">{label}</div>
    {subtitle && <div className="text-xs text-slate-400 mt-1">{subtitle}</div>}
  </div>
);

// ══════════════════════════════════════════════════════════
// DASHBOARD PAGE
// ══════════════════════════════════════════════════════════

function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [contactStats, campData] = await Promise.all([
          api("/contacts/stats"),
          api("/campaigns/?page=1&page_size=10&sort_order=desc"),
        ]);
        setStats(contactStats);
        setCampaigns(campData?.items || []);
      } catch (err) {
        console.error("Dashboard load error:", err);
      }
      setLoading(false);
    }
    load();
  }, []);

  // Compute campaign metrics
  const totalSent = campaigns.reduce((s, c) => s + (c.total_sent || 0), 0);
  const totalOpened = campaigns.reduce((s, c) => s + (c.total_opened || 0), 0);
  const totalClicked = campaigns.reduce((s, c) => s + (c.total_clicked || 0), 0);
  const totalDelivered = campaigns.reduce((s, c) => s + (c.total_delivered || 0), 0);
  const avgOpenRate = totalDelivered > 0 ? ((totalOpened / totalDelivered) * 100).toFixed(1) : "0";
  const avgClickRate = totalDelivered > 0 ? ((totalClicked / totalDelivered) * 100).toFixed(1) : "0";
  const activeCampaigns = campaigns.filter((c) => c.status === "RUNNING" || c.status === "running").length;

  // Funnel data from stats
  const funnelData = stats
    ? Object.entries(stats.by_stage || {}).map(([stage, count]) => ({
        name: stage.replace("LeadStage.", ""),
        value: count,
        fill: { AWARENESS: "#0f172a", INTEREST: "#1e3a5f", CONSIDERATION: "#2563eb", PURCHASE: "#3b82f6", RETENTION: "#60a5fa" }[stage.replace("LeadStage.", "")] || "#94a3b8",
      }))
    : [];

  // Source data for pie
  const sourceData = stats
    ? Object.entries(stats.by_source || {}).map(([source, count]) => ({
        name: source.replace("ContactSource.", ""),
        value: count,
      }))
    : [];
  const SOURCE_COLORS = ["#0f172a", "#1e3a5f", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd"];

  // Campaign chart data
  const campChartData = [...campaigns].reverse().filter(c => c.total_sent > 0).slice(0, 8).map((c) => ({
    name: c.name.length > 18 ? c.name.slice(0, 18) + "…" : c.name,
    envoyés: c.total_sent,
    ouverts: c.total_opened,
    cliqués: c.total_clicked,
  }));

  return (
    <div className="p-8">
      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <MetricCard icon={Users} label="Contacts totaux" value={stats ? stats.total.toLocaleString("fr-FR") : "—"} loading={loading} subtitle={stats ? `${stats.active} actifs · ${stats.internal} internes` : ""} />
        <MetricCard icon={Send} label="Emails envoyés" value={totalSent.toLocaleString("fr-FR")} loading={loading} subtitle={`${activeCampaigns} campagnes actives`} />
        <MetricCard icon={Eye} label="Taux d'ouverture moy." value={`${avgOpenRate}%`} loading={loading} subtitle="Sur toutes les campagnes" />
        <MetricCard icon={MousePointerClick} label="Taux de clic moy." value={`${avgClickRate}%`} loading={loading} subtitle="Sur toutes les campagnes" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {/* Performance campagnes */}
        <div className="col-span-2 bg-white rounded-2xl border border-slate-100 p-6">
          <h3 className="text-base font-bold text-slate-900 mb-1">Performance des campagnes</h3>
          <p className="text-xs text-slate-400 mb-4">Données réelles depuis l'API</p>
          {campChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={campChartData}>
                <defs>
                  <linearGradient id="gSent" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#0f172a" stopOpacity={0.08} /><stop offset="95%" stopColor="#0f172a" stopOpacity={0} /></linearGradient>
                  <linearGradient id="gOpen" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#3b82f6" stopOpacity={0.12} /><stop offset="95%" stopColor="#3b82f6" stopOpacity={0} /></linearGradient>
                  <linearGradient id="gClick" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#22c55e" stopOpacity={0.12} /><stop offset="95%" stopColor="#22c55e" stopOpacity={0} /></linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 12 }} />
                <Area type="monotone" dataKey="envoyés" stroke="#0f172a" strokeWidth={2} fill="url(#gSent)" />
                <Area type="monotone" dataKey="ouverts" stroke="#3b82f6" strokeWidth={2} fill="url(#gOpen)" />
                <Area type="monotone" dataKey="cliqués" stroke="#22c55e" strokeWidth={2} fill="url(#gClick)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-slate-400">Chargement...</div>
          )}
        </div>

        {/* Sources pie */}
        <div className="bg-white rounded-2xl border border-slate-100 p-6">
          <h3 className="text-base font-bold text-slate-900 mb-1">Sources des contacts</h3>
          <p className="text-xs text-slate-400 mb-4">Répartition par origine</p>
          {sourceData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie data={sourceData} dataKey="value" cx="50%" cy="50%" innerRadius={50} outerRadius={75} paddingAngle={3} strokeWidth={0}>
                    {sourceData.map((_, i) => <Cell key={i} fill={SOURCE_COLORS[i % SOURCE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: 12, fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 mt-2">
                {sourceData.map((item, i) => (
                  <div key={item.name} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: SOURCE_COLORS[i % SOURCE_COLORS.length] }} />
                      <span className="text-slate-600 text-xs">{item.name}</span>
                    </div>
                    <span className="font-semibold text-slate-800 text-xs">{item.value}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="h-48 flex items-center justify-center text-slate-400">Chargement...</div>
          )}
        </div>
      </div>

      {/* Funnel + Campaigns Table */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {/* Lead Funnel */}
        <div className="bg-white rounded-2xl border border-slate-100 p-6">
          <h3 className="text-base font-bold text-slate-900 mb-1">Funnel de conversion</h3>
          <p className="text-xs text-slate-400 mb-5">Parcours client réel</p>
          <div className="space-y-3">
            {funnelData.sort((a, b) => b.value - a.value).map((stage) => {
              const maxVal = Math.max(...funnelData.map((s) => s.value), 1);
              const pct = (stage.value / maxVal) * 100;
              return (
                <div key={stage.name} className="flex items-center gap-3">
                  <div className="w-24 text-xs text-slate-600 font-medium truncate">{stage.name}</div>
                  <div className="flex-1 bg-slate-50 rounded-full h-7 overflow-hidden">
                    <div className="h-full rounded-full flex items-center justify-end px-3 transition-all" style={{ width: `${Math.max(pct, 12)}%`, backgroundColor: stage.fill }}>
                      <span className="text-[10px] font-bold text-white">{stage.value}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Campaigns Table */}
        <div className="col-span-2 bg-white rounded-2xl border border-slate-100 p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-base font-bold text-slate-900">Campagnes</h3>
              <p className="text-xs text-slate-400 mt-0.5">Données réelles depuis SQL Server</p>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left text-xs font-medium text-slate-400 pb-3 uppercase tracking-wider">Campagne</th>
                  <th className="text-left text-xs font-medium text-slate-400 pb-3 uppercase tracking-wider">Canal</th>
                  <th className="text-left text-xs font-medium text-slate-400 pb-3 uppercase tracking-wider">Statut</th>
                  <th className="text-right text-xs font-medium text-slate-400 pb-3 uppercase tracking-wider">Envoyés</th>
                  <th className="text-right text-xs font-medium text-slate-400 pb-3 uppercase tracking-wider">Ouv. %</th>
                  <th className="text-right text-xs font-medium text-slate-400 pb-3 uppercase tracking-wider">Clic %</th>
                </tr>
              </thead>
              <tbody>
                {campaigns.map((c) => {
                  const openRate = c.total_delivered > 0 ? ((c.total_opened / c.total_delivered) * 100).toFixed(1) : "—";
                  const clickRate = c.total_delivered > 0 ? ((c.total_clicked / c.total_delivered) * 100).toFixed(1) : "—";
                  return (
                    <tr key={c.id} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/50 transition-colors">
                      <td className="py-3">
                        <div className="flex items-center gap-2.5">
                          <div className={`w-1.5 h-7 rounded-full ${c.campaign_type === "internal" || c.campaign_type === "INTERNAL" ? "bg-sky-400" : "bg-slate-800"}`} />
                          <div>
                            <div className="text-sm font-medium text-slate-800 truncate max-w-[200px]">{c.name}</div>
                            <div className="text-xs text-slate-400">{c.campaign_type === "internal" || c.campaign_type === "INTERNAL" ? "Interne" : "Externe"}</div>
                          </div>
                        </div>
                      </td>
                      <td className="py-3"><ChannelIcon channel={c.channel} /></td>
                      <td className="py-3"><StatusBadge status={c.status} /></td>
                      <td className="py-3 text-right text-sm font-mono text-slate-700">{c.total_sent > 0 ? c.total_sent.toLocaleString("fr-FR") : "—"}</td>
                      <td className="py-3 text-right text-sm font-mono text-slate-700">{openRate !== "—" ? `${openRate}%` : "—"}</td>
                      <td className="py-3 text-right text-sm font-mono text-slate-700">{clickRate !== "—" ? `${clickRate}%` : "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// CONTACTS PAGE
// ══════════════════════════════════════════════════════════

function ContactsPage() {
  const [contacts, setContacts] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const loadContacts = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, page_size: 20, sort_order: "desc" });
      if (search) params.set("search", search);
      const data = await api(`/contacts/?${params}`);
      setContacts(data?.items || []);
      setTotal(data?.total || 0);
      setTotalPages(data?.total_pages || 1);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  }, [page, search]);

  useEffect(() => { loadContacts(); }, [loadContacts]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    loadContacts();
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Contacts</h2>
          <p className="text-sm text-slate-400">{total.toLocaleString("fr-FR")} contacts au total</p>
        </div>
        <form onSubmit={handleSearch} className="flex gap-2">
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Rechercher..." className="px-4 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-sky-400 w-64" />
          <button type="submit" className="px-4 py-2 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800">
            <Search size={16} />
          </button>
        </form>
      </div>

      <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/50">
              <th className="text-left text-xs font-medium text-slate-400 p-4 uppercase tracking-wider">Contact</th>
              <th className="text-left text-xs font-medium text-slate-400 p-4 uppercase tracking-wider">Entreprise</th>
              <th className="text-left text-xs font-medium text-slate-400 p-4 uppercase tracking-wider">Pays</th>
              <th className="text-left text-xs font-medium text-slate-400 p-4 uppercase tracking-wider">Source</th>
              <th className="text-left text-xs font-medium text-slate-400 p-4 uppercase tracking-wider">Étape</th>
              <th className="text-right text-xs font-medium text-slate-400 p-4 uppercase tracking-wider">Score</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i} className="border-b border-slate-50">
                  <td colSpan={6} className="p-4"><div className="h-5 bg-slate-100 rounded animate-pulse" /></td>
                </tr>
              ))
            ) : (
              contacts.map((c) => (
                <tr key={c.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-xs font-bold text-slate-600">
                        {(c.first_name || "?")[0]}{(c.last_name || "?")[0]}
                      </div>
                      <div>
                        <div className="text-sm font-medium text-slate-800">{c.first_name} {c.last_name}</div>
                        <div className="text-xs text-slate-400">{c.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="p-4 text-sm text-slate-600">{c.company || "—"}</td>
                  <td className="p-4 text-sm text-slate-600">{c.country || "—"}</td>
                  <td className="p-4"><span className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded-full">{(c.source || "").replace("ContactSource.", "").replace("_", " ")}</span></td>
                  <td className="p-4"><span className="text-xs font-medium text-sky-600">{(c.lead_stage || "").replace("LeadStage.", "")}</span></td>
                  <td className="p-4 text-right">
                    <span className={`text-sm font-bold ${c.lead_score >= 80 ? "text-emerald-600" : c.lead_score >= 50 ? "text-amber-600" : "text-slate-500"}`}>{c.lead_score}</span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
        <div className="flex items-center justify-between p-4 border-t border-slate-100">
          <span className="text-sm text-slate-400">Page {page} sur {totalPages}</span>
          <div className="flex gap-2">
            <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page <= 1} className="p-2 border border-slate-200 rounded-lg disabled:opacity-30 hover:bg-slate-50">
              <ChevronLeft size={16} />
            </button>
            <button onClick={() => setPage(Math.min(totalPages, page + 1))} disabled={page >= totalPages} className="p-2 border border-slate-200 rounded-lg disabled:opacity-30 hover:bg-slate-50">
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// MAIN APP
// ══════════════════════════════════════════════════════════

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem("orkestra_token"));
  const [activeNav, setActiveNav] = useState("dashboard");

  const handleLogout = () => {
    localStorage.removeItem("orkestra_token");
    setIsLoggedIn(false);
  };

  if (!isLoggedIn) {
    return <LoginPage onLogin={() => setIsLoggedIn(true)} />;
  }

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "contacts", label: "Contacts", icon: Users },
    { id: "campaigns", label: "Campagnes", icon: Send },
    { id: "segments", label: "Segments", icon: Target },
    { id: "analytics", label: "Analytics", icon: BarChart3 },
    { id: "integrations", label: "Intégrations", icon: Link2 },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex" style={{ fontFamily: "'Outfit', system-ui, sans-serif" }}>
      <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet" />

      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 min-h-screen flex flex-col fixed left-0 top-0 z-30">
        <div className="p-5 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-400 to-blue-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">OS</span>
            </div>
            <div>
              <div className="text-white font-bold text-base tracking-tight">Orkestra</div>
              <div className="text-sky-400/50 text-[10px] uppercase tracking-[0.2em]">by OpenSID</div>
            </div>
          </div>
        </div>

        <nav className="flex-1 py-4 px-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeNav === item.id;
            return (
              <button key={item.id} onClick={() => setActiveNav(item.id)} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl mb-0.5 text-sm transition-all ${isActive ? "bg-sky-500/15 text-sky-400 font-medium" : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"}`}>
                <Icon size={18} />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <button onClick={handleLogout} className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-red-400 hover:bg-red-500/10 transition-all">
            <LogOut size={16} />
            Déconnexion
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 ml-64">
        <header className="sticky top-0 z-20 bg-white/80 backdrop-blur-xl border-b border-slate-100">
          <div className="flex items-center justify-between px-8 py-4">
            <div>
              <h1 className="text-xl font-bold text-slate-900 capitalize">{activeNav}</h1>
              <p className="text-sm text-slate-400 mt-0.5">Données en temps réel depuis SQL Server</p>
            </div>
          </div>
        </header>

        {activeNav === "dashboard" && <DashboardPage />}
        {activeNav === "contacts" && <ContactsPage />}
        {activeNav === "campaigns" && (
          <div className="p-8">
            <DashboardPage />
          </div>
        )}
        {(activeNav === "segments" || activeNav === "analytics" || activeNav === "integrations") && (
          <div className="p-8 flex items-center justify-center h-96">
            <div className="text-center">
              <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Zap size={24} className="text-slate-400" />
              </div>
              <h3 className="text-lg font-semibold text-slate-700">Page en construction</h3>
              <p className="text-sm text-slate-400 mt-1">Cette section arrive bientôt</p>
            </div>
          </div>
        )}

        <div className="px-8 pb-6 mt-4 text-center text-xs text-slate-300">
          OS Orkestra v1.0.0 · © 2026 OpenSID
        </div>
      </main>
    </div>
  );
}
