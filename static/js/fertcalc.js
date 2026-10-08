/* Fertilizer calculator */
(() => {
  const form = document.getElementById('fcForm'); if (!form) return;
  const $ = id => document.getElementById(id), qs = new URLSearchParams(location.search);
  if (qs.get('crop') && [...$('fcCrop').options].some(o => o.value === qs.get('crop'))) $('fcCrop').value = qs.get('crop');
  if (qs.get('size')) $('fcSize').value = qs.get('size');
  const num = n => Number(n).toLocaleString('en-IN');
  async function calc() {
    const err = $('fcError'); err.hidden = true;
    const r = await api(`/api/fertilizer-calc?crop=${$('fcCrop').value}&size=${encodeURIComponent($('fcSize').value)}&unit=${$('fcUnit').value}`);
    if (!r.ok) { err.textContent = r.error || 'Could not calculate.'; err.hidden = false; return; }
    const prod = p => p ? `<a class="ai-prod" href="${escapeHTML(p.url)}"><img src="${escapeHTML(p.image)}" alt="${escapeHTML(p.name)}"><div><b>${escapeHTML(p.name)}</b><span><em>${formatINR(p.price)}</em>${escapeHTML(p.seller)}</span></div><button type="button" data-add="${p.id}">Add to Cart</button></a>` : '';
    $('fcResult').innerHTML = `<div class="cd-res"><h2 style="margin:0">${escapeHTML(r.crop)} · ${r.acres} acre${r.acres === 1 ? '' : 's'}</h2>
      <h4>Nutrients needed</h4><div class="npk-bar"><span>N ${num(r.nutrients.n)} kg</span><span>P₂O₅ ${num(r.nutrients.p)} kg</span><span>K₂O ${num(r.nutrients.k)} kg</span></div>
      <h4>Fertilizer required</h4><div class="fert-cards">
        <div class="fert"><span>Urea (46% N)</span><strong>${num(r.fert.urea)} kg</strong><small>≈ ${r.bags.urea} bags of 45 kg</small></div>
        <div class="fert"><span>DAP (18-46-0)</span><strong>${num(r.fert.dap)} kg</strong><small>≈ ${r.bags.dap} bags of 50 kg</small></div>
        <div class="fert"><span>MOP (60% K₂O)</span><strong>${num(r.fert.mop)} kg</strong><small>≈ ${r.bags.mop} bags of 50 kg</small></div></div>
      <h4>When to apply</h4><div class="table-wrap"><table class="table"><thead><tr><th>Stage</th><th>Urea</th><th>DAP</th><th>MOP</th></tr></thead><tbody>
        ${r.schedule.map(s => `<tr><td>${escapeHTML(s.stage)}</td><td>${num(s.urea)} kg</td><td>${s.dap ? num(s.dap) + ' kg' : '–'}</td><td>${s.mop ? num(s.mop) + ' kg' : '–'}</td></tr>`).join('')}</tbody></table></div>
      <p class="muted small">${escapeHTML(r.note)}</p>
      <h4>Buy from AgroConnect</h4><div class="cd-prods">${prod(r.products.urea)}${prod(r.products.dap)}${prod(r.products.mop)}</div>
      <p class="cd-note" style="margin-top:14px"><i class="fa-solid fa-triangle-exclamation"></i> ${escapeHTML(r.disclaimer)}</p></div>`;
  }
  form.addEventListener('submit', e => { e.preventDefault(); calc(); });
  if (qs.get('crop')) calc();
})();
