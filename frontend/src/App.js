import { useState, useEffect, useCallback } from "react";

// ── CONFIG ──────────────────────────────────────────────────────────────────
// ── STYLES ──────────────────────────────────────────────────────────────────
const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@300;400;500;600;700&family=Orbitron:wght@400;700;900&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:        #050a0f;
    --bg2:       #080f17;
    --bg3:       #0d1a26;
    --border:    #0f2a3f;
    --border2:   #1a3d5c;
    --cyan:      #00d4ff;
    --cyan-dim:  #007a99;
    --green:     #00ff88;
    --green-dim: #00664a;
    --amber:     #ffb300;
    --red:       #ff3d5a;
    --text:      #c8e6f5;
    --text-dim:  #4a7a99;
    --font-mono: 'Share Tech Mono', monospace;
    --font-body: 'Rajdhani', sans-serif;
    --font-head: 'Orbitron', monospace;
  }

  body { background: var(--bg); color: var(--text); font-family: var(--font-body); min-height: 100vh; }

  .scanline {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0; pointer-events: none; z-index: 9999;
    background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,212,255,0.015) 2px, rgba(0,212,255,0.015) 4px);
  }

  .app { display: flex; flex-direction: column; min-height: 100vh; }

  /* HEADER */
  .header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 28px; border-bottom: 1px solid var(--border2);
    background: linear-gradient(90deg, var(--bg2) 0%, #0a1520 100%);
    position: sticky; top: 0; z-index: 100;
  }
  .header-logo { display: flex; align-items: center; gap: 14px; }
  .logo-icon {
    width: 38px; height: 38px; border: 2px solid var(--cyan);
    border-radius: 4px; display: flex; align-items: center; justify-content: center;
    font-family: var(--font-head); font-size: 14px; color: var(--cyan);
    box-shadow: 0 0 12px rgba(0,212,255,0.3); animation: pulse-glow 3s ease-in-out infinite;
  }
  @keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 12px rgba(0,212,255,0.3); }
    50% { box-shadow: 0 0 24px rgba(0,212,255,0.6); }
  }
  .logo-text { font-family: var(--font-head); font-size: 18px; font-weight: 700; letter-spacing: 4px; color: var(--cyan); }
  .logo-sub { font-family: var(--font-body); font-size: 11px; color: var(--text-dim); letter-spacing: 2px; text-transform: uppercase; }
  .header-status { display: flex; align-items: center; gap: 20px; }
  .status-pill {
    display: flex; align-items: center; gap: 7px; padding: 5px 12px;
    border: 1px solid var(--border2); border-radius: 20px;
    font-family: var(--font-mono); font-size: 11px; color: var(--text-dim);
  }
  .status-dot { width: 7px; height: 7px; border-radius: 50%; }
  .dot-green { background: var(--green); box-shadow: 0 0 6px var(--green); animation: blink 2s ease-in-out infinite; }
  .dot-amber { background: var(--amber); box-shadow: 0 0 6px var(--amber); }
  .dot-red   { background: var(--red);   box-shadow: 0 0 6px var(--red); }
  @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
  .header-time { font-family: var(--font-mono); font-size: 13px; color: var(--cyan); letter-spacing: 1px; }

  /* TABS */
  .tabs { display: flex; gap: 2px; padding: 0 28px; background: var(--bg2); border-bottom: 1px solid var(--border); }
  .tab {
    padding: 14px 24px; font-family: var(--font-body); font-size: 13px; font-weight: 600;
    letter-spacing: 2px; text-transform: uppercase; color: var(--text-dim);
    cursor: pointer; border: none; background: none; border-bottom: 2px solid transparent;
    transition: all 0.2s; display: flex; align-items: center; gap: 8px;
  }
  .tab:hover { color: var(--text); }
  .tab.active { color: var(--cyan); border-bottom-color: var(--cyan); }
  .tab-badge {
    background: var(--red); color: white; font-size: 9px; padding: 2px 6px;
    border-radius: 10px; font-family: var(--font-mono); animation: blink 1.5s infinite;
  }

  /* MAIN */
  .main { flex: 1; padding: 24px 28px; }

  /* CARDS */
  .card {
    background: var(--bg2); border: 1px solid var(--border); border-radius: 6px;
    overflow: hidden; margin-bottom: 20px;
  }
  .card-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 18px; border-bottom: 1px solid var(--border);
    background: linear-gradient(90deg, var(--bg3) 0%, var(--bg2) 100%);
  }
  .card-title { font-family: var(--font-head); font-size: 11px; letter-spacing: 3px; color: var(--cyan); }
  .card-body { padding: 18px; }

  /* GRID */
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }

  /* STAT CARDS */
  .stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
  .stat-card {
    background: var(--bg2); border: 1px solid var(--border); border-radius: 6px;
    padding: 18px; position: relative; overflow: hidden;
  }
  .stat-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  }
  .stat-card.cyan::before { background: var(--cyan); }
  .stat-card.green::before { background: var(--green); }
  .stat-card.amber::before { background: var(--amber); }
  .stat-card.red::before { background: var(--red); }
  .stat-label { font-family: var(--font-mono); font-size: 10px; color: var(--text-dim); letter-spacing: 2px; margin-bottom: 8px; }
  .stat-value { font-family: var(--font-head); font-size: 28px; font-weight: 700; }
  .stat-value.cyan { color: var(--cyan); }
  .stat-value.green { color: var(--green); }
  .stat-value.amber { color: var(--amber); }
  .stat-value.red { color: var(--red); }
  .stat-sub { font-family: var(--font-mono); font-size: 10px; color: var(--text-dim); margin-top: 4px; }

  /* TABLE */
  .data-table { width: 100%; border-collapse: collapse; font-family: var(--font-mono); font-size: 12px; }
  .data-table th {
    text-align: left; padding: 10px 12px; color: var(--text-dim);
    border-bottom: 1px solid var(--border2); font-size: 10px; letter-spacing: 2px; text-transform: uppercase;
  }
  .data-table td { padding: 10px 12px; border-bottom: 1px solid var(--border); color: var(--text); }
  .data-table tr:last-child td { border-bottom: none; }
  .data-table tr:hover td { background: rgba(0,212,255,0.03); }

  /* BADGES */
  .badge {
    display: inline-block; padding: 3px 10px; border-radius: 3px; font-size: 10px;
    font-family: var(--font-mono); font-weight: bold; letter-spacing: 1px;
  }
  .badge-green { background: rgba(0,255,136,0.1); color: var(--green); border: 1px solid var(--green-dim); }
  .badge-red   { background: rgba(255,61,90,0.1);  color: var(--red);   border: 1px solid #7a1a2a; }
  .badge-amber { background: rgba(255,179,0,0.1);  color: var(--amber); border: 1px solid #7a5500; }
  .badge-cyan  { background: rgba(0,212,255,0.1);  color: var(--cyan);  border: 1px solid var(--cyan-dim); }

  /* BUTTONS */
  .btn {
    padding: 9px 20px; border-radius: 4px; font-family: var(--font-body); font-size: 13px;
    font-weight: 600; letter-spacing: 1px; cursor: pointer; border: none; transition: all 0.2s;
  }
  .btn-cyan { background: rgba(0,212,255,0.1); color: var(--cyan); border: 1px solid var(--cyan-dim); }
  .btn-cyan:hover { background: rgba(0,212,255,0.2); box-shadow: 0 0 12px rgba(0,212,255,0.2); }
  .btn-green { background: rgba(0,255,136,0.1); color: var(--green); border: 1px solid var(--green-dim); }
  .btn-green:hover { background: rgba(0,255,136,0.2); }
  .btn-red { background: rgba(255,61,90,0.1); color: var(--red); border: 1px solid #7a1a2a; }
  .btn-sm { padding: 5px 12px; font-size: 11px; }

  /* INPUT */
  .input {
    background: var(--bg3); border: 1px solid var(--border2); border-radius: 4px;
    color: var(--text); padding: 9px 14px; font-family: var(--font-mono); font-size: 13px;
    outline: none; transition: border 0.2s; width: 100%;
  }
  .input:focus { border-color: var(--cyan); box-shadow: 0 0 8px rgba(0,212,255,0.1); }

  /* SCORE BAR */
  .score-bar-bg { background: var(--bg3); border-radius: 2px; height: 6px; margin-top: 4px; overflow: hidden; }
  .score-bar-fill { height: 100%; border-radius: 2px; transition: width 0.5s; }

  /* ALERT CARD */
  .alert-item {
    border: 1px solid var(--border); border-radius: 5px; padding: 14px;
    margin-bottom: 10px; background: var(--bg3); position: relative; overflow: hidden;
    transition: border-color 0.2s;
  }
  .alert-item:hover { border-color: var(--red); }
  .alert-item::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: var(--red); }
  .alert-item.high::before { background: var(--red); }
  .alert-item.medium::before { background: var(--amber); }
  .alert-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
  .alert-ticker { font-family: var(--font-head); font-size: 16px; color: var(--cyan); }
  .alert-score { font-family: var(--font-head); font-size: 22px; }
  .alert-score.high { color: var(--red); }
  .alert-score.medium { color: var(--amber); }
  .alert-meta { font-family: var(--font-mono); font-size: 10px; color: var(--text-dim); margin-bottom: 8px; }
  .feature-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-top: 8px; }
  .feature-item { background: var(--bg2); padding: 6px 8px; border-radius: 3px; }
  .feature-label { font-size: 9px; color: var(--text-dim); letter-spacing: 1px; }
  .feature-val { font-family: var(--font-mono); font-size: 12px; color: var(--text); margin-top: 2px; }

  /* RULE ITEM */
  .rule-item {
    display: flex; justify-content: space-between; align-items: center;
    padding: 12px 14px; border: 1px solid var(--border); border-radius: 4px;
    margin-bottom: 8px; background: var(--bg3);
  }
  .rule-key { font-family: var(--font-mono); font-size: 12px; color: var(--cyan); }
  .rule-val { font-family: var(--font-head); font-size: 16px; color: var(--amber); }

  /* LOADING */
  .loading { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 40px; color: var(--text-dim); font-family: var(--font-mono); font-size: 12px; }
  .spinner { width: 18px; height: 18px; border: 2px solid var(--border2); border-top-color: var(--cyan); border-radius: 50%; animation: spin 0.8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* EMPTY */
  .empty { text-align: center; padding: 48px; color: var(--text-dim); font-family: var(--font-mono); font-size: 12px; }
  .empty-icon { font-size: 32px; margin-bottom: 12px; opacity: 0.4; }

  /* TERMINAL */
  .terminal {
    background: #020a0f; border: 1px solid var(--border2); border-radius: 4px;
    padding: 14px; font-family: var(--font-mono); font-size: 12px; max-height: 220px;
    overflow-y: auto; color: var(--green);
  }
  .terminal-line { margin-bottom: 4px; }
  .terminal-line .ts { color: var(--text-dim); margin-right: 8px; }
  .terminal-line .ok  { color: var(--green); }
  .terminal-line .err { color: var(--red); }
  .terminal-line .info { color: var(--cyan); }

  /* MODULE TAG */
  .module-tag { font-family: var(--font-mono); font-size: 9px; color: var(--text-dim); letter-spacing: 2px; margin-bottom: 4px; }

  /* SCROLLBAR */
  ::-webkit-scrollbar { width: 5px; height: 5px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--cyan-dim); }

  /* ADVISORY BANNER */
  .advisory {
    display: flex; align-items: center; gap: 10px;
    background: rgba(255,179,0,0.06); border: 1px solid rgba(255,179,0,0.2);
    border-radius: 4px; padding: 10px 14px; margin-bottom: 16px;
    font-family: var(--font-mono); font-size: 11px; color: var(--amber);
  }
`;

// ── HELPERS ─────────────────────────────────────────────────────────────────
const fmt = (n) => typeof n === "number" ? n.toLocaleString() : n;
const pct = (n) => `${(n * 100).toFixed(1)}%`;
const now = () => new Date().toLocaleTimeString("en-GB", { hour12: false });
const scoreColor = (s) => s > 0.75 ? "red" : s > 0.5 ? "amber" : "green";
const scoreBarColor = (s) => s > 0.75 ? "var(--red)" : s > 0.5 ? "var(--amber)" : "var(--green)";

// ── CLOCK ────────────────────────────────────────────────────────────────────
function Clock() {
    const [t, setT] = useState(now());
    useEffect(() => { const id = setInterval(() => setT(now()), 1000); return () => clearInterval(id); }, []);
    return <span className="header-time">{new Date().toISOString().slice(0, 10)} {t} UTC</span>;
}

// ── TAB: MODULE 1 – TRADE VALIDATOR ─────────────────────────────────────────
function Module1Tab() {
    const [auditLogs, setAuditLogs] = useState([]);
    const [scores, setScores] = useState([]);
    const [loading, setLoading] = useState(false);

    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
            // Fetch anomaly scores from Table Storage
            const scoreRes = await fetch(`${CONFIG.ANOMALY_BASE}/api/get-alerts?source=table&code=${CONFIG.GET_ALERTS_KEY}`);
            const scoreData = await scoreRes.json();
            setScores(scoreData.scores || []);

            // Fetch audit logs from blob storage via SAS URL
            const sasBase = CONFIG.AUDIT_LOGS_SAS_URL;
            const today = new Date().toISOString().slice(0, 10);
            const listUrl = `${sasBase}&restype=container&comp=list&prefix=${today}`;
            const listRes = await fetch(listUrl);
            const listText = await listRes.text();

            // Parse blob names from XML response
            const blobNames = [];
            const regex = /<Name>([^<]+)<\/Name>/g;
            let match;
            while ((match = regex.exec(listText)) !== null) {
                blobNames.push(match[1]);
            }

            // Fetch exactly the last 22 audit logs (matches exactly 1 simulator run of 22 orders)
            const logs = [];
            for (const name of blobNames.slice(-22)) { // max 22
                try {
                    const blobUrl = `${sasBase.split('?')[0]}/${name}?${sasBase.split('?')[1]}`;
                    const blobRes = await fetch(blobUrl);
                    const blobData = await blobRes.json();
                    logs.push(blobData);
                } catch (e) { /* skip bad blobs */ }
            }

            // Sort by timestamp descending (newest first)
            logs.sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''));
            setAuditLogs(logs);
        } catch (e) {
            console.error("Module1Tab fetch error:", e);
        }
        setLoading(false);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => { fetchData(); }, [fetchData]);

    // Auto-refresh every 15 seconds
    useEffect(() => {
        const id = setInterval(fetchData, 15000);
        return () => clearInterval(id);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Merge audit logs with anomaly scores by order_id
    const merged = auditLogs.map(log => {
        const score = scores.find(s =>
            (s.RowKey || '').includes(log.order_id) || (s.order_id === log.order_id)
        );
        return { ...log, anomaly_score: score?.anomaly_score, is_flagged: score?.is_flagged };
    });

    // Stats
    const approved = auditLogs.filter(l => l.decision?.status === 'APPROVED').length;
    const rejected = auditLogs.filter(l => l.decision?.status === 'REJECTED' || l.decision?.status === 'FLAGGED').length;
    const totalOrders = auditLogs.length;

    // Most violated rule
    const violations = auditLogs
        .filter(l => l.decision?.status === 'REJECTED')
        .map(l => l.decision?.reason)
        .filter(Boolean);
    const violationCounts = {};
    violations.forEach(v => { violationCounts[v] = (violationCounts[v] || 0) + 1; });
    const topViolation = Object.entries(violationCounts).sort((a, b) => b[1] - a[1])[0];

    return (
        <div>
            <div className="module-tag">MODULE 01 — TRADE VALIDATOR</div>

            {/* Summary Banner */}
            {totalOrders > 0 && (
                <div className="advisory" style={{ background: "rgba(0,212,255,0.04)", borderColor: "var(--border2)", marginBottom: 16 }}>
                    <span style={{ color: "var(--cyan)" }}>
                        Last batch: <strong>{totalOrders}</strong> orders ·{" "}
                        <span style={{ color: "var(--green)" }}>{approved} APPROVED</span> ·{" "}
                        <span style={{ color: "var(--red)" }}>{rejected} REJECTED</span>
                        {topViolation && (
                            <span style={{ color: "var(--amber)", marginLeft: 12 }}>
                                Most violated: {topViolation[0]} ({topViolation[1]}×)
                            </span>
                        )}
                    </span>
                </div>
            )}

            <div className="stat-grid">
                <div className="stat-card cyan">
                    <div className="stat-label">TOTAL ORDERS</div>
                    <div className="stat-value cyan">{totalOrders}</div>
                    <div className="stat-sub">Today's window</div>
                </div>
                <div className="stat-card green">
                    <div className="stat-label">APPROVED</div>
                    <div className="stat-value green">{approved}</div>
                    <div className="stat-sub">Clean trades</div>
                </div>
                <div className="stat-card red">
                    <div className="stat-label">REJECTED</div>
                    <div className="stat-value red">{rejected}</div>
                    <div className="stat-sub">Rule violations</div>
                </div>
                <div className="stat-card amber">
                    <div className="stat-label">REJECT RATE</div>
                    <div className="stat-value amber">{totalOrders ? pct(rejected / totalOrders) : "0.0%"}</div>
                    <div className="stat-sub">Today</div>
                </div>
            </div>

            <div className="grid-2">
                <div className="card">
                    <div className="card-header">
                        <span className="card-title">TRADE DECISIONS — AUDIT LOG</span>
                        <button className="btn btn-cyan btn-sm" onClick={fetchData}>↺ REFRESH</button>
                    </div>
                    <div className="card-body" style={{ padding: 0 }}>
                        {loading ? <div className="loading"><div className="spinner" /> FETCHING...</div> :
                            merged.length === 0 ? <div className="empty"><div className="empty-icon">◈</div>No records yet — run simulator.py</div> :
                                <table className="data-table">
                                    <thead><tr><th>ORDER ID</th><th>TICKER</th><th>VALUE</th><th>STATUS</th><th>REASON</th></tr></thead>
                                    <tbody>
                                        {merged.slice(0, 15).map((l, i) => {
                                            const status = l.decision?.status || "—";
                                            const isRejected = status === "REJECTED" || status === "FLAGGED";
                                            return (
                                                <tr key={i}>
                                                    <td style={{ color: "var(--text-dim)", fontSize: 10 }}>{String(l.order_id || "—").slice(0, 16)}</td>
                                                    <td style={{ color: "var(--cyan)", fontFamily: "var(--font-head)" }}>{l.ticker || "—"}</td>
                                                    <td style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>${fmt(l.value || 0)}</td>
                                                    <td>
                                                        <span className={`badge ${isRejected ? "badge-red" : "badge-green"}`}>
                                                            {status}
                                                        </span>
                                                    </td>
                                                    <td style={{ fontSize: 10, maxWidth: 220 }}>
                                                        {isRejected ? (
                                                            <span style={{ color: "var(--red)" }}>✗ {l.rejection_reason || l.decision?.reason || "—"}</span>
                                                        ) : (
                                                            <span style={{ color: "var(--green)" }}>✓ PASSED</span>
                                                        )}
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>}
                    </div>
                </div>

                <div className="card">
                    <div className="card-header"><span className="card-title">RECENT ACTIVITY FEED</span></div>
                    <div className="card-body" style={{ padding: 0 }}>
                        <div className="terminal" style={{ maxHeight: 380 }}>
                            {auditLogs.length === 0 && <div className="terminal-line"><span className="info">CUSTOS TradeValidator v1.0 — Awaiting orders...</span></div>}
                            {auditLogs.slice(0, 15).map((l, i) => {
                                const time = l.timestamp ? l.timestamp.split('T')[1]?.slice(0, 8) : "--:--:--";
                                const status = l.decision?.status || "—";
                                const isRejected = status === "REJECTED" || status === "FLAGGED";
                                const valStr = l.value ? `$${(l.value / 1e6).toFixed(1)}M` : "$0";
                                return (
                                    <div key={i} className="terminal-line">
                                        <span className="ts">[{time}]</span>
                                        <span className={isRejected ? "err" : "ok"}>
                                            {isRejected ? "✗" : "✓"} {(l.ticker || "—").padEnd(8)} {valStr.padEnd(10)} {status}
                                        </span>
                                        {isRejected && l.rejection_reason && (
                                            <span style={{ color: "var(--text-dim)", marginLeft: 4, fontSize: 10 }}>
                                                — {l.decision?.reason}
                                            </span>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// ── TAB: MODULE 2 – FINDISTILL ───────────────────────────────────────────────
function Module2Tab() {
    const [rules, setRules] = useState([]);
    const [pendingRules, setPendingRules] = useState([]);
    const [pdfFile, setPdfFile] = useState(null);
    const [pdfName, setPdfName] = useState("");
    const [loading, setLoading] = useState(false);
    const [pdfStatus, setPdfStatus] = useState(null);
    const [approveStatus, setApproveStatus] = useState(null);

    const approveRules = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${CONFIG.FINDISTILL_BASE}/api/ApproveRules?code=${CONFIG.APPROVE_RULES_KEY}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ rules: pendingRules }),
            });
            const data = await res.json();
            setApproveStatus(data);

            // Merge newly approved rules with existing rules, keeping newest
            setRules(prev => {
                const map = new Map();
                prev.forEach(r => map.set(r.key, r));
                pendingRules.forEach(r => map.set(r.key, r));
                return Array.from(map.values());
            });
            setPendingRules([]);
        } catch (e) { console.error(e); }
        setLoading(false);
    };

    const uploadPdf = async () => {
        if (!pdfFile) return;
        setLoading(true);
        setPendingRules([]);
        setApproveStatus(null);
        setPdfStatus(null);
        try {
            const res = await fetch(
                `${CONFIG.FINDISTILL_BASE}/api/PDFIngestion?filename=${pdfName}&code=${CONFIG.PDF_INGESTION_KEY}`,
                { method: "POST", headers: { "Content-Type": "application/pdf" }, body: pdfFile }
            );
            const data = await res.json();
            console.log("PDFIngestion full response:", JSON.stringify(data, null, 2));
            setPdfStatus(data);

            if (data.proposed_rules && data.proposed_rules.length > 0) {
                // Deduplicate by key — keep last occurrence
                const map = new Map();
                data.proposed_rules.forEach(r => map.set(r.key, r));
                setPendingRules(Array.from(map.values()));
            }
        } catch (e) { console.error("PDFIngestion fetch error:", e); }
        setLoading(false);
    };

    // Build a human‑readable status from the _debug field
    const debugLine = pdfStatus?._debug ? (() => {
        const d = pdfStatus._debug;
        const parts = [];
        parts.push(`${d.pages_in_pdf || 0} pages`);
        parts.push(`${d.pdf_text_length || 0} chars extracted`);
        parts.push(`${d.indexed_count || 0} indexed`);
        if (d.groq_called) {
            parts.push(`Groq: ${d.rules_before_dedup || 0} raw → ${d.rules_after_dedup || 0} deduped`);
        }
        if (d.groq_error) parts.push(`⚠ ${d.groq_error}`);
        return parts.join(" · ");
    })() : null;

    return (
        <div>
            <div className="module-tag">MODULE 02 — FINDISTILL — REGULATORY INTELLIGENCE</div>
            <div className="grid-2">
                <div>
                    <div className="card">
                        <div className="card-header">
                            <span className="card-title">PROPOSED RULES FROM LAST INGESTION</span>
                        </div>
                        <div className="card-body">
                            {loading ? <div className="loading"><div className="spinner" />INGESTING & EXTRACTING...</div> :
                                pendingRules.length === 0 ?
                                    <div className="empty">
                                        <div className="empty-icon">⊡</div>
                                        {pdfStatus && pdfStatus.status === "ok"
                                            ? "No rules found in this PDF"
                                            : "No rules pending — ingest a PDF to extract rules"}
                                    </div> :
                                    pendingRules.map((r, i) => (
                                        <div key={i} className="rule-item" style={{ flexDirection: "column", alignItems: "stretch" }}>
                                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                                <div>
                                                    <div className="rule-key">{r.key}</div>
                                                    <div style={{ fontSize: 10, color: "var(--text-dim)", marginTop: 2 }}>Proposed value</div>
                                                </div>
                                                <div className="rule-val">{fmt(r.value)}</div>
                                            </div>
                                            {r.source_quote && (
                                                <div style={{ fontSize: 10, color: "var(--text-dim)", marginTop: 6, padding: "6px 8px", background: "var(--bg)", borderRadius: 3, fontFamily: "var(--font-mono)", fontStyle: "italic", borderLeft: "2px solid var(--cyan-dim)" }}>
                                                    "{r.source_quote}"
                                                </div>
                                            )}
                                        </div>
                                    ))}
                            {pendingRules.length > 0 && (
                                <button className="btn btn-green" style={{ width: "100%", marginTop: 12 }} onClick={approveRules}>
                                    ✓ APPROVE & PUSH TO REDIS
                                </button>
                            )}
                            {approveStatus && (
                                <div style={{ marginTop: 12, padding: "10px", background: "rgba(0,255,136,0.05)", border: "1px solid var(--green-dim)", borderRadius: 4, fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--green)" }}>
                                    ✓ Applied: {approveStatus.rules_applied?.join(", ")}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                <div>
                    <div className="card">
                        <div className="card-header"><span className="card-title">PDF INGESTION — REGULATORY DOCS</span></div>
                        <div className="card-body">
                            <div style={{ marginBottom: 14 }}>
                                <div style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 6, fontFamily: "var(--font-mono)" }}>FILENAME</div>
                                <input className="input" placeholder="e.g. daytrading.pdf" value={pdfName} onChange={e => setPdfName(e.target.value)} />
                            </div>
                            <div style={{ marginBottom: 14 }}>
                                <div style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 6, fontFamily: "var(--font-mono)" }}>PDF FILE</div>
                                <input type="file" accept=".pdf" onChange={e => setPdfFile(e.target.files[0])}
                                    style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text)", background: "var(--bg3)", border: "1px solid var(--border2)", padding: "8px", borderRadius: 4, width: "100%" }} />
                            </div>
                            <button className="btn btn-cyan" style={{ width: "100%" }} onClick={uploadPdf} disabled={!pdfFile || !pdfName || loading}>
                                {loading ? "⏳ INGESTING & EXTRACTING..." : "↑ INGEST PDF & EXTRACT RULES"}
                            </button>
                            {pdfStatus && (
                                <div style={{ marginTop: 12, padding: "10px", background: "rgba(0,212,255,0.05)", border: "1px solid var(--cyan-dim)", borderRadius: 4, fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--cyan)" }}>
                                    ✓ {pdfStatus.filename || pdfName} — Pages: {pdfStatus.pages_indexed} — Rules: {pdfStatus.proposed_rules?.length || 0}
                                    {debugLine && <div style={{ marginTop: 4, fontSize: 10, color: "var(--text-dim)" }}>{debugLine}</div>}
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="card">
                        <div className="card-header"><span className="card-title">ACTIVE REDIS RULES</span></div>
                        <div className="card-body">
                            {rules.length === 0 ?
                                <div className="empty"><div className="empty-icon">⊟</div>No active rules — ingest and approve PDFs to populate</div> :
                                rules.map((r, i) => (
                                    <div key={i} className="rule-item">
                                        <div className="rule-key">{r.key}</div>
                                        <div className="rule-val">{fmt(r.value)}</div>
                                    </div>
                                ))
                            }
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// ── TAB: MODULE 3 – AUDIT LOGS ───────────────────────────────────────────────
function Module3Tab() {
    return (
        <div>
            <div className="module-tag">MODULE 03 — IMMUTABLE AUDIT LOG — WORM COMPLIANCE</div>
            <div className="advisory">
                ⚠ MiFID II / SEC Rule 17a-4 — Audit logs are stored with WORM immutability policy (7-day test / 2557-day production). Read-only SAS token issued for Module 4 access.
            </div>
            <div className="stat-grid">
                <div className="stat-card cyan">
                    <div className="stat-label">STORAGE ACCOUNT</div>
                    <div className="stat-value cyan" style={{ fontSize: 16, marginTop: 6 }}>custosblob2</div>
                    <div className="stat-sub">Azure Blob Storage</div>
                </div>
                <div className="stat-card green">
                    <div className="stat-label">CONTAINER</div>
                    <div className="stat-value green" style={{ fontSize: 16, marginTop: 6 }}>audit-logs</div>
                    <div className="stat-sub">WORM protected</div>
                </div>
                <div className="stat-card amber">
                    <div className="stat-label">RETENTION</div>
                    <div className="stat-value amber" style={{ fontSize: 22, marginTop: 6 }}>7 days</div>
                    <div className="stat-sub">Test (2557 prod)</div>
                </div>
                <div className="stat-card red">
                    <div className="stat-label">SAS EXPIRY</div>
                    <div className="stat-value red" style={{ fontSize: 16, marginTop: 6 }}>2026-04-06</div>
                    <div className="stat-sub">Read-only token</div>
                </div>
            </div>

            <div className="grid-2">
                <div className="card">
                    <div className="card-header"><span className="card-title">IMMUTABILITY POLICY</span></div>
                    <div className="card-body">
                        {[
                            { label: "Policy Type", value: "Time-based retention", color: "cyan" },
                            { label: "State", value: "Unlocked (Test Mode)", color: "amber" },
                            { label: "Retention Period", value: "7 days", color: "green" },
                            { label: "Production Setting", value: "2557 days (7 years)", color: "text" },
                            { label: "Compliance", value: "MiFID II Art.17 / SEC Rule 17a-4", color: "cyan" },
                            { label: "Delete Protection", value: "Enabled", color: "green" },
                        ].map((item, i) => (
                            <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "10px 0", borderBottom: "1px solid var(--border)", alignItems: "center" }}>
                                <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-dim)" }}>{item.label}</span>
                                <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: `var(--${item.color})` }}>{item.value}</span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="card">
                    <div className="card-header"><span className="card-title">SAS TOKEN CONFIG — MODULE 4 ACCESS</span></div>
                    <div className="card-body">
                        {[
                            { label: "Allowed Services", value: "Blob only" },
                            { label: "Resource Types", value: "Container + Object" },
                            { label: "Permissions", value: "Read + List" },
                            { label: "Protocol", value: "HTTPS only" },
                            { label: "Region", value: "Central India" },
                            { label: "Purpose", value: "Anomaly detector read access" },
                        ].map((item, i) => (
                            <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "10px 0", borderBottom: "1px solid var(--border)", alignItems: "center" }}>
                                <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-dim)" }}>{item.label}</span>
                                <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--cyan)" }}>{item.value}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

// ── TAB: MODULE 4 – ANOMALY DETECTION ───────────────────────────────────────
function Module4Tab() {
    const [alerts, setAlerts] = useState([]);
    const [scores, setScores] = useState([]);
    const [loading, setLoading] = useState(false);
    const [running, setRunning] = useState(false);
    const [runResult, setRunResult] = useState(null);

    const fetchAlerts = useCallback(async () => {
        setLoading(true);
        try {
            const [aRes, sRes] = await Promise.all([
                fetch(`${CONFIG.ANOMALY_BASE}/api/get-alerts?code=${CONFIG.GET_ALERTS_KEY}`),
                fetch(`${CONFIG.ANOMALY_BASE}/api/get-alerts?source=table&code=${CONFIG.GET_ALERTS_KEY}`),
            ]);
            const aData = await aRes.json();
            const sData = await sRes.json();
            setAlerts(aData.alerts || []);
            setScores(sData.scores || []);
        } catch (e) { console.error(e); }
        setLoading(false);
    }, []);

    // ── FIX: robust RunDetector response parsing ─────────────────────────────
    // The Azure Function returns { status, records_scored, anomalies_flagged }.
    // Previously this read `alerts_flagged` (wrong key) → showed "undefined".
    // Now we check all plausible key names so it works regardless of exact casing.
    const runDetector = async () => {
        setRunning(true);
        setRunResult(null);
        try {
            const res = await fetch(
                `${CONFIG.ANOMALY_BASE}/api/RunDetector?code=${CONFIG.RUN_DETECTOR_KEY}`,
                { method: "POST" }
            );

            // Guard: if the function returns no body (204 / empty), handle gracefully
            const text = await res.text();
            let data = {};
            if (text && text.trim().length > 0) {
                try { data = JSON.parse(text); } catch (_) { data = { status: "ok", raw: text }; }
            }

            // ── Read counts with fallbacks across all likely key names ──────
            const scored =
                data.records_scored ??  // primary key expected from Azure Function
                data.scored_count ??
                data.total_scored ??
                data.total ??
                null;

            const flagged =
                data.anomalies_flagged ??  // primary key expected from Azure Function
                data.flagged_count ??
                data.alerts_flagged ??  // was the old (wrong) key — kept as last fallback
                data.flagged ??
                null;

            setRunResult({
                status: data.status || (res.ok ? "ok" : "error"),
                message: data.message || data.error || null,
                records_scored: scored,
                anomalies_flagged: flagged,
            });

            // Refresh dashboard data after a short delay so new alerts appear
            setTimeout(() => fetchAlerts(), 2500);
        } catch (e) {
            setRunResult({ status: "error", message: e.message });
        }
        setRunning(false);
    };
    // ── END FIX ──────────────────────────────────────────────────────────────

    useEffect(() => { fetchAlerts(); const id = setInterval(fetchAlerts, 60000); return () => clearInterval(id); }, [fetchAlerts]);

    const highAlerts = alerts.filter(a => a.anomaly_score > 0.75);
    const mediumAlerts = alerts.filter(a => a.anomaly_score <= 0.75 && a.anomaly_score > 0.5);
    const avgScore = scores.length ? scores.reduce((a, b) => a + (b.anomaly_score || 0), 0) / scores.length : 0;

    // ── Helper: human-readable result banner ─────────────────────────────────
    const renderRunResult = () => {
        if (!runResult) return null;
        const isError = runResult.status === "error";
        const scored = runResult.records_scored;
        const flagged = runResult.anomalies_flagged;

        let msg;
        if (isError) {
            msg = `✗ Error: ${runResult.message || "Unknown error"}`;
        } else if (scored === null && flagged === null) {
            // Function returned no counts — succeeded but no data in window
            msg = `✓ Detector ran — no records in scoring window (run simulator.py first)`;
        } else {
            msg = `✓ Scored: ${scored ?? "?"} records · Flagged: ${flagged ?? "?"} anomalies`;
        }

        return (
            <div style={{
                fontFamily: "var(--font-mono)", fontSize: 12,
                color: isError ? "var(--red)" : "var(--green)",
                background: isError ? "rgba(255,61,90,0.05)" : "rgba(0,255,136,0.05)",
                border: `1px solid ${isError ? "var(--red)" : "var(--green-dim)"}`,
                padding: "8px 14px", borderRadius: 4,
            }}>
                {msg}
            </div>
        );
    };
    // ── END helper ────────────────────────────────────────────────────────────

    return (
        <div>
            <div className="module-tag">MODULE 04 — ANOMALY DETECTION — SHADOW MODE — ADVISORY ONLY</div>
            <div className="advisory">
                ⚠ ADVISORY ONLY — Module 4 has zero influence over trade execution. No trade is ever blocked based on this output. Satisfies MiFID II Art.17, SEC Rule 15c3-5, FINRA Rule 3110.
            </div>

            {/* RUN DETECTOR PANEL */}
            <div className="card" style={{ marginBottom: 20 }}>
                <div className="card-header">
                    <span className="card-title">⚡ MANUAL TRIGGER — RUN DETECTOR NOW</span>
                </div>
                <div className="card-body" style={{ display: "flex", alignItems: "center", gap: 16 }}>
                    <button
                        className="btn btn-red"
                        onClick={runDetector}
                        disabled={running || !CONFIG.RUN_DETECTOR_KEY}
                        style={{ minWidth: 180 }}
                    >
                        {running ? "⏳ RUNNING..." : "⚡ RUN DETECTOR NOW"}
                    </button>
                    {!CONFIG.RUN_DETECTOR_KEY && (
                        <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--amber)" }}>
                            ⚠ Add RUN_DETECTOR_KEY to CONFIG after deploy
                        </span>
                    )}
                    {renderRunResult()}
                </div>
            </div>

            <div className="stat-grid">
                <div className="stat-card red">
                    <div className="stat-label">HIGH ALERTS</div>
                    <div className="stat-value red">{highAlerts.length}</div>
                    <div className="stat-sub">Score &gt; 0.75</div>
                </div>
                <div className="stat-card amber">
                    <div className="stat-label">MEDIUM ALERTS</div>
                    <div className="stat-value amber">{mediumAlerts.length}</div>
                    <div className="stat-sub">Score 0.5–0.75</div>
                </div>
                <div className="stat-card cyan">
                    <div className="stat-label">SCORED TODAY</div>
                    <div className="stat-value cyan">{scores.length}</div>
                    <div className="stat-sub">Table Storage</div>
                </div>
                <div className="stat-card green">
                    <div className="stat-label">AVG SCORE</div>
                    <div className="stat-value green">{avgScore.toFixed(3)}</div>
                    <div className="stat-sub">All trades</div>
                </div>
            </div>

            <div className="grid-2">
                <div className="card">
                    <div className="card-header">
                        <span className="card-title">FLAGGED ALERTS — BLOB STORAGE</span>
                        <button className="btn btn-cyan btn-sm" onClick={fetchAlerts}>↺ REFRESH</button>
                    </div>
                    <div className="card-body">
                        {loading ? <div className="loading"><div className="spinner" />SCANNING...</div> :
                            alerts.length === 0 ?
                                <div className="empty">
                                    <div className="empty-icon">◉</div>
                                    No alerts yet — click RUN DETECTOR NOW
                                    <div style={{ marginTop: 8, fontSize: 10 }}>Or wait for 1-min auto timer</div>
                                </div> :
                                alerts.map((a, i) => {
                                    const sc = scoreColor(a.anomaly_score);
                                    return (
                                        <div key={i} className={`alert-item ${sc}`}>
                                            <div className="alert-top">
                                                <div>
                                                    <div className="alert-ticker">{a.ticker}</div>
                                                    <div className="alert-meta">{a.order_id?.slice(0, 16)}... · {a.timestamp?.slice(0, 19)}</div>
                                                </div>
                                                <div>
                                                    <div className={`alert-score ${sc}`}>{a.anomaly_score?.toFixed(3)}</div>
                                                    <div style={{ fontSize: 9, color: "var(--text-dim)", textAlign: "right" }}>ANOMALY SCORE</div>
                                                </div>
                                            </div>
                                            <div style={{ display: "flex", gap: 8 }}>
                                                <span className="badge badge-red">ISO: {a.iso_score?.toFixed(3)}</span>
                                                <span className="badge badge-amber">AE: {a.ae_score?.toFixed(3)}</span>
                                                <span className="badge badge-cyan">ADVISORY ONLY</span>
                                            </div>
                                            {a.feature_snapshot && (
                                                <div className="feature-grid">
                                                    {Object.entries(a.feature_snapshot).slice(0, 6).map(([k, v]) => (
                                                        <div key={k} className="feature-item">
                                                            <div className="feature-label">{k.replace(/_/g, " ").toUpperCase()}</div>
                                                            <div className="feature-val">{typeof v === "number" ? v.toFixed(2) : v}</div>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    );
                                })
                        }
                    </div>
                </div>

                <div className="card">
                    <div className="card-header"><span className="card-title">SCORE HISTORY — TABLE STORAGE</span></div>
                    <div className="card-body" style={{ padding: 0 }}>
                        {loading ? <div className="loading"><div className="spinner" />LOADING...</div> :
                            scores.length === 0 ? <div className="empty"><div className="empty-icon">◈</div>No scores yet</div> :
                                <table className="data-table">
                                    <thead><tr><th>TICKER</th><th>SCORE</th><th>ISO</th><th>AE</th><th>FLAG</th></tr></thead>
                                    <tbody>
                                        {scores.slice(0, 15).map((s, i) => (
                                            <tr key={i}>
                                                <td style={{ color: "var(--cyan)", fontFamily: "var(--font-head)" }}>{s.ticker}</td>
                                                <td>
                                                    <div style={{ color: scoreBarColor(s.anomaly_score || 0) }}>{(s.anomaly_score || 0).toFixed(3)}</div>
                                                    <div className="score-bar-bg">
                                                        <div className="score-bar-fill" style={{ width: pct(s.anomaly_score || 0), background: scoreBarColor(s.anomaly_score || 0) }} />
                                                    </div>
                                                </td>
                                                <td style={{ color: "var(--text-dim)" }}>{(s.iso_score || 0).toFixed(3)}</td>
                                                <td style={{ color: "var(--text-dim)" }}>{(s.ae_score || 0).toFixed(3)}</td>
                                                <td><span className={`badge ${s.is_flagged ? "badge-red" : "badge-green"}`}>{s.is_flagged ? "⚑" : "✓"}</span></td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>}
                    </div>
                </div>
            </div>

            <div className="card">
                <div className="card-header"><span className="card-title">ML MODELS — AZURE BLOB / AZURE ML</span></div>
                <div className="card-body">
                    <div className="grid-3">
                        {[
                            { name: "isolation_forest.pkl", type: "IsolationForest", params: "n_estimators=200, contamination=0.02", color: "cyan" },
                            { name: "autoencoder.pt", type: "PyTorch Autoencoder", params: "7→16→8→4→8→16→7 layers", color: "amber" },
                            { name: "scaler.pkl", type: "StandardScaler", params: "7 feature dimensions", color: "green" },
                        ].map((m, i) => (
                            <div key={i} style={{ border: "1px solid var(--border)", borderRadius: 4, padding: 14, background: "var(--bg3)" }}>
                                <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: `var(--${m.color})`, marginBottom: 6 }}>{m.name}</div>
                                <div style={{ fontFamily: "var(--font-head)", fontSize: 14, color: "var(--text)", marginBottom: 4 }}>{m.type}</div>
                                <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-dim)" }}>{m.params}</div>
                                <div style={{ marginTop: 8 }}><span className="badge badge-green">LOADED</span></div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

// ── APP ──────────────────────────────────────────────────────────────────────
const TABS = [
    { id: "m1", label: "Trade Validator", icon: "◈" },
    { id: "m2", label: "FinDistill", icon: "⊕" },
    { id: "m3", label: "Audit Log", icon: "⊟" },
    { id: "m4", label: "Anomaly Detection", icon: "⚑", badge: true },
];

export default function App() {
    const [activeTab, setActiveTab] = useState("m1");
    const [alertCount, setAlertCount] = useState(0);

    useEffect(() => {
        fetch(`${CONFIG.ANOMALY_BASE}/api/get-alerts?code=${CONFIG.GET_ALERTS_KEY}`)
            .then(r => r.json()).then(d => setAlertCount((d.alerts || []).length)).catch(() => { });
    }, []);

    return (
        <>
            <style>{styles}</style>
            <div className="scanline" />
            <div className="app">
                <header className="header">
                    <div className="header-logo">
                        <div className="logo-icon">C</div>
                        <div>
                            <div className="logo-text">CUSTOS</div>
                            <div className="logo-sub">Pre-Trade Risk & Regulatory Intelligence</div>
                        </div>
                    </div>
                    <div className="header-status">
                        <div className="status-pill"><div className="status-dot dot-green" />Event Hubs LIVE</div>
                        <div className="status-pill"><div className="status-dot dot-green" />Redis CONNECTED</div>
                        <div className="status-pill"><div className="status-dot dot-green" />Blob HEALTHY</div>
                        <div className="status-pill"><div className="status-dot dot-amber" />AML ADVISORY</div>
                        <Clock />
                    </div>
                </header>

                <nav className="tabs">
                    {TABS.map(t => (
                        <button key={t.id} className={`tab ${activeTab === t.id ? "active" : ""}`} onClick={() => setActiveTab(t.id)}>
                            {t.icon} {t.label}
                            {t.badge && alertCount > 0 && <span className="tab-badge">{alertCount}</span>}
                        </button>
                    ))}
                </nav>

                <main className="main">
                    {activeTab === "m1" && <Module1Tab />}
                    {activeTab === "m2" && <Module2Tab />}
                    {activeTab === "m3" && <Module3Tab />}
                    {activeTab === "m4" && <Module4Tab />}
                </main>
            </div>
        </>
    );
}
