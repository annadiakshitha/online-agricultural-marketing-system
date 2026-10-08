/* Crop Doctor: diagnosis + damage-spot overlay on the uploaded photo */
(() => {
  const form = document.getElementById('cdForm'); if (!form) return;
  const $ = id => document.getElementById(id), esc = escapeHTML;
  const photo = $('cdPhoto'), prev = $('cdPreview');
  let photoURL = null;
  photo.addEventListener('change', () => {
    const f = photo.files[0];
    if (photoURL) URL.revokeObjectURL(photoURL);
    if (!f) { photoURL = null; prev.hidden = true; $('cdDropText').hidden = false; return; }
    photoURL = URL.createObjectURL(f); prev.src = photoURL; prev.hidden = false; $('cdDropText').hidden = true;
  });
  const list = (t, a) => a && a.length ? `<h4>${t}</h4><ul>${a.map(x => `<li>${esc(x)}</li>`).join('')}</ul>` : '';
  const SEV = { low: 'Low', medium: 'Medium', high: 'High' };

  /* Fallback detector (runs in the browser) when AI spots are not available:
     finds yellow / brown / dark patches that sit on or next to green leaf tissue. */
  function detectSpots(img) {
    const W = 180, sc = W / img.naturalWidth, H = Math.max(1, Math.round(img.naturalHeight * sc));
    const c = document.createElement('canvas'); c.width = W; c.height = H;
    const g = c.getContext('2d', { willReadFrequently: true }); g.drawImage(img, 0, 0, W, H);
    const d = g.getImageData(0, 0, W, H).data, N = W * H;
    const green = new Uint8Array(N), bad = new Uint8Array(N);
    for (let i = 0; i < N; i++) {
      const r = d[i * 4] / 255, gg = d[i * 4 + 1] / 255, b = d[i * 4 + 2] / 255;
      const mx = Math.max(r, gg, b), mn = Math.min(r, gg, b), df = mx - mn, s = mx ? df / mx : 0;
      let h = 0;
      if (df) h = mx === r ? ((gg - b) / df) % 6 : mx === gg ? (b - r) / df + 2 : (r - gg) / df + 4;
      h = (h * 60 + 360) % 360;
      if (h >= 70 && h <= 165 && s > .22 && mx > .15) green[i] = 1;
      else if (((h < 68 || h > 340) && s > .28 && mx > .18) || (mx < .22 && mn < .2)) bad[i] = 1;
    }
    const integ = m => { const I = new Int32Array((W + 1) * (H + 1)); for (let y = 0; y < H; y++) { let row = 0; for (let x = 0; x < W; x++) { row += m[y * W + x]; I[(y + 1) * (W + 1) + x + 1] = I[y * (W + 1) + x + 1] + row; } } return I; };
    const IG = integ(green);
    const sum = (I, x, y, r) => { const x0 = Math.max(0, x - r), y0 = Math.max(0, y - r), x1 = Math.min(W, x + r + 1), y1 = Math.min(H, y + r + 1); return I[y1 * (W + 1) + x1] - I[y0 * (W + 1) + x1] - I[y1 * (W + 1) + x0] + I[y0 * (W + 1) + x0]; };
    const mask = new Uint8Array(N);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const i = y * W + x; if (!bad[i]) continue;
      const near = sum(IG, x, y, 4), wide = sum(IG, x, y, 12), area = (Math.min(W, x + 13) - Math.max(0, x - 12)) * (Math.min(H, y + 13) - Math.max(0, y - 12));
      if (near > 3 && wide / area > .18) mask[i] = 1;
    }
    /* merge nearby pixels, then connected components */
    const m2 = new Uint8Array(N);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (mask[y * W + x]) for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) { const xx = x + dx, yy = y + dy; if (xx >= 0 && yy >= 0 && xx < W && yy < H) m2[yy * W + xx] = 1; }
    const seen = new Uint8Array(N), out = [];
    for (let s0 = 0; s0 < N; s0++) {
      if (!m2[s0] || seen[s0]) continue;
      const st = [s0]; seen[s0] = 1; let x0 = W, y0 = H, x1 = 0, y1 = 0, cnt = 0, hits = 0;
      while (st.length) {
        const p = st.pop(), x = p % W, y = (p / W) | 0; cnt++; if (mask[p]) hits++;
        if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
        if (x > 0 && m2[p - 1] && !seen[p - 1]) { seen[p - 1] = 1; st.push(p - 1); }
        if (x < W - 1 && m2[p + 1] && !seen[p + 1]) { seen[p + 1] = 1; st.push(p + 1); }
        if (y > 0 && m2[p - W] && !seen[p - W]) { seen[p - W] = 1; st.push(p - W); }
        if (y < H - 1 && m2[p + W] && !seen[p + W]) { seen[p + W] = 1; st.push(p + W); }
      }
      if (hits / N < .0012 || hits / N > .45) continue;
      out.push({ hits, x: x0 / W * 100, y: y0 / H * 100, w: (x1 - x0 + 1) / W * 100, h: (y1 - y0 + 1) / H * 100 });
    }
    out.sort((a, b) => b.hits - a.hits);
    return out.slice(0, 6).map((o, i) => {
      const f = o.hits / N, sev = f > .04 ? 'high' : f > .012 ? 'medium' : 'low';
      return { label: 'Possible damage', severity: sev, x: +o.x.toFixed(1), y: +o.y.toFixed(1), w: +o.w.toFixed(1), h: +o.h.toFixed(1) };
    });
  }

  const loadImg = url => new Promise(res => { const i = new Image(); i.onload = () => res(i); i.onerror = () => res(null); i.src = url; });

  function photoBlock(url, spots, estimated) {
    const boxes = spots.map((s, i) => `<span class="cd-box sev-${s.severity}" style="left:${s.x}%;top:${s.y}%;width:${s.w}%;height:${s.h}%"><b>${i + 1}</b></span>`).join('');
    const legend = spots.length
      ? `<ol class="cd-legend">${spots.map((s, i) => `<li><b class="sev-${s.severity}">${i + 1}</b><span>${esc(s.label)}</span><em>${SEV[s.severity]}</em></li>`).join('')}</ol>`
      : '<p class="muted cd-nospot">No clearly damaged area could be marked on this photo.</p>';
    return `<div class="cd-photo"><div class="cd-frame"><img src="${url}" alt="Your plant photo with damaged areas marked">${boxes}</div>
      <div class="cd-photo-meta"><h4><i class="fa-solid fa-location-crosshairs"></i> Damaged areas found${spots.length ? ` (${spots.length})` : ''}</h4>${legend}
      ${estimated && spots.length ? '<p class="cd-est">Marked by a quick colour scan on your device. Enable AI mode for more accurate spots.</p>' : ''}</div></div>`;
  }

  form.addEventListener('submit', async e => {
    e.preventDefault(); const err = $('cdError'); err.hidden = true;
    const fd = new FormData(), file = photo.files[0];
    if (file) fd.append('photo', file);
    fd.append('crop', $('cdCrop').value); fd.append('note', $('cdNote').value);
    fd.append('symptoms', [...form.querySelectorAll('.sym input:checked')].map(i => i.value).join(','));
    const btn = $('cdGo'); btn.disabled = true;
    $('cdResult').innerHTML = '<div class="cd-spin"><i class="fa-solid fa-circle-notch"></i><p>Examining your crop…</p></div>';
    const r = await api('/api/crop-doctor', { method: 'POST', form: fd }); btn.disabled = false;
    if (!r.ok) { $('cdResult').innerHTML = '<div class="cd-empty"><i class="fa-solid fa-leaf"></i><p>Your result will appear here.</p></div>'; err.textContent = r.error || 'Something went wrong.'; err.hidden = false; return; }
    if (r.not_plant) { $('cdResult').innerHTML = '<div class="cd-empty"><i class="fa-solid fa-image"></i><p>That photo does not look like a plant. Please upload a clear close-up of the affected leaf.</p></div>'; return; }

    let photoHTML = '';
    if (file && photoURL) {
      let spots = Array.isArray(r.spots) ? r.spots : [], estimated = false;
      if (r.mode !== 'ai' || !spots.length) {
        const img = await loadImg(photoURL);
        if (img && (r.mode !== 'ai')) { try { spots = detectSpots(img); estimated = true; } catch (_) { spots = []; } }
      }
      photoHTML = photoBlock(photoURL, spots, estimated);
    }
    const prods = (r.products || []).map(p => `<a class="ai-prod" href="${esc(p.url)}"><img src="${esc(p.image)}" alt="${esc(p.name)}"><div><b>${esc(p.name)}</b><span><em>${formatINR(p.price)}</em>${esc(p.seller)}</span></div><button type="button" data-add="${p.id}">Add to Cart</button></a>`).join('');
    $('cdResult').innerHTML = `<div class="cd-res">${r.notice ? `<p class="cd-note"><i class="fa-solid fa-circle-info"></i> ${esc(r.notice)}</p>` : ''}
      ${photoHTML}
      <div class="cd-head"><h2>${esc(r.condition || 'Result')}</h2>${r.confidence && r.confidence !== 'n/a' ? `<span class="conf">${esc(r.confidence)} confidence</span>` : ''}</div>
      <p class="muted">${esc(r.crop || '')}${r.crop ? ' · ' : ''}${esc(r.summary || '')}</p>
      ${r.causes && r.causes.length ? `<h4>Possible causes</h4><ul>${r.causes.map(c => `<li><b>${esc(c.name)}</b>${c.why ? ': ' + esc(c.why) : ''}</li>`).join('')}</ul>` : ''}
      ${list('What to do', r.actions)}${list('Prevention', r.prevention)}
      ${r.see_expert ? '<p class="cd-note"><i class="fa-solid fa-user-doctor"></i> If this spreads or you are unsure, show the plant to your local Krishi Vigyan Kendra (KVK) or agriculture officer before spraying. Always follow the product label for dose and safety.</p>' : ''}
      ${prods ? `<h4>Helpful products</h4><div class="cd-prods">${prods}</div>` : ''}</div>`;
    $('cdResult').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });
})();
