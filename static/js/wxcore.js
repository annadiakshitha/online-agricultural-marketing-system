/* Shared Open-Meteo helpers (free, no API key). Used by the weather page and the farmer dashboard. */
const WX = (() => {
  const CODES = [[[0], 'Clear sky', 'sun'], [[1, 2], 'Partly cloudy', 'cloud-sun'], [[3], 'Overcast', 'cloud'], [[45, 48], 'Fog', 'smog'],
    [[51, 53, 55, 56, 57], 'Drizzle', 'cloud-rain'], [[61, 63, 65, 66, 67], 'Rain', 'cloud-showers-heavy'], [[71, 73, 75, 77], 'Snow', 'snowflake'],
    [[80, 81, 82], 'Showers', 'cloud-showers-heavy'], [[95, 96, 99], 'Thunderstorm', 'cloud-bolt']];
  const info = c => { const m = CODES.find(x => x[0].includes(c)); return m ? { label: m[1], icon: m[2] } : { label: 'Cloudy', icon: 'cloud' }; };
  async function forecast(lat, lng) {
    const u = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code`
      + `&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max&timezone=auto&forecast_days=7`;
    const r = await fetch(u); if (!r.ok) throw new Error('weather'); return r.json();
  }
  async function search(name) {
    const r = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(name)}&count=5&language=en&country_code=IN`);
    return (await r.json()).results || [];
  }
  const day = (iso, i) => i === 0 ? 'Today' : new Date(iso + 'T00:00').toLocaleDateString('en-IN', { weekday: 'short' });
  function advisories(d) {
    const x = d.daily, out = [], n = k => x[k].slice(0, 3).map(v => v ?? 0);
    const rain3 = n('precipitation_sum').reduce((a, b) => a + b, 0), prob2 = Math.max(...x.precipitation_probability_max.slice(0, 2).map(v => v ?? 0));
    const wind2 = Math.max(...x.wind_speed_10m_max.slice(0, 2).map(v => v ?? 0)), tmax3 = Math.max(...n('temperature_2m_max')), tmin3 = Math.min(...n('temperature_2m_min'));
    if (prob2 >= 50 || wind2 >= 20) out.push({ l: 'bad', i: 'spray-can-sparkles', t: `Avoid spraying pesticides or foliar nutrients in the next 2 days (${prob2 >= 50 ? 'rain likely' : 'strong wind'} ${wind2 >= 20 ? `up to ${Math.round(wind2)} km/h` : ''}).` });
    else out.push({ l: 'ok', i: 'spray-can-sparkles', t: 'Good spraying window: low rain chance and light wind in the next 2 days. Spray early morning or evening.' });
    if (rain3 >= 15) out.push({ l: 'warn', i: 'droplet-slash', t: `About ${Math.round(rain3)} mm of rain expected in 3 days: skip irrigation and make sure fields drain well.` });
    else if (rain3 < 3 && tmax3 >= 33) out.push({ l: 'warn', i: 'droplet', t: 'Dry and hot spell ahead: irrigate at the right stage, preferably early morning, and use mulch to hold moisture.' });
    else out.push({ l: 'ok', i: 'droplet', t: 'Normal irrigation schedule is fine. Check soil moisture before watering.' });
    if (rain3 >= 10 && rain3 < 40) out.push({ l: 'ok', i: 'seedling', t: 'Soil should have good moisture after the coming rain: a suitable time for sowing or transplanting if your crop calendar allows.' });
    if (tmax3 >= 40) out.push({ l: 'bad', i: 'temperature-high', t: `Heat alert (up to ${Math.round(tmax3)}°C): avoid midday field work, irrigate lightly in morning/evening, and protect nursery beds.` });
    if (tmin3 <= 8) out.push({ l: 'warn', i: 'temperature-low', t: `Cold nights (down to ${Math.round(tmin3)}°C): protect young seedlings with covers or light irrigation in the evening.` });
    if (x.precipitation_sum.slice(0, 3).every(v => (v ?? 0) < 1) && prob2 < 30) out.push({ l: 'ok', i: 'sun', t: 'Dry days ahead: good for harvesting, threshing and drying produce.' });
    return out;
  }
  return { forecast, search, info, day, advisories };
})();
