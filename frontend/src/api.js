import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export async function getSampleRoutes() {
  const res = await axios.get(`${API_BASE}/sample-routes`);
  return res.data;
}

export async function evaluateRoute(sampleRouteId) {
  const res = await axios.post(`${API_BASE}/evaluate-route`, {
    sample_route_id: sampleRouteId,
  });
  return res.data;
}

export async function getRouteHistory(routeId, limit = 120) {
  const res = await axios.get(`${API_BASE}/route-history/${routeId}`, {
    params: { limit },
  });
  return res.data;
}

export async function compareRoutes(routeIds) {
  const res = await axios.post(`${API_BASE}/compare-routes`, {
    sample_route_ids: routeIds,
  });
  return res.data;
}

export async function getFeedStatus() {
  const res = await axios.get(`${API_BASE}/latest-feed-status`);
  return res.data;
}
