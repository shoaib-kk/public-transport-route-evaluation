import { useEffect, useState } from "react";
import { getSampleRoutes, evaluateRoute, getRouteHistory, compareRoutes, getFeedStatus } from "./api";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

const gradientBg = "linear-gradient(145deg, #0f172a 0%, #0a2342 50%, #0b5f6c 100%)";

function MetricCard({ label, value, hint }) {
  return (
    <div className="card metric">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      {hint && <div className="metric-hint">{hint}</div>}
    </div>
  );
}

function ComparePanel({ routes, onCompare }) {
  const [left, setLeft] = useState(routes[0]?.route_id);
  const [right, setRight] = useState(routes[1]?.route_id);

  useEffect(() => {
    if (routes.length >= 2) {
      setLeft(routes[0].route_id);
      setRight(routes[1].route_id);
    }
  }, [routes]);

  const handleCompare = async () => {
    if (!left || !right || left === right) return;
    await onCompare([left, right]);
  };

  return (
    <div className="card compare">
      <div className="section-title">Quick Compare</div>
      <div className="select-row">
        <select value={left || ""} onChange={(e) => setLeft(e.target.value)}>
          {routes.map((r) => (
            <option key={r.route_id} value={r.route_id}>
              {r.name}
            </option>
          ))}
        </select>
        <select value={right || ""} onChange={(e) => setRight(e.target.value)}>
          {routes.map((r) => (
            <option key={r.route_id} value={r.route_id}>
              {r.name}
            </option>
          ))}
        </select>
      </div>
      <button className="primary" onClick={handleCompare} disabled={!left || !right || left === right}>
        Compare now
      </button>
    </div>
  );
}

export default function App() {
  const [routes, setRoutes] = useState([]);
  const [selected, setSelected] = useState(null);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [summary, setSummary] = useState(null);
  const [compareResult, setCompareResult] = useState(null);
   const [feedStatus, setFeedStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const data = await getSampleRoutes();
        setRoutes(data);
        setSelected(data[0]?.route_id ?? null);
        const feed = await getFeedStatus();
        setFeedStatus(feed.decoded);
      } catch (err) {
        setError("Could not load sample routes.");
      }
    })();
  }, []);

  const fetchHistory = async (routeId) => {
    try {
      const data = await getRouteHistory(routeId, 120);
      setHistory(data.timeseries || []);
      setSummary(data.summary || null);
    } catch {
      setHistory([]);
      setSummary(null);
    }
  };

  const handleEvaluate = async () => {
    if (!selected) return;
    setLoading(true);
    setError("");
    try {
      const res = await evaluateRoute(selected);
      setResult(res);
      await fetchHistory(res.route_id);
      const feed = await getFeedStatus();
      setFeedStatus(feed.decoded);
    } catch (err) {
      setError("Failed to score route. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const handleCompare = async (routeIds) => {
    setError("");
    try {
      const res = await compareRoutes(routeIds);
      setCompareResult(res);
    } catch {
      setCompareResult(null);
      setError("Compare failed.");
    }
  };

  return (
    <div className="page" style={{ backgroundImage: gradientBg }}>
      <header className="hero">
        <div>
          <p className="eyebrow">NSW Transport</p>
          <h1>Route Reliability Lab</h1>
          <p className="subtitle">
            Predict delays, track reliability, and compare routes using live alerts, vehicle coverage, and historical
            memory.
          </p>
        </div>
        <div className="pill">FastAPI · React · Chart.js</div>
      </header>

      <section className="card control">
        <div className="control-row">
          <div className="control-group">
            <label>Sample route</label>
            <select value={selected || ""} onChange={(e) => setSelected(e.target.value)}>
              {routes.map((route) => (
                <option key={route.route_id} value={route.route_id}>
                  {route.name}
                </option>
              ))}
            </select>
          </div>
          <button className="primary" onClick={handleEvaluate} disabled={!selected || loading}>
            {loading ? "Scoring..." : "Score now"}
          </button>
        </div>
        {error && <div className="error">{error}</div>}
      </section>

      {result && (
        <section className="grid">
          <div className="card">
            <div className="section-title">Current outlook · {result.route_name}</div>
            <div className="metrics">
              <MetricCard label="Reliability" value={`${result.route_reliability_score}/100`} />
              <MetricCard label="Expected delay (heuristic)" value={`${result.expected_delay_minutes} min`} />
              <MetricCard
                label="Predicted delay (ML)"
                value={
                  result.predicted_delay_minutes !== null
                    ? `${result.predicted_delay_minutes.toFixed(1)} min`
                    : "–"
                }
                hint={
                  result.delay_over_threshold_probability !== null
                    ? `${(result.delay_over_threshold_probability * 100).toFixed(1)}% chance > 10 min`
                    : ""
                }
              />
            </div>
            <div className="muted">{result.explanation}</div>
          </div>

          <div className="card">
            <div className="section-title">Rolling health</div>
            {summary ? (
              <div className="metrics">
                <MetricCard label="Samples" value={summary.count} />
                <MetricCard label="Avg delay" value={`${summary.delay_mean?.toFixed(1) ?? 0} min`} />
                <MetricCard label="95th delay" value={`${summary.delay_p95?.toFixed(1) ?? 0} min`} />
                <MetricCard label="Avg reliability" value={`${summary.reliability_mean?.toFixed(1) ?? 0}/100`} />
              </div>
            ) : (
              <div className="muted">No history yet. Score a route to build trends.</div>
            )}
          </div>
        </section>
      )}

      <section className="grid">
        <div className="card chart">
          <div className="section-title">Reliability over time</div>
          {history.length === 0 ? (
            <div className="muted">No history yet.</div>
          ) : (
            <Line
              data={{
                labels: history.map((p) => new Date(p.created_at).toLocaleString()),
                datasets: [
                  {
                    label: "Reliability",
                    data: history.map((p) => p.route_reliability_score),
                    borderColor: "#22d3ee",
                    backgroundColor: "rgba(34, 211, 238, 0.2)",
                    tension: 0.25,
                  },
                ],
              }}
              options={{ scales: { y: { min: 0, max: 100 } } }}
            />
          )}
        </div>

        <div className="card chart">
          <div className="section-title">Delay over time</div>
          {history.length === 0 ? (
            <div className="muted">No history yet.</div>
          ) : (
            <Line
              data={{
                labels: history.map((p) => new Date(p.created_at).toLocaleString()),
                datasets: [
                  {
                    label: "Expected delay (min)",
                    data: history.map((p) => p.expected_delay_minutes),
                    borderColor: "#f97316",
                    backgroundColor: "rgba(249, 115, 22, 0.2)",
                    tension: 0.25,
                  },
                ],
              }}
              options={{ scales: { y: { beginAtZero: true } } }}
            />
          )}
        </div>
      </section>

      <section className="grid">
        <ComparePanel routes={routes} onCompare={handleCompare} />

        <div className="card">
          <div className="section-title">Feed health</div>
          {feedStatus ? (
            <div className="metrics">
              <MetricCard label="Alerts in memory" value={feedStatus.alerts_in_memory} />
              <MetricCard label="Vehicle positions" value={feedStatus.vehicle_positions_in_memory} />
              <MetricCard
                label="Vehicle feed age"
                value={
                  feedStatus.vehicle_feed_age_seconds !== null
                    ? `${feedStatus.vehicle_feed_age_seconds}s`
                    : "unknown"
                }
              />
              <MetricCard
                label="Static feed"
                value={feedStatus.static?.available ? "available" : "missing"}
                hint={feedStatus.static?.snapshot_path}
              />
              <MetricCard
                label="Historical feed"
                value={feedStatus.historical?.available ? "available" : "missing"}
                hint={feedStatus.historical?.snapshot_path}
              />
            </div>
          ) : (
            <div className="muted">Feed status not available yet.</div>
          )}
        </div>
      </section>

      {result && result.legs && (
        <section className="card">
          <div className="section-title">Per-leg breakdown</div>
          <div className="legs-grid">
            {result.legs.map((leg) => (
              <div key={leg.leg_id} className="card mini">
                <div className="metric-label">{leg.line}</div>
                <div className="metric-value">{leg.route_id}</div>
                <div className="metric-hint">Risk: {leg.current_risk}</div>
                <div className="metric-hint">Expected delay: {leg.expected_delay_minutes} min</div>
                <div className="metric-hint">Matched alerts: {leg.matched_alerts}</div>
                <div className="metric-hint">Active vehicles: {leg.active_vehicles}</div>
                <div className="metric-hint">Transfer risk: {leg.transfer_risk}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {compareResult && (
        <section className="card">
          <div className="section-title">Comparison result</div>
          <div className="muted">Ordered by reliability (desc)</div>
          <div className="compare-results">
            {compareResult.map((item) => (
              <div key={item.route_id} className="card mini">
                <div className="metric-label">{item.route_name}</div>
                <div className="metric-value">{item.route_reliability_score}/100</div>
                <div className="metric-hint">Delay ~ {item.expected_delay_minutes} min</div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
