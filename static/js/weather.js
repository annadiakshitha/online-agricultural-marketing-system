/* Weather & farm advisory page */
(() => {
  const root = document.getElementById('wx'); if (!root) return;
  const $ = id => document.getElementById(id), esc = escapeHTML;
  async function show(lat, lng, name) {
    $('wxPlace').textContent = name; $('wxBody').innerHTML = '<div class="sk" style="height:180px;border-radius:16px"></div>';
    try {
      const d = await WX.forecast(lat, lng), c = d.current, w = WX.info(c.weather_code), x = d.daily;
      const adv = WX.advisories(d);
      $('wxBody').innerHTML = `
        <div class="wx-now"><i class="fa-solid fa-${w.icon} ico"></i><div><div class="big">${Math.round(c.temperature_2m)}°C</div><div>${w.label}</div>
          <div class="meta"><span>Humidity <b>${c.relative_humidity_2m}%</b></span><span>Wind <b>${Math.round(c.wind_speed_10m)} km/h</b></span><span>Rain now <b>${c.precipitation} mm</b></span></div></div></div>
        <div class="wx-days">${x.time.map((t, i) => { const k = WX.info(x.weather_code[i]); return `<div class="wx-day"><small>${WX.day(t, i)}</small><i class="fa-solid fa-${k.icon}"></i><b>${Math.round(x.temperature_2m_max[i])}° <small>${Math.round(x.temperature_2m_min[i])}°</small></b><small>${x.precipitation_probability_max[i] ?? 0}% · ${Math.round(x.precipitation_sum[i] || 0)} mm</small></div>`; }).join('')}</div>
        <h2 style="margin:0 0 12px">Farm advisory</h2><div class="adv">${adv.map(a => `<div class="${a.l}"><i class="fa-solid fa-${a.i}"></i><span>${esc(a.t)}</span></div>`).join('')}</div>`;
    } catch (e) { $('wxBody').innerHTML = '<p class="form-error">Could not load the forecast. Please check your internet connection and try again.</p>'; }
  }
  show(+root.dataset.lat, +root.dataset.lng, root.dataset.name);
  $('wxSearch').addEventListener('submit', async e => {
    e.preventDefault(); const q = $('wxQ').value.trim(); if (q.length < 2) return;
    const box = $('wxResults'); box.hidden = false; box.innerHTML = '<span class="muted">Searching…</span>';
    try {
      const r = await WX.search(q);
      box.innerHTML = r.length ? r.map(p => `<button type="button" data-lat="${p.latitude}" data-lng="${p.longitude}" data-name="${esc(p.name)}, ${esc(p.admin1 || '')}">${esc(p.name)}, ${esc(p.admin1 || '')} ${p.admin2 ? '· ' + esc(p.admin2) : ''}</button>`).join('') : '<span class="muted">No place found. Try a nearby town.</span>';
    } catch (err) { box.innerHTML = '<span class="muted">Search failed. Check your connection.</span>'; }
  });
  $('wxResults').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; $('wxResults').hidden = true; show(+b.dataset.lat, +b.dataset.lng, b.dataset.name); });
  $('wxGeo').onclick = () => navigator.geolocation ? navigator.geolocation.getCurrentPosition(p => show(p.coords.latitude, p.coords.longitude, 'Your location'), () => toast('Could not get your location', 'error')) : toast('Location not supported', 'error');
})();
