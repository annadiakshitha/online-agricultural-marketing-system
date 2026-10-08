/* Farmer dashboard: compact weather + top advisories */
(async () => {
  const box = document.getElementById('fdWeather'); if (!box) return;
  const body = document.getElementById('fdWxBody');
  try {
    const d = await WX.forecast(box.dataset.lat, box.dataset.lng), c = d.current, w = WX.info(c.weather_code), adv = WX.advisories(d).slice(0, 3);
    body.innerHTML = `<div class="fd-wx"><i class="fa-solid fa-${w.icon} ico"></i><div><div class="big">${Math.round(c.temperature_2m)}°C</div><small class="muted">${w.label} · humidity ${c.relative_humidity_2m}% · wind ${Math.round(c.wind_speed_10m)} km/h</small></div></div>
      <div class="adv" style="margin-top:14px">${adv.map(a => `<div class="${a.l}"><i class="fa-solid fa-${a.i}"></i><span>${escapeHTML(a.t)}</span></div>`).join('')}</div>`;
  } catch (e) { body.innerHTML = '<p class="muted">Weather is unavailable right now. Check your internet connection.</p>'; }
})();
