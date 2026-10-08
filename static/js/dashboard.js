/* AgroConnect – profile, seller and admin dashboards */
document.addEventListener('DOMContentLoaded', () => {
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];

  // Sidebar panel switching
  const showPanel = id => {
    $$('.panel').forEach(p => p.classList.toggle('active', p.id === id));
    $$('.side-link[data-panel]').forEach(b => b.classList.toggle('active', b.dataset.panel === id));
    history.replaceState(null, '', '#' + id); window.dispatchEvent(new Event('resize'));
  };
  $$('.side-link[data-panel]').forEach(b => b.addEventListener('click', () => showPanel(b.dataset.panel)));
  $$('[data-panel-go]').forEach(b => b.addEventListener('click', () => showPanel(b.dataset.panelGo)));
  if (location.hash && document.getElementById(location.hash.slice(1))?.classList.contains('panel')) showPanel(location.hash.slice(1));

  const done = (res, reload = true) => { if (res.ok) { toast(res.message || 'Saved.'); if (reload) setTimeout(() => location.reload(), 700); } else toast(res.error || 'Something went wrong.', 'error'); return res.ok; };

  // ----- Profile page
  const pf = $('#profileForm');
  if (pf) pf.addEventListener('submit', async e => { e.preventDefault(); done(await api('/update-profile', { method: 'PUT', body: { name: $('#pf_name').value, phone: $('#pf_phone').value } })); });
  const photo = $('#photoInput');
  if (photo) photo.addEventListener('change', async () => {
    const fd = new FormData(); fd.append('photo', photo.files[0]);
    if (done(await api('/profile/photo', { method: 'POST', form: fd }), false)) { $('#avatarPreview').src = URL.createObjectURL(photo.files[0]); $('#sidePhoto').src = $('#avatarPreview').src; }
  });
  const pw = $('#pwForm');
  if (pw) pw.addEventListener('submit', async e => { e.preventDefault(); if (done(await api('/change-password', { method: 'POST', body: { current: $('#pw_cur').value, new: $('#pw_new').value } }), false)) pw.reset(); });
  const af = $('#addressForm');
  if (af) af.addEventListener('submit', async e => { e.preventDefault(); done(await api('/profile/address', { method: 'POST', body: { line1: $('#ad_line1').value, village: $('#ad_village').value, district: $('#ad_district').value, state: $('#ad_state').value, pincode: $('#ad_pin').value } })); });
  $$('[data-del-address]').forEach(b => b.addEventListener('click', async () => { if (confirm('Remove this address?')) done(await api('/profile/address/' + b.dataset.delAddress, { method: 'DELETE' })); }));

  // ----- Product management (seller + admin)
  const modal = $('#editModal'), editForm = $('#editProductForm');
  const closeModal = () => { modal.hidden = true; document.body.classList.remove('no-scroll'); };
  if (modal) {
    modal.addEventListener('click', e => { if (e.target === modal || e.target.matches('[data-close]')) closeModal(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
  }
  const openModal = (data, isNew = false) => {
    editForm.reset(); $('#editTitle') && ($('#editTitle').textContent = isNew ? 'Add Product' : 'Edit Product');
    Object.entries(data || {}).forEach(([k, v]) => { if (editForm.elements[k]) editForm.elements[k].value = v ?? ''; });
    editForm.dataset.mode = isNew ? 'new' : 'edit';
    $('#sellerPick') && ($('#sellerPick').hidden = !isNew); $('#imgPick') && ($('#imgPick').hidden = !isNew);
    modal.hidden = false; document.body.classList.add('no-scroll'); editForm.elements.name.focus();
  };
  $$('[data-edit]').forEach(b => b.addEventListener('click', () => openModal(JSON.parse(b.closest('tr').dataset.product))));
  $('#openAdminAdd')?.addEventListener('click', () => openModal({}, true));
  if (editForm) editForm.addEventListener('submit', async e => {
    e.preventDefault(); const f = editForm.elements;
    if (!f.name.value.trim() || !f.description.value.trim() || !f.price.value) return toast('Please fill all required fields.', 'error');
    if (editForm.dataset.mode === 'new') done(await api('/add-product', { method: 'POST', form: new FormData(editForm) }));
    else {
      const body = Object.fromEntries(new FormData(editForm).entries()); delete body.image;
      done(await api('/update-product/' + f.id.value, { method: 'PUT', body }));
    }
  });
  $$('[data-delete]').forEach(b => b.addEventListener('click', async () => { if (confirm('Delete this product permanently?')) done(await api('/delete-product/' + b.dataset.delete, { method: 'DELETE' })); }));
  $$('[data-set-status]').forEach(b => b.addEventListener('click', async () => done(await api(`/admin/product/${b.dataset.id}/status`, { method: 'POST', body: { status: b.dataset.setStatus } }))));
  $$('[data-del-user]').forEach(b => b.addEventListener('click', async () => { if (confirm('Delete this user?')) done(await api('/admin/user/' + b.dataset.delUser, { method: 'DELETE' })); }));
  $$('.status-select').forEach(s => s.addEventListener('change', async () => done(await api(`/order/${s.dataset.order}/status`, { method: 'POST', body: { status: s.value } }), false)));

  const addForm = $('#addProductForm');
  if (addForm) addForm.addEventListener('submit', async e => {
    e.preventDefault(); const f = addForm.elements;
    if (!f.name.value.trim() || !f.price.value || !f.stock.value || !f.description.value.trim()) return toast('Please fill all required fields.', 'error');
    if (f.image.files[0] && f.image.files[0].size > 4 * 1024 * 1024) return toast('Image must be smaller than 4 MB.', 'error');
    if (done(await api('/add-product', { method: 'POST', form: new FormData(addForm) }), false)) { addForm.reset(); setTimeout(() => location.reload(), 900); }
  });
  $('#catForm')?.addEventListener('submit', async e => { e.preventDefault(); done(await api('/admin/category', { method: 'POST', body: { name: $('#catName').value, audience: $('#catAudience').value } })); });

  // ----- Charts (Chart.js)
  if (window.Chart && window.CHART) {
    const C = window.CHART, green = '#39D353', light = '#168A3A';
    Chart.defaults.color = '#A7B3AA'; Chart.defaults.borderColor = '#26352B';
    Chart.defaults.font.family = 'Inter, sans-serif';
    const make = (id, type, labels, data, label, color = green) => { const el = document.getElementById(id); if (!el) return;
      new Chart(el, { type, data: { labels, datasets: [{ label, data, backgroundColor: type === 'line' ? 'rgba(57,211,83,.14)' : color, borderColor: color, fill: type === 'line', tension: .35, borderRadius: 6 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: '#1b2a20' } }, x: { grid: { display: false } } } } }); };
    make('revChart', 'line', C.months, C.revenue, 'Revenue (₹)'); make('revChart2', 'line', C.months, C.revenue, 'Revenue (₹)');
    make('ordersChart', 'bar', C.months, C.orders, 'Orders', light);
    if (C.top_names) make('topChart', 'bar', C.top_names, C.top_qty, 'Units sold');
    if (C.cat_names) make('catChart', 'bar', C.cat_names, C.cat_rev, 'Revenue (₹)');
  }

  // ----- Order tracking timeline
  $$('[data-timeline]').forEach(el => {
    const steps = ['Order Placed', 'Order Confirmed', 'Packed', 'Shipped', 'Out for Delivery', 'Delivered'];
    const map = { 'Order Placed': 0, Confirmed: 1, Packed: 2, Shipped: 3, 'Out for Delivery': 4, Delivered: 5 };
    const current = map[el.dataset.status] ?? 0;
    el.innerHTML = steps.map((s, i) => {
      const state = i < current || current === 5 ? 'done' : i === current ? 'current' : 'todo';
      const icon = state === 'done' ? 'fa-solid fa-circle-check' : state === 'current' ? 'fa-solid fa-circle-dot' : 'fa-regular fa-circle';
      return `<li class="${state}"><i class="${icon}"></i><span>${s}</span></li>`; }).join('');
  });
});


/* Add-product: image preview + gentle mismatch warning */
document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('ap_img'); if (!input) return;
  const prev = document.getElementById('ap_preview'), warn = document.getElementById('ap_warn');
  const nameEl = document.querySelector('#s-add [name="name"]');
  input.addEventListener('change', () => {
    const f = input.files[0];
    if (!f) { prev.classList.remove('show'); warn.classList.remove('show'); return; }
    prev.src = URL.createObjectURL(f); prev.classList.add('show');
    // Heuristic only: warn when the file name shares no word with the product name.
    const words = ((nameEl && nameEl.value) || '').toLowerCase().split(/[^a-z]+/).filter(w => w.length > 3);
    const file = f.name.toLowerCase();
    warn.classList.toggle('show', words.length > 0 && !words.some(w => file.includes(w.replace(/s$/, ''))));
  });
});
