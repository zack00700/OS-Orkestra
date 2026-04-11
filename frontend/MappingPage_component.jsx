// ═══════════════════════════════════════════════════════
// MAPPING PAGE — Ajouter dans App.jsx
// 
// 1. Copie tout ce bloc dans App.jsx AVANT le "// MAIN APP"
// 2. Dans le navItems, ajoute : { id: "mapping", label: "Mapping", icon: Database }
// 3. Dans const pages, ajoute : mapping: MappingPage
// ═══════════════════════════════════════════════════════

function MappingPage() {
  const [step, setStep] = useState(1); // 1=connect, 2=tables, 3=mapping, 4=preview, 5=import
  const [conn, setConn] = useState({ db_type: "mssql", host: "osmdm-server.database.windows.net", port: 1433, username: "mdm-admin", password: "", database: "CRM-Test" });
  const [tables, setTables] = useState([]);
  const [selectedTable, setSelectedTable] = useState("");
  const [columns, setColumns] = useState([]);
  const [sampleData, setSampleData] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [mappings, setMappings] = useState([]);
  const [customMappings, setCustomMappings] = useState([]);
  const [valueMappings, setValueMappings] = useState({});
  const [preview, setPreview] = useState([]);
  const [targetFields, setTargetFields] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [importResult, setImportResult] = useState(null);
  const [savedMappings, setSavedMappings] = useState([]);

  // Load target fields and saved mappings on mount
  useEffect(() => {
    api("/mapping/target-fields").then(setTargetFields).catch(() => {});
    api("/mapping/saved").then(setSavedMappings).catch(() => {});
  }, []);

  // Step 1: Test connection & list tables
  const handleConnect = async () => {
    setLoading(true); setError("");
    try {
      const data = await api("/mapping/list-tables", { method: "POST", body: JSON.stringify(conn) });
      setTables(data.tables || []);
      setStep(2);
    } catch (err) { setError(err.message); }
    setLoading(false);
  };

  // Step 2: Get table schema
  const handleSelectTable = async (tableName) => {
    setSelectedTable(tableName); setLoading(true); setError("");
    try {
      const data = await api("/mapping/table-schema", {
        method: "POST",
        body: JSON.stringify({ connection: conn, table_name: tableName }),
      });
      setColumns(data.columns || []);
      setSampleData(data.sample_data || []);
      setSuggestions(data.suggested_mapping || []);

      // Initialiser les mappings depuis les suggestions
      const stdMaps = [];
      const custMaps = [];
      for (const s of (data.suggested_mapping || [])) {
        if (s.target.startsWith("custom_fields.")) {
          custMaps.push({ source: s.source, target: s.target.replace("custom_fields.", ""), confidence: s.confidence });
        } else {
          stdMaps.push({ source: s.source, target: s.target, confidence: s.confidence });
        }
      }
      setMappings(stdMaps);
      setCustomMappings(custMaps);
      setStep(3);
    } catch (err) { setError(err.message); }
    setLoading(false);
  };

  // Step 3→4: Preview
  const handlePreview = async () => {
    setLoading(true); setError("");
    try {
      const fMaps = mappings.filter(m => m.target).map(m => ({ source: m.source, target: m.target }));
      const cMaps = customMappings.filter(m => m.target).map(m => ({ source: m.source, target: m.target }));
      const data = await api("/mapping/preview", {
        method: "POST",
        body: JSON.stringify({
          connection: conn, source_table: selectedTable,
          field_mappings: fMaps, custom_field_mappings: cMaps,
          value_mappings: valueMappings, limit: 5,
        }),
      });
      setPreview(data.preview || []);
      setStep(4);
    } catch (err) { setError(err.message); }
    setLoading(false);
  };

  // Step 5: Import
  const handleImport = async () => {
    if (!confirm("Lancer l'import ? Les contacts seront ajoutés/mis à jour dans Orkestra.")) return;
    setLoading(true); setError("");
    try {
      const fMaps = mappings.filter(m => m.target).map(m => ({ source: m.source, target: m.target }));
      const cMaps = customMappings.filter(m => m.target).map(m => ({ source: m.source, target: m.target }));
      const result = await api("/mapping/import", {
        method: "POST",
        body: JSON.stringify({
          name: `Import ${selectedTable}`,
          connection: conn, source_table: selectedTable,
          field_mappings: fMaps, custom_field_mappings: cMaps,
          value_mappings: valueMappings,
        }),
      });
      setImportResult(result);
      setStep(5);
    } catch (err) { setError(err.message); }
    setLoading(false);
  };

  // Save mapping
  const handleSaveMapping = async () => {
    try {
      const fMaps = mappings.filter(m => m.target).map(m => ({ source: m.source, target: m.target }));
      const cMaps = customMappings.filter(m => m.target).map(m => ({ source: m.source, target: m.target }));
      await api("/mapping/save", {
        method: "POST",
        body: JSON.stringify({
          name: `${conn.database} / ${selectedTable}`,
          connection: conn, source_table: selectedTable,
          field_mappings: fMaps, custom_field_mappings: cMaps,
          value_mappings: valueMappings,
        }),
      });
      alert("Mapping sauvegardé !");
    } catch (err) { alert("Erreur: " + err.message); }
  };

  const updateMapping = (idx, field, value) => {
    const m = [...mappings]; m[idx] = { ...m[idx], [field]: value }; setMappings(m);
  };

  const confidenceColor = (c) => c === "high" ? "bg-emerald-100 text-emerald-700" : c === "medium" ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-500";

  // Step indicators
  const steps = [
    { n: 1, label: "Connexion" },
    { n: 2, label: "Table" },
    { n: 3, label: "Mapping" },
    { n: 4, label: "Preview" },
    { n: 5, label: "Import" },
  ];

  return (
    <div className="p-8">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-slate-900">Mapping de données</h2>
        <p className="text-sm text-slate-400 mt-1">Connectez une base externe et mappez les champs vers Orkestra</p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-2 mb-8">
        {steps.map((s, i) => (
          <div key={s.n} className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${step >= s.n ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-400"}`}>{s.n}</div>
            <span className={`text-sm ${step >= s.n ? "text-slate-700 font-medium" : "text-slate-400"}`}>{s.label}</span>
            {i < steps.length - 1 && <div className={`w-12 h-0.5 ${step > s.n ? "bg-slate-900" : "bg-slate-200"}`} />}
          </div>
        ))}
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 text-red-700 text-sm">{error}<button onClick={() => setError("")} className="ml-4 text-red-400 hover:text-red-600">✕</button></div>}

      {/* STEP 1: Connection */}
      {step === 1 && (
        <div className="bg-white rounded-2xl border border-slate-100 p-6 max-w-2xl">
          <h3 className="text-base font-bold text-slate-900 mb-4">Connexion à la base source</h3>
          <div className="space-y-4">
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Type de base</label>
              <select value={conn.db_type} onChange={e => setConn({...conn, db_type: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400">
                <option value="mssql">SQL Server / Azure SQL</option><option value="postgresql">PostgreSQL</option><option value="mysql">MySQL</option>
              </select></div>
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2"><label className="text-sm font-medium text-slate-700 mb-1 block">Hôte</label><input value={conn.host} onChange={e => setConn({...conn, host: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
              <div><label className="text-sm font-medium text-slate-700 mb-1 block">Port</label><input type="number" value={conn.port} onChange={e => setConn({...conn, port: parseInt(e.target.value)})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="text-sm font-medium text-slate-700 mb-1 block">Utilisateur</label><input value={conn.username} onChange={e => setConn({...conn, username: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
              <div><label className="text-sm font-medium text-slate-700 mb-1 block">Mot de passe</label><input type="password" value={conn.password} onChange={e => setConn({...conn, password: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
            </div>
            <div><label className="text-sm font-medium text-slate-700 mb-1 block">Base de données</label><input value={conn.database} onChange={e => setConn({...conn, database: e.target.value})} className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-sky-400" /></div>
            <button onClick={handleConnect} disabled={loading} className="px-6 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800 disabled:opacity-50">{loading ? "Connexion..." : "Se connecter"}</button>
          </div>
        </div>
      )}

      {/* STEP 2: Select table */}
      {step === 2 && (
        <div className="bg-white rounded-2xl border border-slate-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-bold text-slate-900">Sélectionner une table ({tables.length} trouvées)</h3>
            <button onClick={() => setStep(1)} className="text-sm text-sky-600 hover:text-sky-700">← Retour</button>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {tables.map(t => (
              <button key={t.full_name} onClick={() => handleSelectTable(t.full_name)}
                className="text-left p-4 border border-slate-200 rounded-xl hover:border-sky-400 hover:bg-sky-50/30 transition-all">
                <div className="text-sm font-medium text-slate-800">{t.name}</div>
                <div className="text-xs text-slate-400">{t.schema} · {t.type}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* STEP 3: Mapping */}
      {step === 3 && (
        <div className="bg-white rounded-2xl border border-slate-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Mapping des champs — {selectedTable}</h3>
              <p className="text-xs text-slate-400 mt-1">Le mapping automatique a été suggéré. Modifiez si nécessaire.</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => setStep(2)} className="text-sm text-sky-600 hover:text-sky-700">← Retour</button>
              <button onClick={handleSaveMapping} className="px-3 py-1.5 border border-slate-200 text-slate-600 rounded-lg text-xs font-medium hover:bg-slate-50">Sauvegarder le mapping</button>
            </div>
          </div>

          {/* Mapping table */}
          <div className="overflow-x-auto mb-6">
            <table className="w-full">
              <thead><tr className="border-b border-slate-100">
                <th className="text-left text-xs font-medium text-slate-400 pb-3 w-1/3">Colonne source</th>
                <th className="text-center text-xs font-medium text-slate-400 pb-3 w-16">→</th>
                <th className="text-left text-xs font-medium text-slate-400 pb-3 w-1/3">Champ Orkestra</th>
                <th className="text-left text-xs font-medium text-slate-400 pb-3">Confiance</th>
              </tr></thead>
              <tbody>
                {mappings.map((m, idx) => (
                  <tr key={idx} className="border-b border-slate-50">
                    <td className="py-2.5"><div className="flex items-center gap-2"><span className="text-sm font-mono text-slate-700">{m.source}</span></div></td>
                    <td className="py-2.5 text-center text-slate-300">→</td>
                    <td className="py-2.5">
                      <select value={m.target} onChange={e => updateMapping(idx, "target", e.target.value)} className="w-full border border-slate-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-sky-400">
                        <option value="">— Ignorer —</option>
                        {targetFields.map(f => <option key={f.name} value={f.name}>{f.label} ({f.name})</option>)}
                        <option value="__custom__">→ Champ personnalisé</option>
                      </select>
                    </td>
                    <td className="py-2.5"><span className={`text-xs px-2 py-0.5 rounded-full ${confidenceColor(m.confidence)}`}>{m.confidence === "high" ? "Auto" : m.confidence === "medium" ? "Suggéré" : "Manuel"}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Custom fields */}
          {customMappings.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-bold text-slate-700 mb-2">Champs personnalisés (→ custom_fields)</h4>
              {customMappings.map((m, idx) => (
                <div key={idx} className="flex items-center gap-3 mb-2">
                  <span className="text-sm font-mono text-slate-600 w-1/3">{m.source}</span>
                  <span className="text-slate-300">→</span>
                  <input value={m.target} onChange={e => { const c = [...customMappings]; c[idx] = {...c[idx], target: e.target.value}; setCustomMappings(c); }}
                    className="flex-1 border border-slate-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-sky-400" placeholder="nom_du_champ" />
                </div>
              ))}
            </div>
          )}

          {/* Sample data */}
          {sampleData.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-bold text-slate-700 mb-2">Aperçu des données source (5 lignes)</h4>
              <div className="overflow-x-auto border border-slate-100 rounded-xl">
                <table className="w-full text-xs">
                  <thead><tr className="bg-slate-50">{Object.keys(sampleData[0]).map(k => <th key={k} className="text-left p-2 font-medium text-slate-500">{k}</th>)}</tr></thead>
                  <tbody>{sampleData.map((row, i) => <tr key={i} className="border-t border-slate-50">{Object.values(row).map((v, j) => <td key={j} className="p-2 text-slate-600 truncate max-w-[150px]">{v || "—"}</td>)}</tr>)}</tbody>
                </table>
              </div>
            </div>
          )}

          <button onClick={handlePreview} disabled={loading} className="px-6 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800 disabled:opacity-50">
            {loading ? "Chargement..." : "Prévisualiser le résultat →"}
          </button>
        </div>
      )}

      {/* STEP 4: Preview */}
      {step === 4 && (
        <div className="bg-white rounded-2xl border border-slate-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Prévisualisation — {preview.length} lignes</h3>
              <p className="text-xs text-slate-400 mt-1">Voici comment les données apparaîtront dans Orkestra</p>
            </div>
            <button onClick={() => setStep(3)} className="text-sm text-sky-600 hover:text-sky-700">← Modifier le mapping</button>
          </div>

          <div className="overflow-x-auto border border-slate-100 rounded-xl mb-6">
            <table className="w-full text-sm">
              <thead><tr className="bg-slate-50">
                {preview.length > 0 && Object.keys(preview[0]).filter(k => k !== "custom_fields").map(k =>
                  <th key={k} className="text-left p-3 text-xs font-medium text-slate-500">{k}</th>
                )}
                {preview.length > 0 && preview[0].custom_fields && <th className="text-left p-3 text-xs font-medium text-slate-500">custom_fields</th>}
              </tr></thead>
              <tbody>
                {preview.map((row, i) => (
                  <tr key={i} className="border-t border-slate-50">
                    {Object.entries(row).filter(([k]) => k !== "custom_fields").map(([k, v], j) =>
                      <td key={j} className="p-3 text-slate-700">{v || "—"}</td>
                    )}
                    {row.custom_fields && <td className="p-3 text-xs text-slate-500 font-mono">{JSON.stringify(row.custom_fields)}</td>}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex gap-3">
            <button onClick={() => setStep(3)} className="px-6 py-2.5 border border-slate-200 text-slate-600 rounded-xl text-sm font-medium hover:bg-slate-50">Modifier le mapping</button>
            <button onClick={handleImport} disabled={loading} className="px-6 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-500 disabled:opacity-50">
              {loading ? "Import en cours..." : "Lancer l'import"}
            </button>
          </div>
        </div>
      )}

      {/* STEP 5: Result */}
      {step === 5 && importResult && (
        <div className="bg-white rounded-2xl border border-slate-100 p-6 max-w-2xl">
          <h3 className="text-base font-bold text-slate-900 mb-4">Import terminé</h3>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-emerald-50 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-emerald-700">{importResult.imported}</div>
              <div className="text-xs text-emerald-600">Importés</div>
            </div>
            <div className="bg-amber-50 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-amber-700">{importResult.updated}</div>
              <div className="text-xs text-amber-600">Mis à jour</div>
            </div>
            <div className="bg-red-50 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-red-700">{importResult.skipped}</div>
              <div className="text-xs text-red-600">Ignorés</div>
            </div>
          </div>
          <p className="text-sm text-slate-500 mb-4">Total traité : {importResult.total_processed} lignes</p>
          {importResult.errors && importResult.errors.length > 0 && (
            <div className="bg-red-50 rounded-xl p-3 mb-4">
              <h4 className="text-sm font-bold text-red-700 mb-2">Erreurs :</h4>
              {importResult.errors.slice(0, 5).map((e, i) => <div key={i} className="text-xs text-red-600">Ligne {e.row}: {e.error}</div>)}
            </div>
          )}
          <div className="flex gap-3">
            <button onClick={() => { setStep(1); setImportResult(null); }} className="px-6 py-2.5 border border-slate-200 text-slate-600 rounded-xl text-sm font-medium hover:bg-slate-50">Nouvel import</button>
            <button onClick={() => window.location.hash = "contacts"} className="px-6 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-slate-800">Voir les contacts</button>
          </div>
        </div>
      )}

      {/* Saved mappings */}
      {savedMappings.length > 0 && step === 1 && (
        <div className="mt-8 bg-white rounded-2xl border border-slate-100 p-6">
          <h3 className="text-sm font-bold text-slate-700 mb-3">Mappings sauvegardés</h3>
          <div className="space-y-2">
            {savedMappings.map(m => (
              <div key={m.id} className="flex items-center justify-between p-3 border border-slate-100 rounded-xl">
                <div>
                  <div className="text-sm font-medium text-slate-800">{m.name}</div>
                  <div className="text-xs text-slate-400">{m.connection_host} / {m.connection_db} · {m.field_mappings?.length || 0} champs mappés</div>
                </div>
                <span className="text-xs text-slate-400">{m.created_at?.split("T")[0]}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
