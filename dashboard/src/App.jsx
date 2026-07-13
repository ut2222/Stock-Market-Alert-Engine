import { useState, useEffect, useRef } from "react"
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import axios from "axios"
import "./App.css"

const API = "http://localhost:8000/api"
const WS_URL = "ws://localhost:8000/ws/live"
const SYMBOLS = ["AAPL", "TSLA", "GOOGL"]
const COLORS = { AAPL: "#7F77DD", TSLA: "#1D9E75", GOOGL: "#EF9F27" }

export default function App() {
  const [selected, setSelected]     = useState("AAPL")
  const [history, setHistory]       = useState([])
  const [stats, setStats]           = useState(null)
  const [livePrices, setLivePrices] = useState({})
  const [alerts, setAlerts]         = useState([])
  const [firedAlerts, setFiredAlerts] = useState([])
  const [newRule, setNewRule]       = useState({ symbol: "AAPL", rule_type: "price_above", threshold: "", window: 14, description: "" })
  const wsRef = useRef(null)

  // Load history + stats when symbol changes
  useEffect(() => {
    axios.get(`${API}/tickers/${selected}/history?days=60`)
      .then(r => setHistory(r.data.bars.slice().reverse().map((b, i) => ({
        day: i + 1, date: b.timestamp, close: b.close, high: b.high, low: b.low
      }))))
      .catch(console.error)

    axios.get(`${API}/tickers/${selected}/stats`)
      .then(r => setStats(r.data))
      .catch(console.error)
  }, [selected])

  // Load existing alert rules
  useEffect(() => {
    axios.get(`${API}/alerts`).then(r => setAlerts(r.data.rules)).catch(console.error)
  }, [])

  // WebSocket live feed
  useEffect(() => {
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === "price_update") {
        const updated = {}
        data.ticks.forEach(t => { updated[t.symbol] = t })
        setLivePrices(prev => ({ ...prev, ...updated }))
      }
    }
    ws.onerror = () => console.log("WS error — is the API server running?")
    return () => ws.close()
  }, [])

  const handleCreateRule = () => {
    if (!newRule.threshold) return
    axios.post(`${API}/alerts`, { ...newRule, threshold: parseFloat(newRule.threshold) })
      .then(() => axios.get(`${API}/alerts`).then(r => setAlerts(r.data.rules)))
      .catch(console.error)
  }

  const handleEvaluate = () => {
    axios.post(`${API}/alerts/evaluate`)
      .then(r => setFiredAlerts(r.data.alerts))
      .catch(console.error)
  }

  const handleDelete = (id) => {
    axios.delete(`${API}/alerts/${id}`)
      .then(() => setAlerts(prev => prev.filter(r => r.id !== id)))
      .catch(console.error)
  }

  const live = livePrices[selected]

  return (
    <div className="app">
      {/* Header */}
      <div className="header">
        <span className="header-title">📈 Stock Alert Engine</span>
        <span className="header-sub">Live DSA-powered market dashboard</span>
      </div>

      {/* Watchlist */}
      <div className="watchlist">
        {SYMBOLS.map(s => {
          const p = livePrices[s]
          return (
            <div key={s} className={`ticker-card ${selected === s ? "active" : ""}`} onClick={() => setSelected(s)}>
              <div className="ticker-symbol" style={{ color: COLORS[s] }}>{s}</div>
              <div className="ticker-price">${p ? p.price.toFixed(2) : "..."}</div>
              <div className={`ticker-change ${p && p.change >= 0 ? "up" : "down"}`}>
                {p ? `${p.change >= 0 ? "▲" : "▼"} ${Math.abs(p.change_pct).toFixed(3)}%` : "—"}
              </div>
            </div>
          )
        })}
      </div>

      <div className="main">
        {/* Chart */}
        <div className="panel chart-panel">
          <div className="panel-title">
            <span>{selected} — 60 day close price</span>
            {live && <span className="live-badge">● LIVE ${live.price.toFixed(2)}</span>}
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3a" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#888" }} interval={9} />
              <YAxis domain={["auto", "auto"]} tick={{ fontSize: 10, fill: "#888" }} />
              <Tooltip contentStyle={{ background: "#1a1a2e", border: "1px solid #333", borderRadius: 8 }} />
              <Line type="monotone" dataKey="close" stroke={COLORS[selected]} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Stats from segment tree */}
        {stats && (
          <div className="panel stats-panel">
            <div className="panel-title">Segment tree range queries</div>
            {Object.entries(stats.range_queries).map(([label, val]) => (
              <div key={label} className="stat-row">
                <span className="stat-label">{label.replace(/_/g, " ")}</span>
                <span className="stat-val">H: <b>${val.high.toFixed(2)}</b></span>
                <span className="stat-val">L: <b>${val.low.toFixed(2)}</b></span>
                <span className="stat-spread">±${val.spread.toFixed(2)}</span>
              </div>
            ))}
          </div>
        )}

        {/* Alert rules */}
        <div className="panel alerts-panel">
          <div className="panel-title">Alert rules</div>

          {/* Create rule form */}
          <div className="rule-form">
            <select value={newRule.symbol} onChange={e => setNewRule({ ...newRule, symbol: e.target.value })}>
              {SYMBOLS.map(s => <option key={s}>{s}</option>)}
            </select>
            <select value={newRule.rule_type} onChange={e => setNewRule({ ...newRule, rule_type: e.target.value })}>
              <option value="price_above">Price above</option>
              <option value="price_below">Price below</option>
              <option value="drop_pct">Drop % in window</option>
              <option value="range_exceeds">Range exceeds</option>
            </select>
            <input type="number" placeholder="Threshold" value={newRule.threshold}
              onChange={e => setNewRule({ ...newRule, threshold: e.target.value })} />
            <input type="text" placeholder="Description" value={newRule.description}
              onChange={e => setNewRule({ ...newRule, description: e.target.value })} />
            <button className="btn-add" onClick={handleCreateRule}>+ Add</button>
            <button className="btn-eval" onClick={handleEvaluate}>⚡ Evaluate</button>
          </div>

          {/* Rules list */}
          <div className="rules-list">
            {alerts.length === 0 && <div className="empty">No rules yet — add one above</div>}
            {alerts.map(r => (
              <div key={r.id} className={`rule-row ${r.triggered ? "triggered" : ""}`}>
                <span className="rule-symbol" style={{ color: COLORS[r.symbol] }}>{r.symbol}</span>
                <span className="rule-type">{r.rule_type}</span>
                <span className="rule-threshold">${r.threshold}</span>
                <span className="rule-desc">{r.description}</span>
                {r.triggered && <span className="fired-badge">FIRED</span>}
                <button className="btn-del" onClick={() => handleDelete(r.id)}>✕</button>
              </div>
            ))}
          </div>

          {/* Fired alerts */}
          {firedAlerts.length > 0 && (
            <div className="fired-alerts">
              <div className="panel-title" style={{ marginTop: 12 }}>⚡ Alerts fired</div>
              {firedAlerts.map((a, i) => (
                <div key={i} className="fired-row">
                  <span className="fired-symbol">{a.symbol}</span>
                  <span className="fired-msg">{a.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}