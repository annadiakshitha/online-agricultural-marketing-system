/* Order tracking map – Leaflet + CARTO dark tiles. Reads GET /api/order/<id>/tracking. */
(async () => {
  const el = document.getElementById('trackMap'); if (!el) return;
  const $ = id => document.getElementById(id);
  let t;
  try { const r = await fetch(`/api/order/${el.dataset.order}/tracking`); t = await r.json(); if (!t.ok) throw 0; } catch (e) { $('trackCard').hidden = true; return; }

  const stops = t.stops, cur = t.current;
  const passed = stops.filter((s, i) => i === 0 || t.progress > 0).length;     // for the "now at" label
  $('tkStatus').textContent = t.status;
  $('tkDist').textContent = t.distance_km + ' km';
  $('tkEtaLabel').textContent = t.delivered ? 'Delivered' : 'Estimated delivery';
  $('tkEta').textContent = t.delivered ? 'Completed' : t.eta;
  const here = t.stages.find(s => s.current); $('tkNow').textContent = here ? here.place : stops[0].name;
  $('tkNote').textContent = (t.approximate ? 'Delivery point shown at the state centre because the district was not recognised. ' : '') + t.note;
  $('tkRoute').textContent = stops.map(s => s.name).join(' → ');

  if (!window.L) { $('trackMap').hidden = true; $('trackFallback').hidden = false; return; }

  const map = L.map(el, { scrollWheelZoom: false, zoomControl: true, attributionControl: true });
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    maxZoom: 18, subdomains: 'abcd', attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>' }).addTo(map);
  el.addEventListener('click', () => map.scrollWheelZoom.enable());

  const icon = (cls, fa, size = 36) => L.divIcon({ className: '', html: `<div class="tk-pin ${cls}"><i class="fa-solid fa-${fa}"></i></div>`, iconSize: [size, size], iconAnchor: [size / 2, size] });
  const pts = stops.map(s => [s.lat, s.lng]);
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  stops.forEach((s, i) => {
    const first = i === 0, last = i === stops.length - 1;
    L.marker(pts[i], { icon: icon(first ? 'tk-origin' : last ? 'tk-dest' : 'tk-hub', first ? 'warehouse' : last ? 'house' : 'boxes-stacked', first || last ? 36 : 26) })
      .addTo(map).bindPopup(`<b>${esc(s.kind)}</b><br>${esc(s.name)}`);
  });

  // full route (dashed) + travelled part (solid, glowing)
  L.polyline(pts, { color: '#3b5a44', weight: 4, dashArray: '8 10' }).addTo(map);
  const cum = [0]; for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + map.distance(pts[i - 1], pts[i]));
  const total = cum[cum.length - 1] || 1, target = t.progress * total;
  const travelled = [pts[0]];
  for (let i = 1; i < pts.length; i++) { if (cum[i] <= target) travelled.push(pts[i]); else break; }
  const path = travelled.concat([[cur.lat, cur.lng]]);
  L.polyline(path, { color: '#39D353', weight: 9, opacity: .18 }).addTo(map);
  const line = L.polyline(path, { color: '#39D353', weight: 4 }).addTo(map);

  // vehicle marker – drives from the start to the current position
  const vehicle = L.marker(pts[0], { zIndexOffset: 1000, icon: L.divIcon({ className: '', iconSize: [46, 46], iconAnchor: [23, 23],
    html: `<div class="tk-truck ${t.delivered ? 'done' : ''}"><span><i class="fa-solid fa-${t.delivered ? 'circle-check' : 'truck-fast'}"></i></span></div>` }) }).addTo(map);
  vehicle.bindPopup(`<b>${esc(t.status)}</b><br>${esc(here ? here.place : '')}`);
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const seg = []; for (let i = 0; i < path.length - 1; i++) seg.push(map.distance(path[i], path[i + 1]));
  const pathLen = seg.reduce((a, b) => a + b, 0);
  const at = d => { let run = 0; for (let i = 0; i < seg.length; i++) { if (run + seg[i] >= d || i === seg.length - 1) { const f = seg[i] ? (d - run) / seg[i] : 0; return [path[i][0] + (path[i + 1][0] - path[i][0]) * f, path[i][1] + (path[i + 1][1] - path[i][1]) * f]; } run += seg[i]; } return path[path.length - 1]; };
  if (reduce || pathLen === 0) vehicle.setLatLng([cur.lat, cur.lng]);
  else { const t0 = performance.now(), dur = 2600; const step = n => { const k = Math.min(1, (n - t0) / dur), e = 1 - Math.pow(1 - k, 3); vehicle.setLatLng(at(pathLen * e)); if (k < 1) requestAnimationFrame(step); else vehicle.openPopup(); }; requestAnimationFrame(step); }

  map.fitBounds(L.latLngBounds(pts).pad(0.25));
  setTimeout(() => map.invalidateSize(), 300);

  // "My location" – shows where the customer is and the straight-line distance to the delivery point
  let me;
  $('trackLocate').onclick = () => {
    if (!navigator.geolocation) { toast('Location is not supported on this device', 'error'); return; }
    navigator.geolocation.getCurrentPosition(p => {
      const ll = [p.coords.latitude, p.coords.longitude]; if (me) me.remove();
      const km = (map.distance(ll, pts[pts.length - 1]) / 1000).toFixed(0);
      me = L.marker(ll, { icon: icon('tk-me', 'user', 32) }).addTo(map).bindPopup(`<b>You are here</b><br>${km} km from the delivery point`).openPopup();
      map.fitBounds(L.latLngBounds(pts.concat([ll])).pad(0.2));
    }, () => toast('Could not get your location. Please allow location access.', 'error'), { timeout: 10000 });
  };
})();
