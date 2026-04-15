import { useState, useEffect, useCallback, useRef } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area } from "recharts";
import { Search, Users, Mail, BarChart3, Zap, Send, Eye, MousePointerClick, RefreshCw, Filter, Plus, LayoutDashboard, Target, Database, Link2, LogOut, ChevronLeft, ChevronRight, X, Calendar, FileText, ArrowUpRight, ArrowDownRight, Layers, Radio, Upload, Code, Trash2, Save, Edit3, Loader2, ArrowLeftRight, CheckCircle, AlertCircle, Clock } from "lucide-react";

const API = window.location.hostname === "localhost"
  ? "http://localhost:8000/api/v1"
  : "/api/v1";

// ══════════════════════════════════════════════════════════
// API HELPER
// ══════════════════════════════════════════════════════════

async function api(endpoint, options = {}) {
  const token = localStorage.getItem("orkestra_token");
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API}${endpoint}`, { ...options, headers });
  if (res.status === 401) { localStorage.removeItem("orkestra_token"); window.location.reload(); return null; }
  if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || `Erreur ${res.status}`); }
  return res.json();
}

// ══════════════════════════════════════════════════════════
// LOGIN
// ══════════════════════════════════════════════════════════

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState("admin@opensid.com");
  const [password, setPassword] = useState("Test1234");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const handleSubmit = async (e) => {
    e.preventDefault(); setLoading(true); setError("");
    try {
      const data = await fetch(`${API}/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) }).then(r => r.json());
      if (data.access_token) { localStorage.setItem("orkestra_token", data.access_token); onLogin(data); }
      else setError(data.detail || "Identifiants incorrects");
    } catch { setError("Impossible de se connecter au serveur"); }
    setLoading(false);
  };
  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "linear-gradient(135deg, #0a0f1a 0%, #121d33 50%, #0d1524 100%)", fontFamily: "'Outfit', system-ui" }}>
      <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-sky-400 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/25"><span className="text-white font-bold text-lg">OS</span></div>
            <div className="text-left"><div className="text-white font-bold text-2xl tracking-tight">Orkestra</div><div className="text-sky-400/60 text-xs uppercase tracking-[0.25em]">by OpenSID</div></div>
          </div>
        </div>
        <div className="bg-white/[0.04] backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
          <h2 className="text-white text-lg font-semibold mb-6">Connexion</h2>
          {error && <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 mb-4 text-red-400 text-sm">{error}</div>}
          <form onSubmit={handleSubmit}>
            <div className="mb-4"><label className="text-white/50 text-xs font-medium uppercase tracking-wider mb-2 block">Email</label><input type="email" value={email} onChange={e => setEmail(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-sky-400/50 transition-all" /></div>
            <div className="mb-6"><label className="text-white/50 text-xs font-medium uppercase tracking-wider mb-2 block">Mot de passe</label><input type="password" value={password} onChange={e => setPassword(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-sky-400/50 transition-all" /></div>
            <button type="submit" disabled={loading} className="w-full bg-gradient-to-r from-sky-500 to-blue-600 text-white font-medium py-3 rounded-xl hover:from-sky-400 hover:to-blue-500 transition-all disabled:opacity-50 shadow-lg shadow-blue-500/25">{loading ? "Connexion..." : "Se connecter"}</button>
          </form>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// SHARED COMPONENTS
// ══════════════════════════════════════════════════════════

const StatusBadge = ({ status }) => {
  const s = (status || "").toUpperCase();
  const styles = { RUNNING: "bg-emerald-50 text-emerald-700 border-emerald-200", COMPLETED: "bg-slate-100 text-slate-600 border-slate-200", SCHEDULED: "bg-amber-50 text-amber-700 border-amber-200", DRAFT: "bg-gray-50 text-gray-500 border-gray-200", PAUSED: "bg-red-50 text-red-600 border-red-200" };
  const labels = { RUNNING: "En cours", COMPLETED: "Terminée", SCHEDULED: "Planifiée", DRAFT: "Brouillon", PAUSED: "En pause" };
  return <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[s] || "bg-gray-50 text-gray-500 border-gray-200"}`}>{labels[s] || status}</span>;
};

const ChannelBadge = ({ channel }) => {
  const c = (channel || "").toUpperCase();
  if (c === "WHATSAPP") return <span className="text-green-600 text-xs font-bold bg-green-50 px-2 py-0.5 rounded-full">WhatsApp</span>;
  if (c === "SMS") return <span className="text-amber-600 text-xs font-bold bg-amber-50 px-2 py-0.5 rounded-full">SMS</span>;
  return <span className="text-sky-600 text-xs font-bold bg-sky-50 px-2 py-0.5 rounded-full">Email</span>;
};

const MetricCard = ({ icon: Icon, label, value, subtitle, loading }) => (
  <div className="bg-white rounded-2xl p-5 border border-slate-100 hover:border-slate-200 transition-all hover:shadow-sm">
    <div className="flex items-start justify-between mb-3"><div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center"><Icon size={18} className="text-white" /></div></div>
    <div className="text-2xl font-bold text-slate-900 tracking-tight">{loading ? <div className="h-8 w-24 bg-slate-100 rounded-lg animate-pulse" /> : value}</div>
    <div className="text-sm text-slate-500 mt-0.5">{label}</div>
    {subtitle && <div className="text-xs text-slate-400 mt-1">{subtitle}</div>}
  </div>
);

const Modal = ({ open, onClose, title, children }) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto m-4" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-6 border-b border-slate-100">
          <h2 className="text-lg font-bold text-slate-900">{title}</h2>
          <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-xl transition-colors"><X size={18} /></button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
};

// ══════════════════════════════════════════════════════════
// DASHBOARD
// ══════════════════════════════════════════════════════════

function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [cs, camp, ana] = await Promise.all([
          api("/contacts/stats"), api("/campaigns/?page=1&page_size=10&sort_order=desc"), api("/analytics/overview?days=30").catch(() => null),
        ]);
        setStats(cs); setCampaigns(camp?.items || []); setAnalytics(ana);
      } catch (err) { console.error(err); }
      setLoading(false);
    }
    load();
  }, []);

  const totalSent = campaigns.reduce((s, c) => s + (c.total_sent || 0), 0);
  const totalDelivered = campaigns.reduce((s, c) => s + (c.total_delivered || 0), 0);
  const totalOpened = campaigns.reduce((s, c) => s + (c.total_opened || 0), 0);
  const totalClicked = campaigns.reduce((s, c) => s + (c.total_clicked || 0), 0);
  const avgOpen = analytics ? `${analytics.open_rate}%` : totalDelivered > 0 ? `${((totalOpened / totalDelivered) * 100).toFixed(1)}%` : "—";
  const avgClick = analytics ? `${analytics.click_rate}%` : totalDelivered > 0 ? `${((totalClicked / totalDelivered) * 100).toFixed(1)}%` : "—";

  const funnelData = stats ? Object.entries(stats.by_stage || {}).map(([k, v]) => ({ name: k.replace("LeadStage.", ""), value: v, fill: { AWARENESS: "#0f172a", INTEREST: "#1e3a5f", CONSIDERATION: "#2563eb", PURCHASE: "#3b82f6", RETENTION: "#60a5fa" }[k.replace("LeadStage.", "")] || "#94a3b8" })) : [];
  const sourceData = stats ? Object.entries(stats.by_source || {}).map(([k, v]) => ({ name: k.replace("ContactSource.", "").replace("_", " "), value: v })) : [];
  const COLORS = ["#0f172a", "#1e3a5f", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd"];
  const chartData = [...campaigns].reverse().filter(c => c.total_sent > 0).slice(0, 8).map(c => ({ name: c.name.length > 15 ? c.name.slice(0, 15) + "…" : c.name, envoyés: c.total_sent, ouverts: c.total_opened, cliqués: c.total_clicked }));

  return (
    <div className="p-8">
      <div className="grid grid-cols-4 gap-4 mb-8">
        <MetricCard icon={Users} label="Contacts totaux" value={stats ? stats.total.toLocaleString("fr-FR") : "—"} loading={loading} subtitle={stats ? `${stats.active} actifs · ${stats.internal} internes` : ""} />
        <MetricCard icon={Send} label="Emails envoyés" value={analytics ? analytics.total_sent.toLocaleString("fr-FR") : totalSent.toLocaleString("fr-FR")} loading={loading} subtitle="30 derniers jours" />
        <MetricCard icon={Eye} label="Taux d'ouverture" value={avgOpen} loading={loading} subtitle="Moyenne 30j" />
        <MetricCard icon={MousePointerClick} label="Taux de clic" value={avgClick} loading={loading} subtitle="Moyenne 30j" />
      </div>
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="col-span-2 bg-white rounded-2xl border border-slate-100 p-6">
          <h3 className="text-base font-bold text-slate-900 mb-1">Performance des campagnes</h3>
          <p className="text-xs text-slate-400 mb-4">Données réelles</p>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="gS" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#0f172a" stopOpacity={0.08} /><stop offset="95%" stopColor="#0f172a" stopOpacity={0} /></linearGradient>
                  <linearGradient id="gO" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#3b82f6" stopOpacity={0.12} /><stop offset="95%" stopColor="#3b82f6" stopOpacity={0} /></linearGradient>
                  <linearGradient id="gC" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#22c55e" stopOpacity={0.12} /><stop offset="95%" stopColor="#22c55e" stopOpacity={0} /></linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" /><XAxis dataKey="name" tick={{ fontSize: 9, fill: "#94a3b8" }} axisLine={false} tickLine={false} /><YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} /><Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 12 }} />
                <Area type="monotone" dataKey="envoyés" stroke="#0f172a" strokeWidth={2} fill="url(#gS)" /><Area type="monotone" dataKey="ouverts" stroke="#3b82f6" strokeWidth={2} fill="url(#gO)" /><Area type="monotone" dataKey="cliqués" stroke="#22c55e" strokeWidth={2} fill="url(#gC)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : <div className="h-64 flex items-center justify-center text-slate-400">Chargement...</div>}
        </div>
        <div className="bg-white rounded-2xl border border-slate-100 p-6">
          <h3 className="text-base font-bold text-slate-900 mb-1">Sources</h3>
          <p className="text-xs text-slate-400 mb-4">Origine des contacts</p>
          {sourceData.length > 0 ? (<><ResponsiveContainer width="100%" height={170}><PieChart><Pie data={sourceData} dataKey="value" cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={3} strokeWidth={0}>{sourceData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Pie><Tooltip contentStyle={{ borderRadius: 12, fontSize: 12 }} /></PieChart></ResponsiveContainer><div className="space-y-1.5 mt-2">{sourceData.map((item, i) => (<div key={item.name} className="flex items-center justify-between text-xs"><div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} /><span className="text-slate-600">{item.name}</span></div><span className="font-semibold text-slate-800">{item.value}</span></div>))}</div></>) : <div className="h-48 flex items-center justify-center text-slate-400">Chargement...</div>}
        </div>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl border border-slate-100 p-6">
          <h3 className="text-base font-bold text-slate-900 mb-4">Funnel</h3>
          <div className="space-y-3">{funnelData.sort((a, b) => b.value - a.value).map(s => { const mx = Math.max(...funnelData.map(x => x.value), 1); return (<div key={s.name} className="flex items-center gap-3"><div className="w-24 text-xs text-slate-600 font-medium truncate">{s.name}</div><div className="flex-1 bg-slate-50 rounded-full h-7 overflow-hidden"><div className="h-full rounded-full flex items-center justify-end px-3" style={{ width: `${Math.max((s.value / mx) * 100, 12)}%`, backgroundColor: s.fill }}><span className="text-[10px] font-bold text-white">{s.value}</span></div></div></div>); })}</div>
        </div>
        <div className="col-span-2 bg-white rounded-2xl border border-slate-100 p-6">
          <h3 className="text-base font-bold text-slate-900 mb-4">Campagnes récentes</h3>
          <table className="w-full"><thead><tr className="border-b border-slate-100"><th className="text-left text-xs font-medium text-slate-400 pb-3">Campagne</th><th className="text-left text-xs font-medium text-slate-400 pb-3">Canal</th><th className="text-left text-xs font-medium text-slate-400 pb-3">Statut</th><th className="text-right text-xs font-medium text-slate-400 pb-3">Envoyés</th><th className="text-right text-xs font-medium text-slate-400 pb-3">Ouv.%</th></tr></thead>
          <tbody>{campaigns.slice(0, 8).map(c => { const or2 = c.total_delivered > 0 ? ((c.total_opened / c.total_delivered) * 100).toFixed(1) : "—"; return (<tr key={c.id} className="border-b border-slate-50 hover:bg-slate-50/50"><td className="py-2.5"><div className="text-sm font-medium text-slate-800 truncate max-w-[180px]">{c.name}</div></td><td className="py-2.5"><ChannelBadge channel={c.channel} /></td><td className="py-2.5"><StatusBadge status={c.status} /></td><td className="py-2.5 text-right text-sm font-mono text-slate-700">{c.total_sent > 0 ? c.total_sent.toLocaleString("fr-FR") : "—"}</td><td className="py-2.5 text-right text-sm font-mono text-slate-700">{or2 !== "—" ? `${or2}%` : "—"}</td></tr>); })}</tbody></table>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// CONTACTS
// ══════════════════════════════════════════════════════════

function ContactsPage() {
  const [contacts, setContacts] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newContact, setNewContact] = useState({ email: "", first_name: "", last_name: "", company: "", job_title: "", phone: "", country: "", city: "", source: "manual", is_internal: false, gdpr_consent: true });
  const [adding, setAdding] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try { const p = new URLSearchParams({ page, page_size: 20, sort_order: "desc" }); if (search) p.set("search", search); const d = await api(`/contacts/?${p}`); setContacts(d?.items || []); setTotal(d?.total || 0); setTotalPages(d?.total_pages || 1); } catch (e) { console.error(e); }
    setLoading(false);
  }, [page, search]);
  useEffect(() => { load(); }, [load]);

  const handleAddContact = async (e) => {
    e.preventDefault(); if (!newContact.email) return alert("Email requis");
    setAdding(true);
    try {
      await api("/contacts/", { method: "POST", body: JSON.stringify(newContact) });
      setShowAdd(false);
      setNewContact({ email: "", first_name: "", last_name: "", company: "", job_title: "", phone: "", country: "", city: "", source: "manual", is_internal: false, gdpr_consent: true });
      load();
    } catch (err) { alert("Erreur: " + err.message); }
    setAdding(false);
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div><h2 className="text-xl font-bold text-slate-900">Contacts</h2><p className="text-sm text-slate-400">{total.toLocaleString("fr-FR")} contacts</p></div>
        <div className="flex gap-3">
          <form onSubmit={e => { e.preventDefault(); setPage(1); load(); }} className="flex gap-2"><input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Rechercher..." className="px-4 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-sky-400 w-64" /><button type="submit" className="px-4 py-2 bg-slate-900 text-white rounded-xl text-sm"><Search size={16} /></button></form>
          <button onClick={() => setShowAdd(true)} className="flex items-center gap-2 px-4 py-2 bg-sky-600 text-white rounded-xl text-sm font-medium hover:bg-sky-500"><Plus size={16}/>Nouveau contact</button>
        </div>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
        <table className="w-full"><thead><tr className="border-b border-slate-100 bg-slate-50/50"><th className="text-left text-xs font-medium text-slate-400 p-4">Contact</th><th className="text-left text-xs font-medium text-slate-400 p-4">Entreprise</th><th className="text-left text-xs font-medium text-slate-400 p-4">Pays</th><th className="text-left text-xs font-medium text-slate-400 p-4">Source</th><th className="text-left text-xs font-medium text-slate-400 p-4">Étape</th><th className="text-right text-xs font-medium text-slate-400 p-4">Score</th></tr></thead>
        <tbody>{loading ? Array.from({ length: 8 }).map((_, i) => <tr key={i} className="border-b border-slate-50"><td colSpan={6} className="p-4"><div className="h-5 bg-slate-100 rounded animate-pulse" /></td></tr>) :
        contacts.map(c => (<tr key={c.id} className="border-b border-slate-50 hover:bg-slate-50/50"><td className="p-4"><div className="flex items-center gap-3"><div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-xs font-bold text-slate-600">{(c.first_name||"?")[0]}{(c.last_name||"?")[0]}</div><div><div className="text-sm font-medium text-slate-800">{c.first_name} {c.last_name}</div><div className="text-xs text-slate-400">{c.email}</div></div></div></td><td className="p-4 text-sm text-slate-600">{c.company||"—"}</td><td className="p-4 text-sm text-slate-600">{c.country||"—"}</td><td className="p-4"><span className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded-full">{(c.source||"").replace("ContactSource.","").replace("_"," ")}</span></td><td className="p-4 text-xs font-medium text-sky-600">{(c.lead_stage||"").replace("LeadStage.","")}</td><td className="p-4 text-right"><span className={`text-sm font-bold ${c.lead_score>=80?"text-emerald-600":c.lead_score>=50?"text-amber-600":"text-slate-500"}`}>{c.lead_score}</span></td></tr>))}</tbody></table>
        <div className="flex items-center justify-between p-4 border-t border-slate-100"><span className="text-sm text-slate-400">Page {page}/{totalPages}</span><div className="flex gap-2"><button onClick={() => setPage(Math.max(1,page-1))} disabled={page<=1} className="p-2 border border-slate-200 rounded-lg disabled:opacity-30 hover:bg-slate-50"><ChevronLeft size={16}/></button><button onClick={() => setPage(Math.min(totalPages,page+1))} disabled={page>=totalPages} className="p-2 border border-slate-200 rounded-lg disabled:opacity-30 hover:bg-slate-50"><ChevronRight size={16}/></button></div></div>
      </div>

      <Modal open={showAdd} onClose={() => setShowAdd(false)} title="Nouveau contact">
        <form onSubmit={handleAddContact} className="space-y-4">
          <div><label className="text-sm font-medium text-slate-700 mb-1 block">Email *</label><input type="email" required value={newContact.email} onChange={e => setNewContact({...newContact, email: e.target.value})} placeholder="contact@exemple.com" className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Prénom</label><input value={newContact.first_name} onChange={e => setNewContact({...newContact, first_name: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Nom</label><input value={newContact.last_name} onChange={e => setNewContact({...newContact, last_name: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Entreprise</label><input value={newContact.company} onChange={e => setNewContact({...newContact, company: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Poste</label><input value={newContact.job_title} onChange={e => setNewContact({...newContact, job_title: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Téléphone</label><input value={newContact.phone} onChange={e => setNewContact({...newContact, phone: e.target.value})} placeholder="+33..." className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Pays</label><input value={newContact.country} onChange={e => setNewContact({...newContact, country: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
          </div>
          <div><label className="text-sm font-medium text-slate-700 mb-1 block">Ville</label><input value={newContact.city} onChange={e => setNewContact({...newContact, city: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm text-slate-600"><input type="checkbox" checked={newContact.is_internal} onChange={e => setNewContact({...newContact, is_internal: e.target.checked})} className="rounded" />Contact interne (collaborateur)</label>
            <label className="flex items-center gap-2 text-sm text-slate-600"><input type="checkbox" checked={newContact.gdpr_consent} onChange={e => setNewContact({...newContact, gdpr_consent: e.target.checked})} className="rounded" />Consentement RGPD</label>
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={() => setShowAdd(false)} className="flex-1 px-4 py-2.5 border border-slate-200 text-slate-600 rounded-xl text-sm font-medium hover:bg-slate-50">Annuler</button>
            <button type="submit" disabled={adding} className="flex-1 px-4 py-2.5 bg-sky-600 text-white rounded-xl text-sm font-medium hover:bg-sky-500 disabled:opacity-50">{adding ? "Ajout..." : "Ajouter le contact"}</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// CAMPAIGNS + CREATE FORM
// ══════════════════════════════════════════════════════════

function CampaignsPage() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [segments, setSegments] = useState([]);
  const [form, setForm] = useState({ name: "", description: "", campaign_type: "external", channel: "email", template_id: "", segment_id: "", subject: "", from_name: "OpenSID Marketing", from_email: "marketing@opensid.com" });
  const [creating, setCreating] = useState(false);
  const [detail, setDetail] = useState(null);

  const load = async () => { setLoading(true); try { const d = await api("/campaigns/?page=1&page_size=50"); setCampaigns(d?.items || []); } catch(e){console.error(e);} setLoading(false); };
  useEffect(() => { load(); }, []);

  const openCreate = async () => {
    try { const [t, s] = await Promise.all([api("/templates/"), api("/segments/")]); setTemplates(t || []); setSegments(s || []); } catch(e) { console.error(e); }
    setShowCreate(true);
  };

  const handleCreate = async (e) => {
    e.preventDefault(); setCreating(true);
    try {
      const body = { ...form };
      if (!body.template_id) delete body.template_id;
      if (!body.segment_id) delete body.segment_id;
      await api("/campaigns/", { method: "POST", body: JSON.stringify(body) });
      setShowCreate(false); setForm({ name: "", description: "", campaign_type: "external", channel: "email", template_id: "", segment_id: "", subject: "", from_name: "OpenSID Marketing", from_email: "marketing@opensid.com" });
      load();
    } catch (err) { alert("Erreur: " + err.message); }
    setCreating(false);
  };

  const launchCampaign = async (id) => {
    if (!confirm("Lancer cette campagne ?")) return;
    try { await api('/diffusion/launch-campaign', { method: 'POST', body: JSON.stringify({ campaign_id: id }) }); load(); } catch (err) { alert("Erreur: " + err.message); }
  };

  const loadDetail = async (id) => {
    try { const d = await api(`/analytics/campaigns/${id}/detail`); setDetail(d); } catch (err) { console.error(err); }
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div><h2 className="text-xl font-bold text-slate-900">Campagnes</h2><p className="text-sm text-slate-400">{campaigns.length} campagnes</p></div>
        <button onClick={openCreate} className="flex items-center gap-2 px-4 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800"><Plus size={16}/>Nouvelle campagne</button>
      </div>

      <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
        <table className="w-full"><thead><tr className="border-b border-slate-100 bg-slate-50/50"><th className="text-left text-xs font-medium text-slate-400 p-4">Campagne</th><th className="text-left text-xs font-medium text-slate-400 p-4">Canal</th><th className="text-left text-xs font-medium text-slate-400 p-4">Statut</th><th className="text-right text-xs font-medium text-slate-400 p-4">Envoyés</th><th className="text-right text-xs font-medium text-slate-400 p-4">Ouv.%</th><th className="text-right text-xs font-medium text-slate-400 p-4">Clic%</th><th className="text-right text-xs font-medium text-slate-400 p-4">Actions</th></tr></thead>
        <tbody>{campaigns.map(c => { const or2 = c.total_delivered>0?((c.total_opened/c.total_delivered)*100).toFixed(1):"—"; const cr = c.total_delivered>0?((c.total_clicked/c.total_delivered)*100).toFixed(1):"—"; return (
          <tr key={c.id} className="border-b border-slate-50 hover:bg-slate-50/50">
            <td className="p-4"><div className="flex items-center gap-2.5"><div className={`w-1.5 h-7 rounded-full ${c.campaign_type==="internal"||c.campaign_type==="INTERNAL"?"bg-sky-400":"bg-slate-800"}`}/><div><div className="text-sm font-medium text-slate-800 truncate max-w-[200px]">{c.name}</div><div className="text-xs text-slate-400">{c.campaign_type==="internal"||c.campaign_type==="INTERNAL"?"Interne":"Externe"}</div></div></div></td>
            <td className="p-4"><ChannelBadge channel={c.channel}/></td><td className="p-4"><StatusBadge status={c.status}/></td>
            <td className="p-4 text-right text-sm font-mono text-slate-700">{c.total_sent>0?c.total_sent.toLocaleString("fr-FR"):"—"}</td>
            <td className="p-4 text-right text-sm font-mono text-slate-700">{or2!=="—"?`${or2}%`:"—"}</td>
            <td className="p-4 text-right text-sm font-mono text-slate-700">{cr!=="—"?`${cr}%`:"—"}</td>
            <td className="p-4 text-right flex gap-2 justify-end">
              {(c.status==="DRAFT"||c.status==="draft"||c.status==="SCHEDULED"||c.status==="scheduled") && <button onClick={()=>launchCampaign(c.id)} className="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-lg text-xs font-medium hover:bg-emerald-100">Lancer</button>}
              <button onClick={()=>loadDetail(c.id)} className="px-3 py-1 bg-sky-50 text-sky-700 rounded-lg text-xs font-medium hover:bg-sky-100">Détails</button>
            </td></tr>);})}</tbody></table>
      </div>

      {/* CREATE MODAL */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Nouvelle campagne">
        <form onSubmit={handleCreate} className="space-y-4">
          <div><label className="text-sm font-medium text-slate-700 mb-1 block">Nom de la campagne *</label><input type="text" required value={form.name} onChange={e => setForm({...form, name: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" placeholder="Ex: Newsletter Avril 2026" /></div>
          <div><label className="text-sm font-medium text-slate-700 mb-1 block">Objet de l'email *</label><input type="text" required value={form.subject} onChange={e => setForm({...form, subject: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" placeholder="Ex: Les actualités du mois" /></div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Type</label><select value={form.campaign_type} onChange={e => setForm({...form, campaign_type: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400"><option value="external">Externe</option><option value="internal">Interne</option></select></div>
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Canal</label><select value={form.channel} onChange={e => setForm({...form, channel: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400"><option value="email">Email</option><option value="sms">SMS</option><option value="whatsapp">WhatsApp</option></select></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Template</label><select value={form.template_id} onChange={e => setForm({...form, template_id: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400"><option value="">— Aucun —</option>{templates.map(t => <option key={t.id} value={t.id}>{t.name} ({t.category})</option>)}</select></div>
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Segment cible</label><select value={form.segment_id} onChange={e => setForm({...form, segment_id: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400"><option value="">— Tous —</option>{segments.map(s => <option key={s.id} value={s.id}>{s.name} ({s.contact_count} contacts)</option>)}</select></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Nom expéditeur</label><input type="text" value={form.from_name} onChange={e => setForm({...form, from_name: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Email expéditeur</label><input type="email" value={form.from_email} onChange={e => setForm({...form, from_email: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
          </div>
          <div><label className="text-sm font-medium text-slate-700 mb-1 block">Description</label><textarea value={form.description} onChange={e => setForm({...form, description: e.target.value})} rows={3} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400 resize-none" placeholder="Description de la campagne..." /></div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={() => setShowCreate(false)} className="flex-1 px-4 py-2.5 border border-slate-200 text-slate-600 rounded-xl text-sm font-medium hover:bg-slate-50">Annuler</button>
            <button type="submit" disabled={creating} className="flex-1 px-4 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800 disabled:opacity-50">{creating ? "Création..." : "Créer la campagne"}</button>
          </div>
        </form>
      </Modal>

      {/* DETAIL MODAL */}
      <Modal open={!!detail} onClose={() => setDetail(null)} title={detail?.campaign?.name || "Détail"}>
        {detail && (
          <div className="space-y-6">
            <div className="grid grid-cols-3 gap-4">
              {[
                { label: "Envoyés", value: detail.metrics.total_sent },
                { label: "Délivrés", value: detail.metrics.total_delivered },
                { label: "Ouverts", value: detail.metrics.total_opened },
                { label: "Cliqués", value: detail.metrics.total_clicked },
                { label: "Taux ouv.", value: `${detail.metrics.open_rate}%` },
                { label: "Taux clic", value: `${detail.metrics.click_rate}%` },
                { label: "Réactivité", value: `${detail.metrics.reactivity_rate}%` },
                { label: "Délivrabilité", value: `${detail.metrics.deliverability_rate}%` },
                { label: "Rebonds", value: `${detail.metrics.bounce_rate}%` },
              ].map(m => (
                <div key={m.label} className="bg-slate-50 rounded-xl p-3 text-center">
                  <div className="text-lg font-bold text-slate-900">{typeof m.value === "number" ? m.value.toLocaleString("fr-FR") : m.value}</div>
                  <div className="text-xs text-slate-500">{m.label}</div>
                </div>
              ))}
            </div>
            {detail.top_links?.length > 0 && (
              <div><h4 className="text-sm font-bold text-slate-700 mb-2">Top liens cliqués</h4>
              {detail.top_links.map((l, i) => (
                <div key={i} className="flex items-center justify-between py-1.5 border-b border-slate-50">
                  <span className="text-xs text-slate-600 truncate max-w-[300px]">{l.url}</span>
                  <span className="text-xs font-bold text-slate-800">{l.clicks} clics</span>
                </div>
              ))}</div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// SEGMENTS
// ══════════════════════════════════════════════════════════

// ══════════════════════════════════════════════════════════
// SEGMENTS (DYNAMIQUES) — Remplacer l'ancien SegmentsPage dans App.jsx
// ══════════════════════════════════════════════════════════

function SegmentsPage() {
  const [segments, setSegments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSegment, setSelectedSegment] = useState(null);
  const [segmentContacts, setSegmentContacts] = useState([]);
  const [contactsLoading, setContactsLoading] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [newSeg, setNewSeg] = useState({ name: "", description: "", filter_field: "country", filter_value: "" });
  const [creating, setCreating] = useState(false);

  const load = async () => {
    setLoading(true);
    try { const d = await api("/segments/"); setSegments(d || []); }
    catch (e) { console.error(e); }
    setLoading(false);
  };
  useEffect(() => { load(); }, []);

  const viewSegment = async (seg) => {
    setSelectedSegment(seg);
    setContactsLoading(true);
    try {
      const d = await api(`/segments/${seg.id}/contacts?page=1&page_size=50`);
      setSegmentContacts(d?.contacts || []);
    } catch (e) { console.error(e); setSegmentContacts([]); }
    setContactsLoading(false);
  };

  const handleCreate = async () => {
    if (!newSeg.name) return alert("Nom requis");
    setCreating(true);
    try {
      const filter = {};
      if (newSeg.filter_value) {
        filter[newSeg.filter_field] = newSeg.filter_value;
      }
      await api("/segments/", {
        method: "POST",
        body: JSON.stringify({
          name: newSeg.name,
          description: newSeg.description || `Segment ${newSeg.name}`,
          filter_criteria: filter,
          is_dynamic: true,
        }),
      });
      setShowCreate(false);
      setNewSeg({ name: "", description: "", filter_field: "country", filter_value: "" });
      load();
    } catch (err) { alert("Erreur: " + err.message); }
    setCreating(false);
  };

  const handleDelete = async (id) => {
    if (!confirm("Supprimer ce segment ?")) return;
    try { await api(`/segments/${id}`, { method: "DELETE" }); setSelectedSegment(null); load(); }
    catch (err) { alert("Erreur: " + err.message); }
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div><h2 className="text-xl font-bold text-slate-900">Segments</h2><p className="text-sm text-slate-400">{segments.length} segments · comptage dynamique</p></div>
        <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 px-4 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800"><Plus size={16}/>Nouveau segment</button>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-8">
        {segments.map(s => (
          <button key={s.id} onClick={() => viewSegment(s)} className={`text-left bg-white rounded-2xl border p-5 hover:border-sky-400 transition-all ${selectedSegment?.id === s.id ? "border-sky-400 ring-2 ring-sky-100" : "border-slate-100"}`}>
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl bg-sky-50 flex items-center justify-center"><Target size={18} className="text-sky-600" /></div>
              <div><div className="text-sm font-bold text-slate-900">{s.name}</div><div className="text-xs text-slate-400">{s.description}</div></div>
            </div>
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-50">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">{s.is_dynamic ? "Dynamique" : "Statique"}</span>
                {s.filter_criteria && Object.keys(s.filter_criteria).length > 0 && (
                  <span className="text-xs bg-sky-50 text-sky-600 px-2 py-0.5 rounded-full">
                    {Object.entries(s.filter_criteria).map(([k,v]) => `${k}=${v}`).join(", ")}
                  </span>
                )}
              </div>
              <span className="text-lg font-bold text-slate-900">{s.contact_count}</span>
            </div>
          </button>
        ))}
      </div>

      {/* Détail du segment sélectionné */}
      {selectedSegment && (
        <div className="bg-white rounded-2xl border border-slate-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Contacts dans « {selectedSegment.name} »</h3>
              <p className="text-xs text-slate-400">{segmentContacts.length} contacts affichés</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => handleDelete(selectedSegment.id)} className="px-3 py-1.5 text-xs text-red-500 hover:bg-red-50 rounded-lg">Supprimer</button>
              <button onClick={() => setSelectedSegment(null)} className="px-3 py-1.5 text-xs text-slate-500 hover:bg-slate-50 rounded-lg">Fermer</button>
            </div>
          </div>
          {contactsLoading ? (
            <div className="py-8 text-center text-slate-400">Chargement...</div>
          ) : segmentContacts.length === 0 ? (
            <div className="py-8 text-center text-slate-400">Aucun contact dans ce segment</div>
          ) : (
            <table className="w-full">
              <thead><tr className="border-b border-slate-100">
                <th className="text-left text-xs font-medium text-slate-400 pb-3">Contact</th>
                <th className="text-left text-xs font-medium text-slate-400 pb-3">Entreprise</th>
                <th className="text-left text-xs font-medium text-slate-400 pb-3">Pays</th>
                <th className="text-left text-xs font-medium text-slate-400 pb-3">Poste</th>
                <th className="text-right text-xs font-medium text-slate-400 pb-3">Score</th>
              </tr></thead>
              <tbody>{segmentContacts.map(c => (
                <tr key={c.id} className="border-b border-slate-50 hover:bg-slate-50/50">
                  <td className="py-2.5"><div><div className="text-sm font-medium text-slate-800">{c.first_name} {c.last_name}</div><div className="text-xs text-slate-400">{c.email}</div></div></td>
                  <td className="py-2.5 text-sm text-slate-600">{c.company || "—"}</td>
                  <td className="py-2.5 text-sm text-slate-600">{c.country || "—"}</td>
                  <td className="py-2.5 text-sm text-slate-600">{c.job_title || "—"}</td>
                  <td className="py-2.5 text-right"><span className={`text-sm font-bold ${c.lead_score >= 80 ? "text-emerald-600" : c.lead_score >= 50 ? "text-amber-600" : "text-slate-500"}`}>{c.lead_score}</span></td>
                </tr>
              ))}</tbody>
            </table>
          )}
        </div>
      )}

      {/* Modal création segment */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Nouveau segment">
        <div className="space-y-4">
          <div><label className="text-sm font-medium text-slate-700 mb-1 block">Nom du segment *</label>
            <input value={newSeg.name} onChange={e => setNewSeg({...newSeg, name: e.target.value})} placeholder="Ex: Clients Afrique" className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
          <div><label className="text-sm font-medium text-slate-700 mb-1 block">Description</label>
            <input value={newSeg.description} onChange={e => setNewSeg({...newSeg, description: e.target.value})} placeholder="Description du segment" className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Filtrer par</label>
              <select value={newSeg.filter_field} onChange={e => setNewSeg({...newSeg, filter_field: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400">
                <option value="country">Pays</option>
                <option value="city">Ville</option>
                <option value="company">Entreprise</option>
                <option value="source">Source</option>
                <option value="status">Statut</option>
                <option value="business_unit">Business Unit</option>
              </select></div>
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Valeur</label>
              <input value={newSeg.filter_value} onChange={e => setNewSeg({...newSeg, filter_value: e.target.value})} placeholder="Ex: Ghana, France..." className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
          </div>
          <p className="text-xs text-slate-400">Laissez la valeur vide pour un segment qui inclut tous les contacts.</p>
          <div className="flex gap-3 pt-2">
            <button onClick={() => setShowCreate(false)} className="flex-1 px-4 py-2.5 border border-slate-200 text-slate-600 rounded-xl text-sm font-medium hover:bg-slate-50">Annuler</button>
            <button onClick={handleCreate} disabled={creating} className="flex-1 px-4 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800 disabled:opacity-50">{creating ? "Création..." : "Créer le segment"}</button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

function AnalyticsPage() {
  const [overview, setOverview] = useState(null);
  const [ranking, setRanking] = useState([]);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([api(`/analytics/overview?days=${days}`), api("/analytics/campaigns/ranking?limit=10")])
      .then(([o, r]) => { setOverview(o); setRanking(r || []); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [days]);

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-slate-900">Analytics</h2>
        <div className="flex gap-2">{[7, 30, 90].map(d => (<button key={d} onClick={() => setDays(d)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${days === d ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}>{d}j</button>))}</div>
      </div>
      {overview && (
        <>
          <div className="grid grid-cols-4 gap-4 mb-8">
            <MetricCard icon={Send} label="Envoyés" value={overview.total_sent.toLocaleString("fr-FR")} subtitle={`${days} derniers jours`} />
            <MetricCard icon={Eye} label="Taux d'ouverture" value={`${overview.open_rate}%`} subtitle={`${overview.unique_opens} ouvertures uniques`} />
            <MetricCard icon={MousePointerClick} label="Taux de clic" value={`${overview.click_rate}%`} subtitle={`${overview.unique_clicks} clics uniques`} />
            <MetricCard icon={BarChart3} label="Délivrabilité" value={`${overview.deliverability_rate}%`} subtitle={`${overview.total_bounced} rebonds`} />
          </div>
          <div className="bg-white rounded-2xl border border-slate-100 p-6">
            <h3 className="text-base font-bold text-slate-900 mb-4">Top campagnes par ouvertures</h3>
            <table className="w-full"><thead><tr className="border-b border-slate-100"><th className="text-left text-xs font-medium text-slate-400 pb-3">Campagne</th><th className="text-right text-xs font-medium text-slate-400 pb-3">Envoyés</th><th className="text-right text-xs font-medium text-slate-400 pb-3">Ouv.%</th><th className="text-right text-xs font-medium text-slate-400 pb-3">Clic%</th><th className="text-right text-xs font-medium text-slate-400 pb-3">Rebond%</th></tr></thead>
            <tbody>{ranking.map(c => (<tr key={c.id} className="border-b border-slate-50"><td className="py-3"><div className="text-sm font-medium text-slate-800">{c.name}</div><div className="text-xs text-slate-400">{c.type} · {c.channel}</div></td><td className="py-3 text-right text-sm font-mono">{c.total_sent.toLocaleString("fr-FR")}</td><td className="py-3 text-right text-sm font-mono text-emerald-600 font-bold">{c.open_rate}%</td><td className="py-3 text-right text-sm font-mono text-sky-600">{c.click_rate}%</td><td className="py-3 text-right text-sm font-mono text-red-500">{c.bounce_rate}%</td></tr>))}</tbody></table>
          </div>
        </>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// INTEGRATIONS
// ══════════════════════════════════════════════════════════

const INTEGRATION_FIELDS = {
  database: [
    { key: "db_type", label: "Type de base", type: "select", options: [{ value: "mssql", label: "SQL Server" }, { value: "postgresql", label: "PostgreSQL" }, { value: "mysql", label: "MySQL" }, { value: "sqlite", label: "SQLite" }, { value: "oracle", label: "Oracle" }] },
    { key: "host", label: "Hôte", placeholder: "localhost" },
    { key: "port", label: "Port", placeholder: "1433" },
    { key: "username", label: "Utilisateur", placeholder: "sa" },
    { key: "password", label: "Mot de passe", type: "password" },
    { key: "database", label: "Base de données", placeholder: "hubline" },
  ],
  crm_dynamics: [
    { key: "base_url", label: "URL Dynamics", placeholder: "https://your-org.crm4.dynamics.com" },
    { key: "tenant_id", label: "Tenant ID" },
    { key: "client_id", label: "Client ID" },
    { key: "client_secret", label: "Client Secret", type: "password" },
  ],
  crm_salesforce: [
    { key: "base_url", label: "URL Salesforce", placeholder: "https://login.salesforce.com" },
    { key: "client_id", label: "Client ID" },
    { key: "client_secret", label: "Client Secret", type: "password" },
    { key: "username", label: "Utilisateur" },
    { key: "password", label: "Mot de passe", type: "password" },
  ],
  azure_ad: [
    { key: "tenant_id", label: "Tenant ID" },
    { key: "client_id", label: "Client ID (Application)" },
    { key: "client_secret", label: "Client Secret", type: "password" },
  ],
  smtp: [
    { key: "host", label: "Serveur SMTP", placeholder: "smtp.gmail.com" },
    { key: "port", label: "Port", placeholder: "587" },
    { key: "username", label: "Utilisateur / Email" },
    { key: "password", label: "Mot de passe / App Password", type: "password" },
    { key: "use_tls", label: "TLS", type: "select", options: [{ value: "true", label: "Oui (recommandé)" }, { value: "false", label: "Non" }] },
    { key: "from_email", label: "Email expéditeur", placeholder: "noreply@opensid.com" },
    { key: "from_name", label: "Nom expéditeur", placeholder: "OS Orkestra" },
  ],
  whatsapp: [
    { key: "api_token", label: "API Token (Meta Business)", type: "password" },
    { key: "phone_number_id", label: "Phone Number ID" },
  ],
  sms: [
    { key: "provider", label: "Fournisseur", type: "select", options: [{ value: "twilio", label: "Twilio" }, { value: "vonage", label: "Vonage" }, { value: "other", label: "Autre" }] },
    { key: "api_key", label: "API Key", type: "password" },
    { key: "api_secret", label: "API Secret", type: "password" },
    { key: "from_number", label: "Numéro expéditeur", placeholder: "+33612345678" },
  ],
};

const INTEGRATION_ICONS = {
  database: Database, crm_dynamics: Link2, crm_salesforce: Link2,
  azure_ad: Users, smtp: Mail, whatsapp: Send, sms: Send,
};

const INTEGRATION_COLORS = {
  database: "bg-indigo-50 text-indigo-600", crm_dynamics: "bg-blue-50 text-blue-600",
  crm_salesforce: "bg-sky-50 text-sky-600", azure_ad: "bg-violet-50 text-violet-600",
  smtp: "bg-amber-50 text-amber-600", whatsapp: "bg-green-50 text-green-600",
  sms: "bg-orange-50 text-orange-600",
};

function IntegrationsPage() {
  const [integrations, setIntegrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [configuring, setConfiguring] = useState(null); // type being configured
  const [formData, setFormData] = useState({});
  const [testing, setTesting] = useState(false);
  const [actionResult, setActionResult] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try { const d = await api("/integrations/configured"); setIntegrations(d || []); }
    catch (e) { console.error(e); }
    setLoading(false);
  };
  useEffect(() => { load(); }, []);

  const openConfig = (type) => {
    setConfiguring(type);
    setFormData({});
    setActionResult(null);
  };

  const handleTest = async () => {
    setTesting(true); setActionResult(null);
    try {
      const result = await api("/integrations/test-connection", {
        method: "POST", body: JSON.stringify({ type: configuring, config: formData }),
      });
      setActionResult(result);
    } catch (err) { setActionResult({ success: false, message: err.message }); }
    setTesting(false);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const integ = integrations.find(i => i.type === configuring);
      await api("/integrations/configure", {
        method: "POST",
        body: JSON.stringify({ type: configuring, name: integ?.name || configuring, config: formData }),
      });
      setConfiguring(null);
      load();
    } catch (err) { alert("Erreur: " + err.message); }
    setSaving(false);
  };

  const handleDelete = async (id) => {
    if (!confirm("Supprimer cette intégration ?")) return;
    try { await api(`/integrations/${id}`, { method: "DELETE" }); load(); }
    catch (err) { alert("Erreur: " + err.message); }
  };

  // Séparer sources vs canaux
  const sources = integrations.filter(i => ["database", "crm_dynamics", "crm_salesforce", "azure_ad"].includes(i.type));
  const channels = integrations.filter(i => ["smtp", "whatsapp", "sms"].includes(i.type));

  const renderCard = (integ) => {
    const Icon = INTEGRATION_ICONS[integ.type] || Database;
    const colorClass = INTEGRATION_COLORS[integ.type] || "bg-slate-50 text-slate-600";
    const statusColors = { connected: "bg-emerald-500", configured: "bg-amber-500", error: "bg-red-500", not_configured: "bg-slate-300" };

    return (
      <div key={integ.type + (integ.id || "")} className="bg-white rounded-2xl border border-slate-100 p-5 hover:border-slate-200 transition-all">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl ${colorClass} flex items-center justify-center`}><Icon size={18} /></div>
            <div>
              <div className="text-sm font-bold text-slate-900">{integ.name}</div>
              <div className="text-xs text-slate-400">{integ.description || ""}</div>
            </div>
          </div>
          <div className={`w-2.5 h-2.5 rounded-full ${statusColors[integ.status] || statusColors.not_configured}`} title={integ.status} />
        </div>
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-50">
          <span className="text-xs text-slate-400">
            {integ.status === "connected" ? "Connecté" : integ.status === "configured" ? "Configuré" : integ.status === "error" ? "Erreur" : "Non configuré"}
          </span>
          <div className="flex gap-2">
            {integ.id && <button onClick={() => handleDelete(integ.id)} className="px-2.5 py-1 text-xs text-red-500 hover:bg-red-50 rounded-lg transition-colors">Supprimer</button>}
            <button onClick={() => openConfig(integ.type)} className="px-3 py-1 bg-slate-900 text-white text-xs font-medium rounded-lg hover:bg-slate-800 transition-colors">
              {integ.status === "not_configured" ? "Configurer" : "Modifier"}
            </button>
          </div>
        </div>
      </div>
    );
  };

  const fields = configuring ? (INTEGRATION_FIELDS[configuring] || []) : [];
  const configuringInteg = integrations.find(i => i.type === configuring);

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-xl font-bold text-slate-900">Intégrations</h2>
        <p className="text-sm text-slate-400 mt-1">Connectez vos sources de données et canaux de diffusion</p>
      </div>

      {/* Sources de données */}
      <div className="mb-8">
        <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider mb-4">Sources de données</h3>
        <div className="grid grid-cols-2 gap-4">
          {sources.map(renderCard)}
        </div>
      </div>

      {/* Canaux de diffusion */}
      <div className="mb-8">
        <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider mb-4">Canaux de diffusion</h3>
        <div className="grid grid-cols-3 gap-4">
          {channels.map(renderCard)}
        </div>
      </div>

      {/* CONFIGURATION MODAL */}
      <Modal open={!!configuring} onClose={() => setConfiguring(null)} title={`Configurer : ${configuringInteg?.name || configuring}`}>
        <div className="space-y-4">
          {fields.map(field => (
            <div key={field.key}>
              <label className="text-sm font-medium text-slate-700 mb-1 block">{field.label}</label>
              {field.type === "select" ? (
                <select value={formData[field.key] || ""} onChange={e => setFormData({ ...formData, [field.key]: e.target.value })} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400">
                  <option value="">— Sélectionner —</option>
                  {(field.options || []).map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              ) : (
                <input type={field.type || "text"} value={formData[field.key] || ""} onChange={e => setFormData({ ...formData, [field.key]: e.target.value })} placeholder={field.placeholder || ""} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" />
              )}
            </div>
          ))}

          {/* Test result */}
          {actionResult && (
            <div className={`rounded-xl p-4 text-sm ${actionResult.success ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-700 border border-red-200"}`}>
              {actionResult.success ? "✓ " : "✗ "}{actionResult.message}
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button onClick={handleTest} disabled={testing} className="flex-1 px-4 py-2.5 border border-slate-200 text-slate-700 rounded-xl text-sm font-medium hover:bg-slate-50 disabled:opacity-50">
              {testing ? "Test en cours..." : "Tester la connexion"}
            </button>
            <button onClick={handleSave} disabled={saving} className="flex-1 px-4 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800 disabled:opacity-50">
              {saving ? "Sauvegarde..." : "Sauvegarder"}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// MAPPING PAGE
// ══════════════════════════════════════════════════════════

function MappingPage() {
  const [step, setStep] = useState(1);
  const [conn, setConn] = useState({ db_type: "mssql", host: "osmdm-server.database.windows.net", port: 1433, username: "mdm-admin", password: "", database: "CRM-Test" });
  const [tables, setTables] = useState([]);
  const [selectedTable, setSelectedTable] = useState("");
  const [columns, setColumns] = useState([]);
  const [sampleData, setSampleData] = useState([]);
  const [mappings, setMappings] = useState([]);
  const [customMappings, setCustomMappings] = useState([]);
  const [valueMappings, setValueMappings] = useState({});
  const [preview, setPreview] = useState([]);
  const [targetFields, setTargetFields] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [importResult, setImportResult] = useState(null);
  const [savedMappings, setSavedMappings] = useState([]);

  useEffect(() => {
    api("/mapping/target-fields").then(setTargetFields).catch(() => {});
    api("/mapping/saved").then(setSavedMappings).catch(() => {});
  }, []);

  const handleConnect = async () => {
    setLoading(true); setError("");
    try { const data = await api("/mapping/list-tables", { method: "POST", body: JSON.stringify(conn) }); setTables(data.tables || []); setStep(2); }
    catch (err) { setError(err.message); }
    setLoading(false);
  };

  const handleSelectTable = async (tableName) => {
    setSelectedTable(tableName); setLoading(true); setError("");
    try {
      const data = await api("/mapping/table-schema", { method: "POST", body: JSON.stringify({ connection: conn, table_name: tableName }) });
      setColumns(data.columns || []); setSampleData(data.sample_data || []);
      const stdMaps = [], custMaps = [];
      for (const s of (data.suggested_mapping || [])) {
        if (s.target.startsWith("custom_fields.")) custMaps.push({ source: s.source, target: s.target.replace("custom_fields.", ""), confidence: s.confidence });
        else stdMaps.push({ source: s.source, target: s.target, confidence: s.confidence });
      }
      setMappings(stdMaps); setCustomMappings(custMaps); setStep(3);
    } catch (err) { setError(err.message); }
    setLoading(false);
  };

  const handlePreview = async () => {
    setLoading(true); setError("");
    try {
      const fMaps = mappings.filter(m => m.target).map(m => ({ source: m.source, target: m.target }));
      const cMaps = customMappings.filter(m => m.target).map(m => ({ source: m.source, target: m.target }));
      const data = await api("/mapping/preview", { method: "POST", body: JSON.stringify({ connection: conn, source_table: selectedTable, field_mappings: fMaps, custom_field_mappings: cMaps, value_mappings: valueMappings, limit: 5 }) });
      setPreview(data.preview || []); setStep(4);
    } catch (err) { setError(err.message); }
    setLoading(false);
  };

  const handleImport = async () => {
    if (!confirm("Lancer l'import ? Les contacts seront ajoutés/mis à jour dans Orkestra.")) return;
    setLoading(true); setError("");
    try {
      const fMaps = mappings.filter(m => m.target).map(m => ({ source: m.source, target: m.target }));
      const cMaps = customMappings.filter(m => m.target).map(m => ({ source: m.source, target: m.target }));
      const result = await api("/mapping/import", { method: "POST", body: JSON.stringify({ name: `Import ${selectedTable}`, connection: conn, source_table: selectedTable, field_mappings: fMaps, custom_field_mappings: cMaps, value_mappings: valueMappings }) });
      setImportResult(result); setStep(5);
    } catch (err) { setError(err.message); }
    setLoading(false);
  };

  const handleSaveMapping = async () => {
    try {
      const fMaps = mappings.filter(m => m.target).map(m => ({ source: m.source, target: m.target }));
      const cMaps = customMappings.filter(m => m.target).map(m => ({ source: m.source, target: m.target }));
      await api("/mapping/save", { method: "POST", body: JSON.stringify({ name: `${conn.database} / ${selectedTable}`, connection: conn, source_table: selectedTable, field_mappings: fMaps, custom_field_mappings: cMaps, value_mappings: valueMappings }) });
      alert("Mapping sauvegardé !");
    } catch (err) { alert("Erreur: " + err.message); }
  };

  const updateMapping = (idx, field, value) => { const m = [...mappings]; m[idx] = { ...m[idx], [field]: value }; setMappings(m); };
  const confColor = (c) => c === "high" ? "bg-emerald-100 text-emerald-700" : c === "medium" ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-500";
  const steps = [{ n: 1, label: "Connexion" }, { n: 2, label: "Table" }, { n: 3, label: "Mapping" }, { n: 4, label: "Preview" }, { n: 5, label: "Import" }];

  return (
    <div className="p-8">
      <div className="mb-6"><h2 className="text-xl font-bold text-slate-900">Mapping de données</h2><p className="text-sm text-slate-400 mt-1">Connectez une base externe et mappez les champs vers Orkestra</p></div>
      <div className="flex items-center gap-2 mb-8">{steps.map((s, i) => (<div key={s.n} className="flex items-center gap-2"><div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${step >= s.n ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-400"}`}>{s.n}</div><span className={`text-sm ${step >= s.n ? "text-slate-700 font-medium" : "text-slate-400"}`}>{s.label}</span>{i < steps.length - 1 && <div className={`w-12 h-0.5 ${step > s.n ? "bg-slate-900" : "bg-slate-200"}`} />}</div>))}</div>
      {error && <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 text-red-700 text-sm">{error}<button onClick={() => setError("")} className="ml-4 text-red-400 hover:text-red-600">✕</button></div>}

      {step === 1 && (<div className="bg-white rounded-2xl border border-slate-100 p-6 max-w-2xl"><h3 className="text-base font-bold text-slate-900 mb-4">Connexion à la base source</h3><div className="space-y-4">
        <div><label className="text-sm font-medium text-slate-700 mb-1 block">Type de base</label><select value={conn.db_type} onChange={e => setConn({...conn, db_type: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400"><option value="mssql">SQL Server / Azure SQL</option><option value="postgresql">PostgreSQL</option><option value="mysql">MySQL</option></select></div>
        <div className="grid grid-cols-3 gap-4"><div className="col-span-2"><label className="text-sm font-medium text-slate-700 mb-1 block">Hôte</label><input value={conn.host} onChange={e => setConn({...conn, host: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div><div><label className="text-sm font-medium text-slate-700 mb-1 block">Port</label><input type="number" value={conn.port} onChange={e => setConn({...conn, port: parseInt(e.target.value)})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div></div>
        <div className="grid grid-cols-2 gap-4"><div><label className="text-sm font-medium text-slate-700 mb-1 block">Utilisateur</label><input value={conn.username} onChange={e => setConn({...conn, username: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div><div><label className="text-sm font-medium text-slate-700 mb-1 block">Mot de passe</label><input type="password" value={conn.password} onChange={e => setConn({...conn, password: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div></div>
        <div><label className="text-sm font-medium text-slate-700 mb-1 block">Base de données</label><input value={conn.database} onChange={e => setConn({...conn, database: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
        <button onClick={handleConnect} disabled={loading} className="px-6 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800 disabled:opacity-50">{loading ? "Connexion..." : "Se connecter"}</button>
      </div></div>)}

      {step === 2 && (<div className="bg-white rounded-2xl border border-slate-100 p-6"><div className="flex items-center justify-between mb-4"><h3 className="text-base font-bold text-slate-900">Sélectionner une table ({tables.length})</h3><button onClick={() => setStep(1)} className="text-sm text-sky-600">← Retour</button></div>
        <div className="grid grid-cols-3 gap-3">{tables.map(t => (<button key={t.full_name} onClick={() => handleSelectTable(t.full_name)} className="text-left p-4 border border-slate-200 rounded-xl hover:border-sky-400 hover:bg-sky-50/30 transition-all"><div className="text-sm font-medium text-slate-800">{t.name}</div><div className="text-xs text-slate-400">{t.schema} · {t.type}</div></button>))}</div></div>)}

      {step === 3 && (<div className="bg-white rounded-2xl border border-slate-100 p-6"><div className="flex items-center justify-between mb-4"><div><h3 className="text-base font-bold text-slate-900">Mapping — {selectedTable}</h3><p className="text-xs text-slate-400 mt-1">Mapping auto-suggéré. Modifiez si nécessaire.</p></div><div className="flex gap-2"><button onClick={() => setStep(2)} className="text-sm text-sky-600">← Retour</button><button onClick={handleSaveMapping} className="px-3 py-1.5 border border-slate-200 text-slate-600 rounded-lg text-xs font-medium hover:bg-slate-50">Sauvegarder</button></div></div>
        <div className="overflow-x-auto mb-6"><table className="w-full"><thead><tr className="border-b border-slate-100"><th className="text-left text-xs font-medium text-slate-400 pb-3 w-1/3">Source</th><th className="text-center text-xs font-medium text-slate-400 pb-3 w-16">→</th><th className="text-left text-xs font-medium text-slate-400 pb-3 w-1/3">Orkestra</th><th className="text-left text-xs font-medium text-slate-400 pb-3">Auto</th></tr></thead>
        <tbody>{mappings.map((m, idx) => (<tr key={idx} className="border-b border-slate-50"><td className="py-2.5 text-sm font-mono text-slate-700">{m.source}</td><td className="py-2.5 text-center text-slate-300">→</td><td className="py-2.5"><select value={m.target} onChange={e => updateMapping(idx, "target", e.target.value)} className="w-full border border-slate-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-sky-400"><option value="">— Ignorer —</option>{targetFields.map(f => <option key={f.name} value={f.name}>{f.label} ({f.name})</option>)}</select></td><td className="py-2.5"><span className={`text-xs px-2 py-0.5 rounded-full ${confColor(m.confidence)}`}>{m.confidence === "high" ? "Auto" : m.confidence === "medium" ? "Suggéré" : "Manuel"}</span></td></tr>))}</tbody></table></div>
        {customMappings.length > 0 && (<div className="mb-6"><h4 className="text-sm font-bold text-slate-700 mb-2">Champs personnalisés (→ custom_fields)</h4>{customMappings.map((m, idx) => (<div key={idx} className="flex items-center gap-3 mb-2"><span className="text-sm font-mono text-slate-600 w-1/3">{m.source}</span><span className="text-slate-300">→</span><input value={m.target} onChange={e => { const c = [...customMappings]; c[idx] = {...c[idx], target: e.target.value}; setCustomMappings(c); }} className="flex-1 border border-slate-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-sky-400" /></div>))}</div>)}
        {sampleData.length > 0 && (<div className="mb-6"><h4 className="text-sm font-bold text-slate-700 mb-2">Aperçu source (5 lignes)</h4><div className="overflow-x-auto border border-slate-100 rounded-xl"><table className="w-full text-xs"><thead><tr className="bg-slate-50">{Object.keys(sampleData[0]).map(k => <th key={k} className="text-left p-2 font-medium text-slate-500">{k}</th>)}</tr></thead><tbody>{sampleData.map((row, i) => <tr key={i} className="border-t border-slate-50">{Object.values(row).map((v, j) => <td key={j} className="p-2 text-slate-600 truncate max-w-[150px]">{v || "—"}</td>)}</tr>)}</tbody></table></div></div>)}
        <button onClick={handlePreview} disabled={loading} className="px-6 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800 disabled:opacity-50">{loading ? "Chargement..." : "Prévisualiser →"}</button>
      </div>)}

      {step === 4 && (<div className="bg-white rounded-2xl border border-slate-100 p-6"><div className="flex items-center justify-between mb-4"><div><h3 className="text-base font-bold text-slate-900">Preview — {preview.length} lignes</h3><p className="text-xs text-slate-400 mt-1">Données transformées telles qu'elles apparaîtront dans Orkestra</p></div><button onClick={() => setStep(3)} className="text-sm text-sky-600">← Modifier</button></div>
        <div className="overflow-x-auto border border-slate-100 rounded-xl mb-6"><table className="w-full text-sm"><thead><tr className="bg-slate-50">{preview.length > 0 && Object.keys(preview[0]).filter(k => k !== "custom_fields").map(k => <th key={k} className="text-left p-3 text-xs font-medium text-slate-500">{k}</th>)}{preview.length > 0 && preview[0].custom_fields && <th className="text-left p-3 text-xs font-medium text-slate-500">custom_fields</th>}</tr></thead>
        <tbody>{preview.map((row, i) => (<tr key={i} className="border-t border-slate-50">{Object.entries(row).filter(([k]) => k !== "custom_fields").map(([k, v], j) => <td key={j} className="p-3 text-slate-700">{v || "—"}</td>)}{row.custom_fields && <td className="p-3 text-xs text-slate-500 font-mono">{JSON.stringify(row.custom_fields)}</td>}</tr>))}</tbody></table></div>
        <div className="flex gap-3"><button onClick={() => setStep(3)} className="px-6 py-2.5 border border-slate-200 text-slate-600 rounded-xl text-sm font-medium hover:bg-slate-50">Modifier</button><button onClick={handleImport} disabled={loading} className="px-6 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-500 disabled:opacity-50">{loading ? "Import..." : "Lancer l'import"}</button></div>
      </div>)}

      {step === 5 && importResult && (<div className="bg-white rounded-2xl border border-slate-100 p-6 max-w-2xl"><h3 className="text-base font-bold text-slate-900 mb-4">Import terminé</h3>
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-emerald-50 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-emerald-700">{importResult.imported}</div><div className="text-xs text-emerald-600">Importés</div></div>
          <div className="bg-amber-50 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-amber-700">{importResult.updated}</div><div className="text-xs text-amber-600">Mis à jour</div></div>
          <div className="bg-red-50 rounded-xl p-4 text-center"><div className="text-2xl font-bold text-red-700">{importResult.skipped}</div><div className="text-xs text-red-600">Ignorés</div></div>
        </div>
        <p className="text-sm text-slate-500 mb-4">Total : {importResult.total_processed} lignes</p>
        <div className="flex gap-3"><button onClick={() => { setStep(1); setImportResult(null); }} className="px-6 py-2.5 border border-slate-200 text-slate-600 rounded-xl text-sm font-medium hover:bg-slate-50">Nouvel import</button></div>
      </div>)}

      {savedMappings.length > 0 && step === 1 && (<div className="mt-8 bg-white rounded-2xl border border-slate-100 p-6"><h3 className="text-sm font-bold text-slate-700 mb-3">Mappings sauvegardés</h3><div className="space-y-2">{savedMappings.map(m => (<div key={m.id} className="flex items-center justify-between p-3 border border-slate-100 rounded-xl"><div><div className="text-sm font-medium text-slate-800">{m.name}</div><div className="text-xs text-slate-400">{m.connection_host} · {m.field_mappings?.length || 0} champs</div></div></div>))}</div></div>)}
    </div>
  );
}



// ══════════════════════════════════════════════════════════
// DIFFUSION PAGE
// ══════════════════════════════════════════════════════════

function DiffusionPage() {
  const [config, setConfig] = useState({ smtp: {}, whatsapp: {}, sms: {} });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("email");
  const [smtpForm, setSmtpForm] = useState({ host: "smtp.gmail.com", port: 587, username: "", password: "", use_tls: true, from_email: "", from_name: "OS Orkestra" });
  const [whatsappForm, setWhatsappForm] = useState({ api_token: "", phone_number_id: "" });
  const [smsForm, setSmsForm] = useState({ provider: "twilio", api_key: "", api_secret: "", from_number: "" });
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [actionResult, setActionResult] = useState(null);
  const [testEmail, setTestEmail] = useState("");
  const [sendingTest, setSendingTest] = useState(false);
  const [sendResult, setSendResult] = useState(null);
  const [testPhone, setTestPhone] = useState("");
  const [sendingWa, setSendingWa] = useState(false);
  const [waTestResult, setWaTestResult] = useState(null);

  useEffect(() => {
    api("/diffusion/config").then(d => {
      setConfig(d || {});
      // Pré-remplir les formulaires avec la config sauvée
      if (d?.smtp && d.smtp.status !== "not_configured") {
        setSmtpForm(prev => ({
          ...prev,
          host: d.smtp.host || prev.host,
          port: d.smtp.port || prev.port,
          username: d.smtp.username || prev.username,
          password: "", // Ne jamais pré-remplir le mot de passe (masqué côté API)
          use_tls: d.smtp.use_tls !== undefined ? d.smtp.use_tls : prev.use_tls,
          from_email: d.smtp.from_email || prev.from_email,
          from_name: d.smtp.from_name || prev.from_name,
        }));
      }
      if (d?.whatsapp && d.whatsapp.status !== "not_configured") {
        setWhatsappForm(prev => ({
          ...prev,
          phone_number_id: d.whatsapp.phone_number_id || prev.phone_number_id,
        }));
      }
      if (d?.sms && d.sms.status !== "not_configured") {
        setSmsForm(prev => ({
          ...prev,
          provider: d.sms.provider || prev.provider,
          from_number: d.sms.from_number || prev.from_number,
        }));
      }
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const reloadConfig = async () => {
    try { const d = await api("/diffusion/config"); setConfig(d || {}); } catch {}
  };

  const saveSmtp = async () => {
    setSaving(true); setActionResult(null);
    try {
      await api("/diffusion/config/smtp", { method: "POST", body: JSON.stringify(smtpForm) });
      await reloadConfig();
      setActionResult({ success: true, message: "Configuration SMTP sauvegardée" });
    } catch (err) { setActionResult({ success: false, message: err.message }); }
    setSaving(false);
  };

  const testSmtp = async () => {
    setTesting(true); setActionResult(null);
    try {
      const r = await api("/diffusion/test-smtp", { method: "POST" });
      await reloadConfig();
      setActionResult(r);
    } catch (err) { setActionResult({ success: false, message: err.message }); }
    setTesting(false);
  };

  const sendTestEmail = async () => {
    if (!testEmail) return alert("Entrez un email");
    setSendingTest(true); setSendResult(null);
    try {
      const r = await api("/diffusion/send-test-email", { method: "POST", body: JSON.stringify({ to_email: testEmail, subject: "Test OS Orkestra", body: "Ceci est un email de test. Si vous le recevez, la configuration SMTP fonctionne !" }) });
      setSendResult(r);
    } catch (err) { setSendResult({ success: false, message: err.message }); }
    setSendingTest(false);
  };

  const saveWhatsapp = async () => {
    setSaving(true); setActionResult(null);
    try {
      await api("/diffusion/config/whatsapp", { method: "POST", body: JSON.stringify(whatsappForm) });
      await reloadConfig();
      setActionResult({ success: true, message: "WhatsApp configuré" });
    } catch (err) { setActionResult({ success: false, message: err.message }); }
    setSaving(false);
  };

  const sendTestWhatsapp = async () => {
    if (!testPhone.trim()) { setWaTestResult({ success: false, message: "Entrez un numéro" }); return; }
    setSendingWa(true); setWaTestResult(null);
    try {
      const r = await api("/whatsapp/send-test", { method: "POST", body: JSON.stringify({ to_phone: testPhone.trim() }) });
      setWaTestResult(r);
    } catch (err) { setWaTestResult({ success: false, message: err.message }); }
    setSendingWa(false);
  };

  const saveSms = async () => {
    setSaving(true); setActionResult(null);
    try {
      await api("/diffusion/config/sms", { method: "POST", body: JSON.stringify(smsForm) });
      await reloadConfig();
      setActionResult({ success: true, message: "SMS configuré" });
    } catch (err) { setActionResult({ success: false, message: err.message }); }
    setSaving(false);
  };

  const getStatus = (key) => {
    const c = config[key];
    if (!c || c.status === "not_configured") return { label: "Non configuré", color: "bg-slate-100 text-slate-500", dot: "bg-slate-300" };
    if (c.status === "connected") return { label: "Connecté", color: "bg-emerald-50 text-emerald-700", dot: "bg-emerald-500" };
    if (c.status === "configured") return { label: "Configuré", color: "bg-sky-50 text-sky-700", dot: "bg-sky-500" };
    if (c.status === "error") return { label: "Erreur", color: "bg-red-50 text-red-700", dot: "bg-red-500" };
    return { label: c.status || "—", color: "bg-slate-100 text-slate-500", dot: "bg-slate-300" };
  };

  const tabs = [
    { id: "email", label: "Email (SMTP)", icon: Mail, configKey: "smtp" },
    { id: "whatsapp", label: "WhatsApp", icon: Send, configKey: "whatsapp" },
    { id: "sms", label: "SMS", icon: Radio, configKey: "sms" },
  ];

  if (loading) return <div className="p-8 text-center text-slate-400">Chargement...</div>;

  return (
    <div className="p-8">
      <div className="mb-6"><h2 className="text-xl font-bold text-slate-900">Diffusion</h2><p className="text-sm text-slate-400 mt-1">Configurez vos canaux d'envoi</p></div>

      {/* Bandeau statut */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {tabs.map(t => {
          const Icon = t.icon;
          const st = getStatus(t.configKey);
          const c = config[t.configKey] || {};
          return (
            <div key={t.id} className={`rounded-2xl border p-4 ${activeTab === t.id ? "border-slate-300 bg-white shadow-sm" : "border-slate-100 bg-white"}`}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2"><Icon size={16} className="text-slate-500" /><span className="text-sm font-medium text-slate-700">{t.label}</span></div>
                <span className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${st.color}`}><span className={`w-1.5 h-1.5 rounded-full ${st.dot}`}/>{st.label}</span>
              </div>
              {c.host && <div className="text-xs text-slate-400">{c.host}{c.port ? `:${c.port}` : ""}</div>}
              {c.username && <div className="text-xs text-slate-400 truncate">{c.username}</div>}
              {c.phone_number_id && <div className="text-xs text-slate-400">ID: {c.phone_number_id}</div>}
              {c.last_tested && <div className="text-xs text-slate-300 mt-1">Testé: {new Date(c.last_tested).toLocaleString("fr-FR")}</div>}
              {c.configured_at && !c.last_tested && <div className="text-xs text-slate-300 mt-1">Configuré: {new Date(c.configured_at).toLocaleString("fr-FR")}</div>}
            </div>
          );
        })}
      </div>

      <div className="flex gap-3 mb-6">{tabs.map(t => { const Icon = t.icon; return (
        <button key={t.id} onClick={() => { setActiveTab(t.id); setActionResult(null); setSendResult(null); }} className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${activeTab === t.id ? "bg-slate-900 text-white" : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"}`}>
          <Icon size={16}/>{t.label}
        </button>);})}</div>

      {activeTab === "email" && (
        <div className="bg-white rounded-2xl border border-slate-100 p-6 max-w-2xl">
          <h3 className="text-base font-bold text-slate-900 mb-4">Configuration SMTP</h3>
          {config.smtp?.status && config.smtp.status !== "not_configured" && (
            <div className="bg-sky-50 border border-sky-100 rounded-xl p-3 text-sm text-sky-700 mb-4">Configuration existante détectée — modifiez les champs si nécessaire. Laissez le mot de passe vide pour garder l'ancien.</div>
          )}
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2"><label className="text-sm font-medium text-slate-700 mb-1 block">Serveur SMTP</label><input value={smtpForm.host} onChange={e => setSmtpForm({...smtpForm, host: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
              <div><label className="text-sm font-medium text-slate-700 mb-1 block">Port</label><input type="number" value={smtpForm.port} onChange={e => setSmtpForm({...smtpForm, port: parseInt(e.target.value) || 587})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="text-sm font-medium text-slate-700 mb-1 block">Email / Login</label><input value={smtpForm.username} onChange={e => setSmtpForm({...smtpForm, username: e.target.value})} placeholder="votre@gmail.com" className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
              <div><label className="text-sm font-medium text-slate-700 mb-1 block">Mot de passe / App Password</label><input type="password" value={smtpForm.password} onChange={e => setSmtpForm({...smtpForm, password: e.target.value})} placeholder={config.smtp?.status !== "not_configured" ? "••••••• (inchangé)" : ""} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="text-sm font-medium text-slate-700 mb-1 block">Email expéditeur</label><input value={smtpForm.from_email} onChange={e => setSmtpForm({...smtpForm, from_email: e.target.value})} placeholder="noreply@opensid.com" className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
              <div><label className="text-sm font-medium text-slate-700 mb-1 block">Nom expéditeur</label><input value={smtpForm.from_name} onChange={e => setSmtpForm({...smtpForm, from_name: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
            </div>
            <div className="flex items-center gap-2"><input type="checkbox" checked={smtpForm.use_tls} onChange={e => setSmtpForm({...smtpForm, use_tls: e.target.checked})} className="rounded" /><label className="text-sm text-slate-600">Utiliser TLS (recommandé)</label></div>

            {actionResult && <div className={`rounded-xl p-3 text-sm ${actionResult.success ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-700 border border-red-200"}`}>{actionResult.success ? "✓ " : "✗ "}{actionResult.message}</div>}

            <div className="flex gap-3">
              <button onClick={saveSmtp} disabled={saving} className="px-5 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800 disabled:opacity-50">{saving ? "..." : "Sauvegarder"}</button>
              <button onClick={testSmtp} disabled={testing} className="px-5 py-2.5 border border-slate-200 text-slate-700 rounded-xl text-sm font-medium hover:bg-slate-50 disabled:opacity-50">{testing ? "Test..." : "Tester la connexion"}</button>
            </div>

            <div className="border-t border-slate-100 pt-4 mt-4">
              <h4 className="text-sm font-bold text-slate-700 mb-3">Envoyer un email de test</h4>
              <div className="flex gap-3">
                <input value={testEmail} onChange={e => setTestEmail(e.target.value)} placeholder="votre@email.com" className="flex-1 border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" />
                <button onClick={sendTestEmail} disabled={sendingTest} className="px-5 py-2.5 bg-sky-600 text-white rounded-xl text-sm font-medium hover:bg-sky-500 disabled:opacity-50">{sendingTest ? "Envoi..." : "Envoyer"}</button>
              </div>
              {sendResult && <div className={`rounded-xl p-3 text-sm mt-3 ${sendResult.success ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-700 border border-red-200"}`}>{sendResult.success ? "✓ " : "✗ "}{sendResult.message}</div>}
            </div>
          </div>
        </div>
      )}

      {activeTab === "whatsapp" && (
        <div className="bg-white rounded-2xl border border-slate-100 p-6 max-w-2xl">
          <h3 className="text-base font-bold text-slate-900 mb-4">WhatsApp Business API</h3>
          <p className="text-sm text-slate-400 mb-4">Nécessite un compte Meta Business avec l'API WhatsApp activée.</p>
          <div className="space-y-4">
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">API Token (Meta)</label><input type="password" value={whatsappForm.api_token} onChange={e => setWhatsappForm({...whatsappForm, api_token: e.target.value})} placeholder={config.whatsapp?.status !== "not_configured" ? "••••••• (inchangé)" : ""} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Phone Number ID</label><input value={whatsappForm.phone_number_id} onChange={e => setWhatsappForm({...whatsappForm, phone_number_id: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
            {actionResult && activeTab === "whatsapp" && <div className={`rounded-xl p-3 text-sm ${actionResult.success ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-700 border border-red-200"}`}>{actionResult.success ? "✓ " : "✗ "}{actionResult.message}</div>}
            <button onClick={saveWhatsapp} disabled={saving} className="px-5 py-2.5 bg-green-600 text-white rounded-xl text-sm font-medium hover:bg-green-500 disabled:opacity-50">{saving ? "..." : "Sauvegarder"}</button>

            <div className="border-t border-slate-100 pt-4 mt-4">
              <h4 className="text-sm font-bold text-slate-700 mb-2">Envoyer un message test</h4>
              <p className="text-xs text-slate-400 mb-3">Envoie le template <code className="bg-slate-100 px-1 rounded">hello_world</code> (requis par Meta pour initier une conversation).</p>
              <div className="flex gap-3">
                <input value={testPhone} onChange={e => setTestPhone(e.target.value)} placeholder="+33612345678" className="flex-1 border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" />
                <button onClick={sendTestWhatsapp} disabled={sendingWa || !testPhone.trim()} className="px-5 py-2.5 bg-green-600 text-white rounded-xl text-sm font-medium hover:bg-green-500 disabled:opacity-50">{sendingWa ? "Envoi..." : "Envoyer"}</button>
              </div>
              {waTestResult && <div className={`rounded-xl p-3 text-sm mt-3 ${waTestResult.success ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-700 border border-red-200"}`}>{waTestResult.success ? "✓ " : "✗ "}{waTestResult.message}</div>}
            </div>
          </div>
        </div>
      )}

      {activeTab === "sms" && (
        <div className="bg-white rounded-2xl border border-slate-100 p-6 max-w-2xl">
          <h3 className="text-base font-bold text-slate-900 mb-4">Configuration SMS</h3>
          <div className="space-y-4">
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Fournisseur</label><select value={smsForm.provider} onChange={e => setSmsForm({...smsForm, provider: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400"><option value="twilio">Twilio</option><option value="vonage">Vonage</option></select></div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="text-sm font-medium text-slate-700 mb-1 block">API Key</label><input type="password" value={smsForm.api_key} onChange={e => setSmsForm({...smsForm, api_key: e.target.value})} placeholder={config.sms?.status !== "not_configured" ? "••••••• (inchangé)" : ""} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
              <div><label className="text-sm font-medium text-slate-700 mb-1 block">API Secret</label><input type="password" value={smsForm.api_secret} onChange={e => setSmsForm({...smsForm, api_secret: e.target.value})} placeholder={config.sms?.status !== "not_configured" ? "••••••• (inchangé)" : ""} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
            </div>
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Numéro expéditeur</label><input value={smsForm.from_number} onChange={e => setSmsForm({...smsForm, from_number: e.target.value})} placeholder="+33612345678" className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
            {actionResult && activeTab === "sms" && <div className={`rounded-xl p-3 text-sm ${actionResult.success ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-700 border border-red-200"}`}>{actionResult.success ? "✓ " : "✗ "}{actionResult.message}</div>}
            <button onClick={saveSms} disabled={saving} className="px-5 py-2.5 bg-amber-600 text-white rounded-xl text-sm font-medium hover:bg-amber-500 disabled:opacity-50">{saving ? "..." : "Sauvegarder"}</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// TEMPLATES EDITOR
// ══════════════════════════════════════════════════════════

function TemplatesPage() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [editing, setEditing] = useState(false);
  const [htmlContent, setHtmlContent] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ name: "", subject: "", category: "newsletter", html_content: "<html>\n<body>\n  <h1>Bonjour {{first_name}}</h1>\n  <p>Votre message ici</p>\n</body>\n</html>" });
  const [saving, setSaving] = useState(false);

  useEffect(() => { loadTemplates(); }, []);

  const loadTemplates = async () => {
    try { const data = await api("/templates/"); setTemplates(data || []); } catch (e) { console.error(e); }
    setLoading(false);
  };

  const selectTemplate = async (tpl) => {
    try {
      const data = await api(`/templates/${tpl.id}`);
      setSelected(data);
      setHtmlContent(data.html_content || "");
      setEditing(false);
    } catch (e) { console.error(e); }
  };

  const saveTemplate = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      await api(`/templates/${selected.id}`, { method: "PUT", body: JSON.stringify({ html_content: htmlContent }) });
      setSelected({ ...selected, html_content: htmlContent });
      setEditing(false);
      loadTemplates();
    } catch (e) { alert("Erreur: " + e.message); }
    setSaving(false);
  };

  const createTemplate = async () => {
    setSaving(true);
    try {
      await api("/templates/", { method: "POST", body: JSON.stringify(createForm) });
      setShowCreate(false);
      setCreateForm({ name: "", subject: "", category: "newsletter", html_content: "<html>\n<body>\n  <h1>Bonjour {{first_name}}</h1>\n  <p>Votre message ici</p>\n</body>\n</html>" });
      loadTemplates();
    } catch (e) { alert("Erreur: " + e.message); }
    setSaving(false);
  };

  const deleteTemplate = async (id) => {
    if (!confirm("Supprimer ce template ?")) return;
    try { await api(`/templates/${id}`, { method: "DELETE" }); setSelected(null); loadTemplates(); } catch (e) { alert("Erreur: " + e.message); }
  };

  if (loading) return <div className="p-8 text-center text-slate-400">Chargement...</div>;

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Templates email</h2>
          <p className="text-sm text-slate-400">{templates.length} template{templates.length > 1 ? "s" : ""}</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 px-4 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800"><Plus size={16}/>Nouveau template</button>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Liste templates */}
        <div className="col-span-4 space-y-2">
          {templates.map(tpl => (
            <div key={tpl.id} onClick={() => selectTemplate(tpl)} className={`p-4 rounded-2xl border cursor-pointer transition-all ${selected?.id === tpl.id ? "bg-sky-50 border-sky-200" : "bg-white border-slate-100 hover:border-slate-200"}`}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-slate-900 text-sm">{tpl.name}</div>
                  <div className="text-xs text-slate-400 mt-1">{tpl.subject}</div>
                </div>
                <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full">{tpl.category}</span>
              </div>
            </div>
          ))}
          {templates.length === 0 && <div className="text-center text-slate-400 text-sm py-8">Aucun template. Créez-en un !</div>}
        </div>

        {/* Éditeur + Preview */}
        <div className="col-span-8">
          {selected ? (
            <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
              <div className="flex items-center justify-between p-4 border-b border-slate-100 bg-slate-50">
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">{selected.name}</h3>
                  <p className="text-xs text-slate-400">{selected.subject}</p>
                </div>
                <div className="flex gap-2">
                  {editing ? (
                    <>
                      <button onClick={saveTemplate} disabled={saving} className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 text-white rounded-lg text-xs font-medium hover:bg-emerald-500 disabled:opacity-50"><Save size={14}/>{saving ? "..." : "Sauver"}</button>
                      <button onClick={() => { setHtmlContent(selected.html_content); setEditing(false); }} className="px-3 py-1.5 bg-slate-200 text-slate-600 rounded-lg text-xs font-medium hover:bg-slate-300">Annuler</button>
                    </>
                  ) : (
                    <>
                      <button onClick={() => setEditing(true)} className="flex items-center gap-1.5 px-3 py-1.5 bg-sky-600 text-white rounded-lg text-xs font-medium hover:bg-sky-500"><Edit3 size={14}/>Modifier</button>
                      <button onClick={() => deleteTemplate(selected.id)} className="flex items-center gap-1.5 px-3 py-1.5 bg-red-100 text-red-600 rounded-lg text-xs font-medium hover:bg-red-200"><Trash2 size={14}/></button>
                    </>
                  )}
                </div>
              </div>

              {editing ? (
                <div className="grid grid-cols-2 divide-x divide-slate-100" style={{ height: "500px" }}>
                  <div className="flex flex-col">
                    <div className="px-3 py-2 bg-slate-900 text-slate-300 text-xs font-mono flex items-center gap-2"><Code size={12}/>HTML</div>
                    <textarea value={htmlContent} onChange={e => setHtmlContent(e.target.value)} className="flex-1 p-4 font-mono text-xs text-slate-700 resize-none focus:outline-none bg-slate-50" spellCheck={false} />
                  </div>
                  <div className="flex flex-col">
                    <div className="px-3 py-2 bg-sky-600 text-white text-xs font-medium flex items-center gap-2"><Eye size={12}/>Preview</div>
                    <iframe srcDoc={htmlContent} className="flex-1 bg-white" title="preview" sandbox="" />
                  </div>
                </div>
              ) : (
                <div style={{ height: "500px" }}>
                  <iframe srcDoc={selected.html_content || "<p>Aucun contenu</p>"} className="w-full h-full bg-white" title="preview" sandbox="" />
                </div>
              )}

              <div className="p-3 border-t border-slate-100 bg-slate-50 text-xs text-slate-400">
                Variables disponibles : {"{{first_name}}, {{last_name}}, {{company}}, {{email}}"}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-slate-100 flex items-center justify-center" style={{ height: "500px" }}>
              <div className="text-center text-slate-400">
                <FileText size={48} className="mx-auto mb-3 opacity-30" />
                <p className="text-sm">Sélectionnez un template pour le visualiser ou le modifier</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modal création */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Nouveau template">
        <div className="space-y-4">
          <div><label className="text-sm font-medium text-slate-700 mb-1 block">Nom</label><input value={createForm.name} onChange={e => setCreateForm({...createForm, name: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" placeholder="Newsletter Avril" /></div>
          <div><label className="text-sm font-medium text-slate-700 mb-1 block">Objet</label><input value={createForm.subject} onChange={e => setCreateForm({...createForm, subject: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" placeholder="Découvrez nos offres {{first_name}}" /></div>
          <div><label className="text-sm font-medium text-slate-700 mb-1 block">Catégorie</label>
            <select value={createForm.category} onChange={e => setCreateForm({...createForm, category: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400">
              <option value="newsletter">Newsletter</option><option value="welcome">Bienvenue</option><option value="promo">Promotion</option><option value="event">Événement</option><option value="notification">Notification</option>
            </select>
          </div>
          <div><label className="text-sm font-medium text-slate-700 mb-1 block">Contenu HTML</label><textarea value={createForm.html_content} onChange={e => setCreateForm({...createForm, html_content: e.target.value})} rows={8} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-mono focus:outline-none focus:border-sky-400" /></div>
          <button onClick={createTemplate} disabled={saving || !createForm.name} className="w-full py-2.5 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800 disabled:opacity-50">{saving ? "Création..." : "Créer le template"}</button>
        </div>
      </Modal>
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// IMPORT CSV
// ══════════════════════════════════════════════════════════

function ImportCSVPage() {
  const [step, setStep] = useState(1);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [mapping, setMapping] = useState({});
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const uploadPreview = async () => {
    if (!file) return;
    setError("");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const token = localStorage.getItem("orkestra_token");
      const res = await fetch(`${API}/import/csv/preview`, { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: formData });
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail || "Erreur upload"); }
      const data = await res.json();
      setPreview(data);
      setMapping(data.mapping_suggestions || {});
      setStep(2);
    } catch (e) { setError(e.message); }
  };

  const executeImport = async () => {
    if (!file) return;
    setImporting(true); setError("");
    const formData = new FormData();
    formData.append("file", file);
    formData.append("mapping_json", JSON.stringify(mapping));
    try {
      const token = localStorage.getItem("orkestra_token");
      const res = await fetch(`${API}/import/csv/execute`, { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: formData });
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail || "Erreur import"); }
      const data = await res.json();
      setResult(data);
      setStep(3);
    } catch (e) { setError(e.message); }
    setImporting(false);
  };

  const reset = () => { setStep(1); setFile(null); setPreview(null); setMapping({}); setResult(null); setError(""); };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Import CSV</h2>
          <p className="text-sm text-slate-400">Importez vos contacts depuis un fichier CSV</p>
        </div>
        {step > 1 && <button onClick={reset} className="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-600 rounded-xl text-sm hover:bg-slate-200"><RefreshCw size={14}/>Recommencer</button>}
      </div>

      {/* Progress */}
      <div className="flex items-center gap-4 mb-8">
        {["Upload", "Mapping", "Résultat"].map((label, i) => (
          <div key={i} className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${step > i + 1 ? "bg-emerald-500 text-white" : step === i + 1 ? "bg-sky-600 text-white" : "bg-slate-100 text-slate-400"}`}>{step > i + 1 ? "✓" : i + 1}</div>
            <span className={`text-sm ${step === i + 1 ? "text-slate-900 font-medium" : "text-slate-400"}`}>{label}</span>
            {i < 2 && <div className="w-12 h-px bg-slate-200" />}
          </div>
        ))}
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-3 text-sm mb-4">{error}</div>}

      {/* Step 1: Upload */}
      {step === 1 && (
        <div className="bg-white rounded-2xl border border-slate-100 p-8 max-w-xl">
          <div className="border-2 border-dashed border-slate-200 rounded-2xl p-8 text-center hover:border-sky-300 transition-colors">
            <Upload size={40} className="mx-auto mb-3 text-slate-300" />
            <p className="text-sm text-slate-600 mb-4">Glissez votre fichier CSV ici ou cliquez pour parcourir</p>
            <input type="file" accept=".csv" onChange={e => setFile(e.target.files[0])} className="block mx-auto text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-medium file:bg-sky-50 file:text-sky-600 hover:file:bg-sky-100" />
          </div>
          {file && (
            <div className="mt-4 flex items-center justify-between">
              <span className="text-sm text-slate-600">{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
              <button onClick={uploadPreview} className="px-5 py-2.5 bg-sky-600 text-white rounded-xl text-sm font-medium hover:bg-sky-500">Analyser</button>
            </div>
          )}
        </div>
      )}

      {/* Step 2: Mapping */}
      {step === 2 && preview && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-100 p-6">
            <h3 className="text-base font-bold text-slate-900 mb-4">Mapping des colonnes</h3>
            <p className="text-sm text-slate-400 mb-4">{preview.total_columns} colonnes détectées dans {preview.filename}</p>
            <div className="space-y-3">
              {preview.columns.map(col => (
                <div key={col} className="flex items-center gap-4">
                  <div className="w-48 text-sm font-mono text-slate-600 bg-slate-50 px-3 py-2 rounded-lg truncate">{col}</div>
                  <span className="text-slate-300">→</span>
                  <select value={mapping[col] || ""} onChange={e => setMapping({...mapping, [col]: e.target.value})} className="flex-1 border border-slate-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-sky-400">
                    <option value="">— Ignorer —</option>
                    {preview.orkestra_fields.map(f => <option key={f} value={f}>{f}</option>)}
                  </select>
                </div>
              ))}
            </div>
          </div>

          {/* Preview data */}
          <div className="bg-white rounded-2xl border border-slate-100 p-6">
            <h3 className="text-base font-bold text-slate-900 mb-4">Aperçu des données</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="bg-slate-50">{preview.columns.map(c => <th key={c} className="px-3 py-2 text-left font-medium text-slate-600 text-xs">{c}</th>)}</tr></thead>
                <tbody>{preview.preview_rows.map((row, i) => <tr key={i} className="border-t border-slate-50">{preview.columns.map(c => <td key={c} className="px-3 py-2 text-slate-700 text-xs">{row[c]}</td>)}</tr>)}</tbody>
              </table>
            </div>
          </div>

          <button onClick={executeImport} disabled={importing || !Object.values(mapping).some(v => v)} className="px-6 py-3 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800 disabled:opacity-50">{importing ? "Import en cours..." : "Importer les contacts"}</button>
        </div>
      )}

      {/* Step 3: Result */}
      {step === 3 && result && (
        <div className="bg-white rounded-2xl border border-slate-100 p-8 max-w-xl">
          <div className="text-center mb-6">
            <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4"><span className="text-3xl">✓</span></div>
            <h3 className="text-lg font-bold text-slate-900">Import terminé</h3>
          </div>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="text-center p-4 bg-emerald-50 rounded-xl"><div className="text-2xl font-bold text-emerald-700">{result.imported}</div><div className="text-xs text-emerald-600 mt-1">Importés</div></div>
            <div className="text-center p-4 bg-amber-50 rounded-xl"><div className="text-2xl font-bold text-amber-700">{result.skipped}</div><div className="text-xs text-amber-600 mt-1">Ignorés</div></div>
            <div className="text-center p-4 bg-red-50 rounded-xl"><div className="text-2xl font-bold text-red-700">{result.errors?.length || 0}</div><div className="text-xs text-red-600 mt-1">Erreurs</div></div>
          </div>
          {result.errors?.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-xs text-red-600 mb-4">{result.errors.map((e, i) => <div key={i}>{e}</div>)}</div>
          )}
          <button onClick={reset} className="w-full py-2.5 bg-sky-600 text-white rounded-xl text-sm font-medium hover:bg-sky-500">Nouvel import</button>
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// SYNC CRM (Write-back)
// ══════════════════════════════════════════════════════════

function SyncCRMPage() {
  const [tab, setTab] = useState("config");
  const [loading, setLoading] = useState(true);
  const [config, setConfig] = useState(null);
  const [preview, setPreview] = useState(null);
  const [logs, setLogs] = useState([]);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [isDirty, setIsDirty] = useState(false);

  const [form, setForm] = useState({
    host: "osmdm-server.database.windows.net",
    port: 1433,
    username: "",
    password: "",
    database: "CRM-Test",
    table: "Clients",
    key_field: "ClientID",
  });

  const [mapping, setMapping] = useState([
    { orkestra_field: "lead_score", crm_field: "Score" },
    { orkestra_field: "lead_stage", crm_field: "Etape" },
    { orkestra_field: "status", crm_field: "Statut" },
  ]);

  const orkestraFields = ["email", "first_name", "last_name", "company", "phone", "country", "city", "job_title", "lead_score", "lead_stage", "status"];
  const IDENT_RE = /^[A-Za-z_][A-Za-z0-9_]{0,63}$/;

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [cfg, prev, lg] = await Promise.all([
        api("/sync/config").catch(() => null),
        api("/sync/preview?limit=10").catch(() => null),
        api("/sync/logs?limit=10").catch(() => null),
      ]);
      setConfig(cfg);
      setPreview(prev);
      setLogs(lg?.logs || []);
      if (cfg && cfg.host) {
        setForm(p => ({ ...p, host: cfg.host || p.host, port: cfg.port || p.port, username: cfg.username || p.username, database: cfg.database || p.database, table: cfg.table || p.table, key_field: cfg.key_field || p.key_field }));
        if (Array.isArray(cfg.field_mapping) && cfg.field_mapping.length > 0) setMapping(cfg.field_mapping);
      }
      setIsDirty(false);
    } catch {}
    setLoading(false);
  };

  const updateForm = (patch) => { setForm(f => ({ ...f, ...patch })); setIsDirty(true); };

  const validateConfig = () => {
    if (!IDENT_RE.test(form.table)) return "Nom de table invalide (alphanumérique + _ uniquement)";
    if (!IDENT_RE.test(form.key_field)) return "Clé primaire invalide (alphanumérique + _ uniquement)";
    const seen = new Set();
    for (const m of mapping) {
      if (!m.orkestra_field || !m.crm_field) continue;
      if (seen.has(m.orkestra_field)) return `Champ Orkestra en doublon : ${m.orkestra_field}`;
      seen.add(m.orkestra_field);
      if (!IDENT_RE.test(m.crm_field)) return `Nom de champ CRM invalide : ${m.crm_field}`;
    }
    return null;
  };

  const saveConfig = async () => {
    setTestResult(null);
    const err = validateConfig();
    if (err) { setTestResult({ success: false, message: err }); return; }
    try {
      await api("/sync/config", {
        method: "POST",
        body: JSON.stringify({
          config: form,
          field_mapping: mapping.filter(m => m.orkestra_field && m.crm_field),
        }),
      });
      setTestResult({ success: true, message: "Configuration sauvegardée" });
      await loadData();
    } catch (e) { setTestResult({ success: false, message: e.message }); }
  };

  const testConnection = async () => {
    setTestResult(null);
    if (isDirty) {
      setTestResult({ success: false, message: "Sauvegardez d'abord la configuration avant de tester." });
      return;
    }
    try {
      const r = await api("/sync/test", { method: "POST" });
      setTestResult(r);
    } catch (e) { setTestResult({ success: false, message: e.message }); }
  };

  const executeSync = async () => {
    setSyncing(true); setSyncResult(null);
    try {
      const r = await api("/sync/execute", { method: "POST" });
      setSyncResult(r);
      await loadData();
    } catch (e) { setSyncResult({ success: false, message: e.message }); }
    setSyncing(false);
  };

  const addMapping = () => { setMapping(m => [...m, { orkestra_field: "", crm_field: "" }]); setIsDirty(true); };
  const removeMapping = (i) => { setMapping(m => m.filter((_, idx) => idx !== i)); setIsDirty(true); };
  const updateMapping = (i, field, value) => {
    setMapping(m => m.map((row, idx) => idx === i ? { ...row, [field]: value } : row));
    setIsDirty(true);
  };

  const switchTab = (id) => { setTab(id); setTestResult(null); setSyncResult(null); };

  if (loading) return <div className="p-8 text-center text-slate-400">Chargement...</div>;

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Sync CRM</h2>
          <p className="text-sm text-slate-400">Synchronisez les données Orkestra vers votre CRM</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-3 mb-6">
        {[
          { id: "config", label: "Configuration", icon: Database },
          { id: "preview", label: "Preview", icon: Eye },
          { id: "sync", label: "Synchroniser", icon: ArrowLeftRight },
          { id: "logs", label: "Historique", icon: Clock },
        ].map(t => {
          const Icon = t.icon;
          return (
            <button key={t.id} onClick={() => switchTab(t.id)} className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${tab === t.id ? "bg-slate-900 text-white" : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"}`}>
              <Icon size={16} />{t.label}
            </button>
          );
        })}
      </div>

      {/* Config */}
      {tab === "config" && (
        <div className="space-y-6 max-w-2xl">
          <div className="bg-white rounded-2xl border border-slate-100 p-6">
            <h3 className="text-base font-bold text-slate-900 mb-4">Connexion CRM cible</h3>
            {config && config.status !== "not_configured" && (
              <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-sm text-emerald-700 mb-4 flex items-center gap-2"><CheckCircle size={16} />Configuration existante détectée</div>
            )}
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="col-span-2"><label className="text-sm font-medium text-slate-700 mb-1 block">Serveur</label><input value={form.host} onChange={e => updateForm({ host: e.target.value })} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
                <div><label className="text-sm font-medium text-slate-700 mb-1 block">Port</label><input type="number" value={form.port} onChange={e => updateForm({ port: parseInt(e.target.value) || 1433 })} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><label className="text-sm font-medium text-slate-700 mb-1 block">Utilisateur</label><input value={form.username} onChange={e => updateForm({ username: e.target.value })} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
                <div><label className="text-sm font-medium text-slate-700 mb-1 block">Mot de passe</label><input type="password" value={form.password} onChange={e => updateForm({ password: e.target.value })} placeholder={config && config.status !== "not_configured" ? "••••••• (inchangé)" : ""} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div><label className="text-sm font-medium text-slate-700 mb-1 block">Base de données</label><input value={form.database} onChange={e => updateForm({ database: e.target.value })} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
                <div><label className="text-sm font-medium text-slate-700 mb-1 block">Table</label><input value={form.table} onChange={e => updateForm({ table: e.target.value })} pattern="[A-Za-z_][A-Za-z0-9_]*" className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
                <div><label className="text-sm font-medium text-slate-700 mb-1 block">Clé primaire CRM</label><input value={form.key_field} onChange={e => updateForm({ key_field: e.target.value })} pattern="[A-Za-z_][A-Za-z0-9_]*" className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-100 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-slate-900">Mapping des champs</h3>
              <button onClick={addMapping} className="flex items-center gap-1 text-sm text-sky-600 hover:text-sky-500"><Plus size={14} />Ajouter</button>
            </div>
            <p className="text-sm text-slate-400 mb-4">Choisissez quels champs Orkestra sont envoyés vers quels champs CRM</p>
            <div className="space-y-3">
              {mapping.map((m, i) => (
                <div key={i} className="flex items-center gap-3">
                  <select value={m.orkestra_field} onChange={e => updateMapping(i, "orkestra_field", e.target.value)} className="flex-1 border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-sky-400">
                    <option value="">— Champ Orkestra —</option>
                    {orkestraFields.map(f => <option key={f} value={f}>{f}</option>)}
                  </select>
                  <span className="text-slate-300">→</span>
                  <input value={m.crm_field} onChange={e => updateMapping(i, "crm_field", e.target.value)} placeholder="Champ CRM" className="flex-1 border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-sky-400" />
                  <button onClick={() => removeMapping(i)} className="p-2 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg"><Trash2 size={14} /></button>
                </div>
              ))}
            </div>
          </div>

          {testResult && <div className={`rounded-xl p-3 text-sm ${testResult.success ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-700 border border-red-200"}`}>{testResult.success ? "✓ " : "✗ "}{testResult.message}</div>}

          <div className="flex gap-3">
            <button onClick={saveConfig} className="px-5 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800">Sauvegarder</button>
            <button onClick={testConnection} className="px-5 py-2.5 border border-slate-200 text-slate-700 rounded-xl text-sm font-medium hover:bg-slate-50">Tester la connexion</button>
          </div>
        </div>
      )}

      {/* Preview */}
      {tab === "preview" && (
        <div className="bg-white rounded-2xl border border-slate-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Contacts à synchroniser</h3>
              <p className="text-sm text-slate-400">{preview?.total_syncable || 0} contacts avec un ID CRM externe</p>
            </div>
            <button onClick={loadData} className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700"><RefreshCw size={14} />Rafraîchir</button>
          </div>
          {preview?.preview?.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="bg-slate-50">
                  <th className="px-3 py-2 text-left font-medium text-slate-600 text-xs">Email</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600 text-xs">Nom</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600 text-xs">Entreprise</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600 text-xs">Score</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600 text-xs">Stage</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600 text-xs">Statut</th>
                  <th className="px-3 py-2 text-left font-medium text-slate-600 text-xs">CRM ID</th>
                </tr></thead>
                <tbody>
                  {preview.preview.map((c, i) => (
                    <tr key={i} className="border-t border-slate-50">
                      <td className="px-3 py-2 text-slate-700">{c.email}</td>
                      <td className="px-3 py-2 text-slate-700">{c.first_name} {c.last_name}</td>
                      <td className="px-3 py-2 text-slate-500">{c.company}</td>
                      <td className="px-3 py-2"><span className="bg-sky-50 text-sky-700 px-2 py-0.5 rounded-full text-xs font-medium">{c.lead_score}</span></td>
                      <td className="px-3 py-2 text-slate-500 text-xs">{c.lead_stage}</td>
                      <td className="px-3 py-2 text-slate-500 text-xs">{c.status}</td>
                      <td className="px-3 py-2 text-slate-400 text-xs font-mono">{c.external_crm_id && (c.external_crm_id.length > 12 ? c.external_crm_id.slice(0, 12) + "…" : c.external_crm_id)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center text-slate-400 py-8">
              <AlertCircle size={32} className="mx-auto mb-2 opacity-30" />
              <p className="text-sm">Aucun contact avec un ID CRM externe. Importez d'abord des contacts via le Mapping DB.</p>
            </div>
          )}
        </div>
      )}

      {/* Sync */}
      {tab === "sync" && (
        <div className="max-w-xl">
          <div className="bg-white rounded-2xl border border-slate-100 p-6">
            <h3 className="text-base font-bold text-slate-900 mb-2">Lancer la synchronisation</h3>
            <p className="text-sm text-slate-400 mb-6">Les données modifiées dans Orkestra seront envoyées vers le CRM cible via le mapping configuré.</p>

            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-700 mb-6">
              <div className="font-medium mb-1">Attention</div>
              Cette action va modifier les données dans votre CRM. Vérifiez la preview avant de lancer.
            </div>

            <div className="flex items-center gap-4 mb-6 p-4 bg-slate-50 rounded-xl">
              <div className="text-center flex-1">
                <div className="text-2xl font-bold text-slate-900">{preview?.total_syncable || 0}</div>
                <div className="text-xs text-slate-500">Contacts à sync</div>
              </div>
              <ArrowLeftRight size={20} className="text-slate-300" />
              <div className="text-center flex-1">
                <div className="text-sm font-medium text-slate-700">{form.database}</div>
                <div className="text-xs text-slate-500">{form.table}</div>
              </div>
            </div>

            {syncResult && (
              <div className={`rounded-xl p-4 text-sm mb-4 ${syncResult.errors === 0 || syncResult.status === "completed" ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-amber-50 text-amber-700 border border-amber-200"}`}>
                <div className="font-medium mb-1">{syncResult.message}</div>
                {syncResult.duration_seconds && <div className="text-xs opacity-70">Durée : {syncResult.duration_seconds}s</div>}
                {syncResult.error_details?.length > 0 && (
                  <div className="mt-2 text-xs">{syncResult.error_details.map((e, i) => <div key={i}>{e}</div>)}</div>
                )}
              </div>
            )}

            <button onClick={executeSync} disabled={syncing || !preview?.total_syncable} className="w-full py-3 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800 disabled:opacity-50 flex items-center justify-center gap-2">
              {syncing ? <><Loader2 size={16} className="animate-spin" />Synchronisation en cours...</> : <><ArrowLeftRight size={16} />Synchroniser {preview?.total_syncable || 0} contacts</>}
            </button>
          </div>
        </div>
      )}

      {/* Logs */}
      {tab === "logs" && (
        <div className="bg-white rounded-2xl border border-slate-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-bold text-slate-900">Historique des synchronisations</h3>
            <button onClick={loadData} className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700"><RefreshCw size={14} />Rafraîchir</button>
          </div>
          {logs.length > 0 ? (
            <div className="space-y-3">
              {logs.map((log, i) => (
                <div key={i} className="flex items-center justify-between p-4 border border-slate-100 rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${log.error_count === 0 ? "bg-emerald-50" : "bg-amber-50"}`}>
                      {log.error_count === 0 ? <CheckCircle size={16} className="text-emerald-600" /> : <AlertCircle size={16} className="text-amber-600" />}
                    </div>
                    <div>
                      <div className="text-sm font-medium text-slate-700">{log.source}</div>
                      <div className="text-xs text-slate-400">{log.direction === "orkestra_to_crm" ? "Orkestra → CRM" : log.direction}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-slate-700">{log.success_count}/{log.total_records} contacts</div>
                    <div className="text-xs text-slate-400">{log.started_at ? new Date(log.started_at).toLocaleString("fr-FR") : "—"} · {log.duration_seconds ? `${log.duration_seconds}s` : ""}</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-slate-400 py-8">
              <Clock size={32} className="mx-auto mb-2 opacity-30" />
              <p className="text-sm">Aucune synchronisation effectuée</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════
// AI ASSISTANT (O.S ✦)
// ══════════════════════════════════════════════════════════

// Rendu markdown minimal : **gras**, listes (-, *, 1.), sauts de ligne préservés
function renderMarkdown(text) {
  const lines = text.split("\n");
  const out = [];
  let listBuffer = [];
  const flushList = () => {
    if (listBuffer.length) {
      out.push(<ul key={`ul-${out.length}`} className="list-disc pl-5 my-1 space-y-0.5">{listBuffer}</ul>);
      listBuffer = [];
    }
  };
  const formatInline = (s) => {
    const parts = s.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((p, i) => p.startsWith("**") && p.endsWith("**")
      ? <strong key={i}>{p.slice(2, -2)}</strong>
      : <span key={i}>{p}</span>);
  };
  lines.forEach((line, i) => {
    const m = line.match(/^\s*(?:[-*]|\d+\.)\s+(.*)$/);
    if (m) {
      listBuffer.push(<li key={`li-${i}`}>{formatInline(m[1])}</li>);
    } else {
      flushList();
      if (line.trim() === "") out.push(<div key={i} className="h-2" />);
      else out.push(<div key={i}>{formatInline(line)}</div>);
    }
  });
  flushList();
  return out;
}

function AIAssistant() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Bonjour ! Je suis l'assistant IA d'Orkestra. Je peux vous aider à gérer vos contacts, campagnes, segments et templates. Que voulez-vous faire ?" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, loading, open]);

  const sendText = async (text) => {
    const userMsg = (text || "").trim();
    if (!userMsg || loading) return;
    setInput("");
    setLoading(true);

    // Construit l'historique : skip welcome, filtre content vide,
    // s'assure que le premier message est 'user' (Anthropic l'exige)
    let payloadMessages = [];
    setMessages(prev => {
      const history = prev
        .slice(1)
        .filter(m => m.content && m.content.trim())
        .map(m => ({ role: m.role, content: m.content }));
      // Drop les messages de tête tant que ce n'est pas 'user'
      while (history.length && history[0].role !== "user") history.shift();
      payloadMessages = [...history, { role: "user", content: userMsg }];
      return [...prev, { role: "user", content: userMsg }];
    });

    try {
      const data = await api("/ai/chat", {
        method: "POST",
        body: JSON.stringify({ messages: payloadMessages }),
      });
      const aiReply = data?.reply || "Désolé, je n'ai pas pu traiter votre demande.";
      setMessages(prev => [...prev, { role: "assistant", content: aiReply }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "assistant", content: "Erreur : " + (err.message || "Connexion impossible") }]);
    }
    setLoading(false);
  };

  const sendMessage = () => sendText(input);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  return (
    <>
      {/* Bouton flottant O.S Rainbow */}
      <button
        onClick={() => setOpen(!open)}
        aria-label={open ? "Fermer l'assistant IA" : "Ouvrir l'assistant IA"}
        aria-expanded={open}
        className="fixed bottom-6 right-6 z-50 group"
        style={{ outline: "none" }}
      >
        <div style={{
          padding: "3px",
          borderRadius: "999px",
          background: open ? "transparent" : "linear-gradient(135deg, #ec4899, #8b5cf6, #06b6d4, #10b981)",
          boxShadow: open ? "none" : "0 0 24px rgba(139,92,246,0.25), 0 0 48px rgba(236,72,153,0.15)",
          transition: "all 0.3s ease",
        }}>
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: open ? "12px" : "12px 22px",
            borderRadius: "999px",
            background: open ? "#ef4444" : "#1e293b",
            cursor: "pointer",
            transition: "all 0.3s ease",
          }}>
            {open ? (
              <X size={20} color="white" />
            ) : (
              <>
                <span style={{ color: "white", fontWeight: 700, fontSize: "16px", letterSpacing: "-0.5px" }}>O.S</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.582a.5.5 0 0 1 0 .963L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" fill="rgba(255,255,255,0.9)"/>
                  <path d="M20 3v3" stroke="rgba(255,255,255,0.6)" strokeWidth="1.5" strokeLinecap="round"/>
                  <path d="M21.5 4.5h-3" stroke="rgba(255,255,255,0.6)" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
              </>
            )}
          </div>
        </div>
      </button>

      {/* Panneau chat */}
      {open && (
        <div className="fixed bottom-24 right-6 z-50 w-96 bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col" style={{ height: "520px" }}>
          {/* Header */}
          <div className="flex items-center gap-3 p-4 border-b border-slate-100">
            <div style={{
              padding: "2px",
              borderRadius: "999px",
              background: "linear-gradient(135deg, #ec4899, #8b5cf6, #06b6d4, #10b981)",
            }}>
              <div style={{
                display: "flex",
                alignItems: "center",
                gap: "4px",
                padding: "4px 10px",
                borderRadius: "999px",
                background: "#1e293b",
              }}>
                <span style={{ color: "white", fontWeight: 700, fontSize: "11px" }}>O.S</span>
                <svg width="10" height="10" viewBox="0 0 24 24" fill="rgba(255,255,255,0.9)"><path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.582a.5.5 0 0 1 0 .963L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/></svg>
              </div>
            </div>
            <div>
              <div className="text-sm font-bold text-slate-900">Assistant IA</div>
              <div className="text-xs text-slate-400">Powered by OpenSID</div>
            </div>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3" id="ai-chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
                  msg.role === "user"
                    ? "bg-slate-900 text-white rounded-br-md"
                    : "bg-slate-100 text-slate-700 rounded-bl-md"
                }`}>
                  {msg.role === "assistant" ? renderMarkdown(msg.content) : msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-slate-100 rounded-2xl rounded-bl-md px-4 py-3 flex items-center gap-2">
                  <Loader2 size={14} className="animate-spin text-slate-400" />
                  <span className="text-sm text-slate-400">Réflexion...</span>
                </div>
              </div>
            )}
          </div>

          {/* Suggestions rapides */}
          {messages.length <= 1 && (
            <div className="px-4 pb-2 flex flex-wrap gap-2">
              {[
                "Combien de contacts actifs ?",
                "Liste mes campagnes",
                "Crée un segment VIP",
                "Résumé analytics 30j",
              ].map((s, i) => (
                <button key={i} onClick={() => sendText(s)} disabled={loading} className="text-xs bg-slate-50 border border-slate-200 text-slate-600 px-3 py-1.5 rounded-full hover:bg-slate-100 disabled:opacity-50 transition-colors">{s}</button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="p-3 border-t border-slate-100">
            <div className="flex gap-2">
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Demandez à l'IA..."
                className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400"
                disabled={loading}
              />
              <button
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                aria-label="Envoyer le message"
                className="px-3 py-2.5 bg-slate-900 text-white rounded-xl hover:bg-slate-800 disabled:opacity-30 transition-colors"
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ══════════════════════════════════════════════════════════
// MAIN APP
// ══════════════════════════════════════════════════════════

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem("orkestra_token"));
  const [activeNav, setActiveNav] = useState("dashboard");
  if (!isLoggedIn) return <LoginPage onLogin={() => setIsLoggedIn(true)} />;

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "contacts", label: "Contacts", icon: Users },
    { id: "campaigns", label: "Campagnes", icon: Send },
    { id: "segments", label: "Segments", icon: Target },
    { id: "templates", label: "Templates", icon: FileText },
    { id: "analytics", label: "Analytics", icon: BarChart3 },
    { id: "import", label: "Import CSV", icon: Upload },
    { id: "mapping", label: "Mapping DB", icon: Layers },
    { id: "sync", label: "Sync CRM", icon: ArrowLeftRight },
    { id: "diffusion", label: "Diffusion", icon: Radio },
    { id: "integrations", label: "Intégrations", icon: Link2 },
  ];

  const pages = { dashboard: DashboardPage, contacts: ContactsPage, campaigns: CampaignsPage, segments: SegmentsPage, templates: TemplatesPage, analytics: AnalyticsPage, integrations: IntegrationsPage, mapping: MappingPage, diffusion: DiffusionPage, import: ImportCSVPage, sync: SyncCRMPage };
  const Page = pages[activeNav];

  return (
    <div className="min-h-screen bg-slate-50 flex" style={{ fontFamily: "'Outfit', system-ui" }}>
      <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      <aside className="w-64 bg-slate-900 min-h-screen flex flex-col fixed left-0 top-0 z-30">
        <div className="p-5 border-b border-slate-800"><div className="flex items-center gap-2.5"><div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-400 to-blue-600 flex items-center justify-center"><span className="text-white font-bold text-sm">OS</span></div><div><div className="text-white font-bold text-base tracking-tight">Orkestra</div><div className="text-sky-400/50 text-[10px] uppercase tracking-[0.2em]">by OpenSID</div></div></div></div>
        <nav className="flex-1 py-4 px-3">{navItems.map(item => { const Icon = item.icon; const isActive = activeNav === item.id; return (<button key={item.id} onClick={() => setActiveNav(item.id)} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl mb-0.5 text-sm transition-all ${isActive ? "bg-sky-500/15 text-sky-400 font-medium" : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"}`}><Icon size={18}/>{item.label}</button>); })}</nav>
        <div className="p-4 border-t border-slate-800"><button onClick={() => { localStorage.removeItem("orkestra_token"); setIsLoggedIn(false); }} className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-red-400 hover:bg-red-500/10"><LogOut size={16}/>Déconnexion</button></div>
      </aside>
      <main className="flex-1 ml-64">
        <header className="sticky top-0 z-20 bg-white/80 backdrop-blur-xl border-b border-slate-100"><div className="flex items-center justify-between px-8 py-4"><div><h1 className="text-xl font-bold text-slate-900 capitalize">{activeNav}</h1><p className="text-sm text-slate-400 mt-0.5">Données en temps réel</p></div></div></header>
        {Page ? <Page /> : <div className="p-8 flex items-center justify-center h-96"><div className="text-center"><div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4"><Zap size={24} className="text-slate-400"/></div><h3 className="text-lg font-semibold text-slate-700">En construction</h3></div></div>}
        <div className="px-8 pb-6 mt-4 text-center text-xs text-slate-300">OS Orkestra v1.0.0 · © 2026 OpenSID</div>
      </main>
      <AIAssistant />
    </div>
  );
}
