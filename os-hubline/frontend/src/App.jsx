import { useState, useEffect, useCallback } from "react";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area } from "recharts";
import { Search, Bell, Settings, Users, Mail, BarChart3, Zap, Globe, Building2, ChevronDown, ArrowUpRight, ArrowDownRight, Activity, Send, Eye, MousePointerClick, AlertTriangle, CheckCircle, RefreshCw, Filter, Plus, LayoutDashboard, Target, Database, Link2 } from "lucide-react";

// ══════════════════════════════════════════════════════════
// MOCK DATA
// ══════════════════════════════════════════════════════════

const campaignData = [
  { month: "Sep", envoyés: 34200, ouverts: 14100, cliqués: 4800 },
  { month: "Oct", envoyés: 38500, ouverts: 16200, cliqués: 5600 },
  { month: "Nov", envoyés: 42100, ouverts: 18900, cliqués: 6300 },
  { month: "Dec", envoyés: 35800, ouverts: 15400, cliqués: 5100 },
  { month: "Jan", envoyés: 44200, ouverts: 20100, cliqués: 7200 },
  { month: "Feb", envoyés: 48600, ouverts: 22400, cliqués: 8100 },
  { month: "Mar", envoyés: 51300, ouverts: 24800, cliqués: 9400 },
];

const leadFunnelData = [
  { name: "Awareness", value: 42500, fill: "#0f172a" },
  { name: "Interest", value: 18200, fill: "#1e3a5f" },
  { name: "Considération", value: 8400, fill: "#2563eb" },
  { name: "Achat", value: 3200, fill: "#3b82f6" },
  { name: "Rétention", value: 2100, fill: "#60a5fa" },
];

const channelData = [
  { name: "Email", value: 72, color: "#1e3a5f" },
  { name: "Interne", value: 18, color: "#3b82f6" },
  { name: "WhatsApp", value: 7, color: "#22c55e" },
  { name: "SMS", value: 3, color: "#f59e0b" },
];

const recentCampaigns = [
  { id: 1, name: "Newsletter Mars 2026", type: "external", status: "running", sent: 12400, openRate: 42.3, clickRate: 18.2, channel: "email" },
  { id: 2, name: "Info collaborateurs Q1", type: "internal", status: "completed", sent: 2840, openRate: 78.1, clickRate: 34.5, channel: "email" },
  { id: 3, name: "Offre spéciale Printemps", type: "external", status: "scheduled", sent: 0, openRate: 0, clickRate: 0, channel: "whatsapp" },
  { id: 4, name: "Webinar IA & Data", type: "external", status: "completed", sent: 8920, openRate: 51.2, clickRate: 22.8, channel: "email" },
  { id: 5, name: "Welcome Series - Nouveaux", type: "external", status: "running", sent: 3450, openRate: 65.8, clickRate: 28.4, channel: "email" },
];

const syncStatus = [
  { name: "Dynamics 365", status: "synced", lastSync: "il y a 23 min", records: 105160, icon: "crm" },
  { name: "Azure AD", status: "synced", lastSync: "il y a 2h", records: 4820, icon: "ad" },
  { name: "WhatsApp API", status: "connected", lastSync: "actif", records: null, icon: "wa" },
];

const dataQuality = { score: 87.4, emailValid: 96.2, fieldCompletion: 82.1, duplicates: 234, staleContacts: 1203 };

const scoreHistory = [
  { date: "Sep", score: 78 }, { date: "Oct", score: 80 }, { date: "Nov", score: 82 },
  { date: "Dec", score: 83 }, { date: "Jan", score: 85 }, { date: "Feb", score: 86 }, { date: "Mar", score: 87.4 },
];

// ══════════════════════════════════════════════════════════
// COMPONENTS
// ══════════════════════════════════════════════════════════

const StatusBadge = ({ status }) => {
  const styles = {
    running: "bg-emerald-50 text-emerald-700 border-emerald-200",
    completed: "bg-slate-100 text-slate-600 border-slate-200",
    scheduled: "bg-amber-50 text-amber-700 border-amber-200",
    draft: "bg-gray-50 text-gray-500 border-gray-200",
    paused: "bg-red-50 text-red-600 border-red-200",
  };
  const labels = { running: "En cours", completed: "Terminée", scheduled: "Planifiée", draft: "Brouillon", paused: "En pause" };
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[status] || styles.draft}`}>
      {labels[status] || status}
    </span>
  );
};

const ChannelIcon = ({ channel }) => {
  if (channel === "whatsapp") return <span className="text-green-500 text-sm font-bold">WA</span>;
  if (channel === "sms") return <span className="text-amber-500 text-sm font-bold">SMS</span>;
  return <Mail size={14} className="text-slate-400" />;
};

const MetricCard = ({ icon: Icon, label, value, change, changeType, subtitle }) => (
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
    <div className="text-2xl font-bold text-slate-900 tracking-tight">{value}</div>
    <div className="text-sm text-slate-500 mt-0.5">{label}</div>
    {subtitle && <div className="text-xs text-slate-400 mt-1">{subtitle}</div>}
  </div>
);

const SyncCard = ({ item }) => {
  const statusColor = item.status === "synced" ? "bg-emerald-500" : item.status === "connected" ? "bg-blue-500" : "bg-red-500";
  return (
    <div className="flex items-center justify-between py-3 border-b border-slate-50 last:border-0">
      <div className="flex items-center gap-3">
        <div className={`w-2 h-2 rounded-full ${statusColor}`} />
        <div>
          <div className="text-sm font-semibold text-slate-800">{item.name}</div>
          <div className="text-xs text-slate-400">{item.lastSync}</div>
        </div>
      </div>
      {item.records && (
        <div className="text-sm font-mono text-slate-600">{item.records.toLocaleString("fr-FR")}</div>
      )}
    </div>
  );
};

// ══════════════════════════════════════════════════════════
// MAIN DASHBOARD
// ══════════════════════════════════════════════════════════

export default function HubLineDashboard() {
  const [activeNav, setActiveNav] = useState("dashboard");
  const [searchOpen, setSearchOpen] = useState(false);

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "contacts", label: "Contacts", icon: Users },
    { id: "campaigns", label: "Campagnes", icon: Send },
    { id: "automation", label: "Automatisation", icon: Zap },
    { id: "segments", label: "Segments", icon: Target },
    { id: "analytics", label: "Analytics", icon: BarChart3 },
    { id: "integrations", label: "Intégrations", icon: Link2 },
    { id: "data", label: "Données", icon: Database },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex" style={{ fontFamily: "'DM Sans', system-ui, -apple-system, sans-serif" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&display=swap" rel="stylesheet" />

      {/* ── Sidebar ────────────────────────────────── */}
      <aside className="w-64 bg-slate-900 min-h-screen flex flex-col fixed left-0 top-0 z-30">
        <div className="p-5 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center">
              <span className="text-white font-bold text-sm">OS</span>
            </div>
            <div>
              <div className="text-white font-bold text-base tracking-tight">HubLine</div>
              <div className="text-slate-500 text-[10px] uppercase tracking-widest">by OpenSID</div>
            </div>
          </div>
        </div>

        <nav className="flex-1 py-4 px-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeNav === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveNav(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl mb-0.5 text-sm transition-all ${
                  isActive
                    ? "bg-blue-600/20 text-blue-400 font-medium"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Icon size={18} />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center gap-3 px-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-600 to-slate-700 flex items-center justify-center text-white text-xs font-bold">AD</div>
            <div className="flex-1 min-w-0">
              <div className="text-sm text-slate-200 font-medium truncate">Admin OpenSID</div>
              <div className="text-xs text-slate-500 truncate">admin@opensid.com</div>
            </div>
            <Settings size={16} className="text-slate-500" />
          </div>
        </div>
      </aside>

      {/* ── Main Content ───────────────────────────── */}
      <main className="flex-1 ml-64">
        {/* Header */}
        <header className="sticky top-0 z-20 bg-white/80 backdrop-blur-xl border-b border-slate-100">
          <div className="flex items-center justify-between px-8 py-4">
            <div>
              <h1 className="text-xl font-bold text-slate-900">Dashboard</h1>
              <p className="text-sm text-slate-400 mt-0.5">Vue d'ensemble de votre activité marketing</p>
            </div>
            <div className="flex items-center gap-3">
              <button className="w-9 h-9 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center hover:bg-slate-100 transition-colors">
                <Search size={16} className="text-slate-500" />
              </button>
              <button className="w-9 h-9 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center hover:bg-slate-100 transition-colors relative">
                <Bell size={16} className="text-slate-500" />
                <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-blue-500 rounded-full border-2 border-white" />
              </button>
              <button className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800 transition-colors">
                <Plus size={16} />
                Nouvelle campagne
              </button>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="p-8">
          {/* ── KPI Cards ─────────────────────────── */}
          <div className="grid grid-cols-4 gap-4 mb-8">
            <MetricCard icon={Users} label="Contacts totaux" value="109 980" change="+2.4%" changeType="up" subtitle="105 160 externes · 4 820 internes" />
            <MetricCard icon={Send} label="Emails envoyés (30j)" value="51 300" change="+5.6%" changeType="up" subtitle="129 campagnes actives" />
            <MetricCard icon={Eye} label="Taux d'ouverture" value="48.3%" change="+3.1%" changeType="up" subtitle="Moyenne 30 derniers jours" />
            <MetricCard icon={MousePointerClick} label="Taux de clic" value="18.3%" change="-0.8%" changeType="down" subtitle="Objectif : > 20%" />
          </div>

          {/* ── Charts Row 1 ─────────────────────── */}
          <div className="grid grid-cols-3 gap-4 mb-8">
            {/* Performance campagnes */}
            <div className="col-span-2 bg-white rounded-2xl border border-slate-100 p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-base font-bold text-slate-900">Performance des campagnes</h3>
                  <p className="text-xs text-slate-400 mt-0.5">Évolution sur 7 mois</p>
                </div>
                <div className="flex items-center gap-4 text-xs text-slate-500">
                  <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-slate-900" /> Envoyés</span>
                  <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-blue-500" /> Ouverts</span>
                  <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Cliqués</span>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={campaignData}>
                  <defs>
                    <linearGradient id="gradSent" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0f172a" stopOpacity={0.08} />
                      <stop offset="95%" stopColor="#0f172a" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gradOpened" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.12} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gradClicked" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#22c55e" stopOpacity={0.12} />
                      <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="month" tick={{ fontSize: 12, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 12, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", boxShadow: "0 4px 16px rgba(0,0,0,.06)", fontSize: 13 }} />
                  <Area type="monotone" dataKey="envoyés" stroke="#0f172a" strokeWidth={2} fill="url(#gradSent)" />
                  <Area type="monotone" dataKey="ouverts" stroke="#3b82f6" strokeWidth={2} fill="url(#gradOpened)" />
                  <Area type="monotone" dataKey="cliqués" stroke="#22c55e" strokeWidth={2} fill="url(#gradClicked)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Répartition canaux */}
            <div className="bg-white rounded-2xl border border-slate-100 p-6">
              <h3 className="text-base font-bold text-slate-900 mb-1">Canaux de communication</h3>
              <p className="text-xs text-slate-400 mb-4">Répartition des envois</p>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie data={channelData} dataKey="value" cx="50%" cy="50%" innerRadius={50} outerRadius={75} paddingAngle={3} strokeWidth={0}>
                    {channelData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: 12, fontSize: 13 }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 mt-2">
                {channelData.map((item) => (
                  <div key={item.name} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                      <span className="text-slate-600">{item.name}</span>
                    </div>
                    <span className="font-semibold text-slate-800">{item.value}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ── Row 2: Funnel + Integrations ──────── */}
          <div className="grid grid-cols-3 gap-4 mb-8">
            {/* Lead Funnel */}
            <div className="col-span-2 bg-white rounded-2xl border border-slate-100 p-6">
              <h3 className="text-base font-bold text-slate-900 mb-1">Funnel de conversion</h3>
              <p className="text-xs text-slate-400 mb-5">Répartition des contacts par étape du parcours</p>
              <div className="space-y-3">
                {leadFunnelData.map((stage, i) => {
                  const maxVal = leadFunnelData[0].value;
                  const pct = (stage.value / maxVal) * 100;
                  const convRate = i > 0 ? ((stage.value / leadFunnelData[i-1].value) * 100).toFixed(1) : "—";
                  return (
                    <div key={stage.name} className="flex items-center gap-4">
                      <div className="w-28 text-sm text-slate-600 font-medium">{stage.name}</div>
                      <div className="flex-1 bg-slate-50 rounded-full h-8 overflow-hidden">
                        <div className="h-full rounded-full flex items-center justify-end px-3 transition-all" style={{ width: `${Math.max(pct, 8)}%`, backgroundColor: stage.fill }}>
                          <span className="text-xs font-bold text-white">{stage.value.toLocaleString("fr-FR")}</span>
                        </div>
                      </div>
                      <div className="w-16 text-right text-xs text-slate-400">{convRate !== "—" ? `${convRate}%` : ""}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Intégrations + Data Quality */}
            <div className="space-y-4">
              {/* Sync Status */}
              <div className="bg-white rounded-2xl border border-slate-100 p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-bold text-slate-900">Intégrations</h3>
                  <button className="p-1 hover:bg-slate-50 rounded-lg transition-colors">
                    <RefreshCw size={14} className="text-slate-400" />
                  </button>
                </div>
                {syncStatus.map((item) => <SyncCard key={item.name} item={item} />)}
              </div>

              {/* Data Quality */}
              <div className="bg-white rounded-2xl border border-slate-100 p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-bold text-slate-900">Qualité des données</h3>
                  <span className={`text-lg font-bold ${dataQuality.score >= 85 ? "text-emerald-600" : dataQuality.score >= 70 ? "text-amber-600" : "text-red-600"}`}>
                    {dataQuality.score}%
                  </span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2 mb-4">
                  <div className="bg-emerald-500 h-2 rounded-full transition-all" style={{ width: `${dataQuality.score}%` }} />
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <div className="text-slate-400">Emails valides</div>
                    <div className="font-bold text-slate-800">{dataQuality.emailValid}%</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Complétion</div>
                    <div className="font-bold text-slate-800">{dataQuality.fieldCompletion}%</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Doublons</div>
                    <div className="font-bold text-amber-600">{dataQuality.duplicates}</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Obsolètes</div>
                    <div className="font-bold text-red-500">{dataQuality.staleContacts.toLocaleString("fr-FR")}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ── Campaigns Table ───────────────────── */}
          <div className="bg-white rounded-2xl border border-slate-100 p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="text-base font-bold text-slate-900">Campagnes récentes</h3>
                <p className="text-xs text-slate-400 mt-0.5">Dernières campagnes créées et en cours</p>
              </div>
              <div className="flex items-center gap-2">
                <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 transition-colors">
                  <Filter size={13} />
                  Filtrer
                </button>
                <button className="text-xs text-blue-600 font-medium hover:text-blue-700">
                  Voir tout →
                </button>
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
                    <th className="text-right text-xs font-medium text-slate-400 pb-3 uppercase tracking-wider">Taux ouv.</th>
                    <th className="text-right text-xs font-medium text-slate-400 pb-3 uppercase tracking-wider">Taux clic</th>
                  </tr>
                </thead>
                <tbody>
                  {recentCampaigns.map((c) => (
                    <tr key={c.id} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/50 transition-colors cursor-pointer">
                      <td className="py-3.5">
                        <div className="flex items-center gap-2.5">
                          <div className={`w-1.5 h-8 rounded-full ${c.type === "internal" ? "bg-blue-400" : "bg-slate-800"}`} />
                          <div>
                            <div className="text-sm font-medium text-slate-800">{c.name}</div>
                            <div className="text-xs text-slate-400">{c.type === "internal" ? "Interne" : "Externe"}</div>
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5"><ChannelIcon channel={c.channel} /></td>
                      <td className="py-3.5"><StatusBadge status={c.status} /></td>
                      <td className="py-3.5 text-right text-sm font-mono text-slate-700">{c.sent > 0 ? c.sent.toLocaleString("fr-FR") : "—"}</td>
                      <td className="py-3.5 text-right text-sm font-mono text-slate-700">{c.openRate > 0 ? `${c.openRate}%` : "—"}</td>
                      <td className="py-3.5 text-right text-sm font-mono text-slate-700">{c.clickRate > 0 ? `${c.clickRate}%` : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Footer */}
          <div className="mt-8 text-center text-xs text-slate-300">
            OS HubLine v1.0.0 · © 2026 OpenSID — Tous droits réservés
          </div>
        </div>
      </main>
    </div>
  );
}
