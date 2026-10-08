/* AgroConnect AI assistant widget (additive). Talks to POST /api/assistant. */
(() => {
  const $ = id => document.getElementById(id);
  document.addEventListener('DOMContentLoaded', () => {
    const w = $('aiWidget'); if (!w) return;
    const fab = $('aiFab'), panel = $('aiPanel'), log = $('aiLog'), form = $('aiForm'), input = $('aiInput'), chips = $('aiChips'), mic = $('aiMic'), modeEl = $('aiMode');
    const KEY = 'agro_ai_chat';
    let history = []; try { history = JSON.parse(sessionStorage.getItem(KEY) || '[]'); } catch (e) {}
    const lang = () => (window.I18N && I18N.lang) || 'en';
    const save = () => { try { sessionStorage.setItem(KEY, JSON.stringify(history.slice(-20))); } catch (e) {} };
    const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const fmt = s => esc(s).replace(/(\/order\/\d+)/g, '<a href="$1">Open order &amp; map</a>').replace(/\n/g, '<br>');
    const inr = n => '₹' + Number(n).toLocaleString('en-IN');
    const scroll = () => { log.scrollTop = log.scrollHeight; };

    const add = (role, text) => { const d = document.createElement('div'); d.className = 'ai-msg ' + role; if (role === 'user') d.setAttribute('data-no-i18n', ''); d.innerHTML = role === 'bot' ? fmt(text) : esc(text); log.appendChild(d); scroll(); return d; };
    const addProducts = list => {
      if (!list || !list.length) return;
      const box = document.createElement('div'); box.className = 'ai-products';
      box.innerHTML = list.map(p => `<a class="ai-prod" href="${esc(p.url)}"><img src="${esc(p.image)}" alt="${esc(p.name)}" loading="lazy">
        <div><b>${esc(p.name)}</b><span><em>${inr(p.price)}</em>${p.old ? `<s>${inr(p.old)}</s>` : ''}${esc(p.seller)}</span></div>
        <button type="button" data-add="${p.id}" data-name="${esc(p.name)}">Add to Cart</button></a>`).join('');
      // the global [data-add] handler in cart.js adds the item and shows the toast
      log.appendChild(box); scroll();
    };
    const greet = () => add('bot', "Hi! I'm your AgroConnect assistant. Ask me about products, farming tips, delivery or your orders.");
    const render = () => { log.innerHTML = ''; greet(); history.forEach(h => add(h.role === 'user' ? 'user' : 'bot', h.content)); };

    const suggestions = ['Tomato seeds', 'Best fertilizer for rice', 'Drip irrigation', 'Track my order', 'Check delivery to 508001'];
    chips.innerHTML = suggestions.map(s => `<button type="button">${s}</button>`).join('');
    chips.addEventListener('click', e => { const b = e.target.closest('button'); if (b) ask(b.textContent); });

    const open = on => {
      panel.hidden = !on; w.classList.toggle('open', on); fab.setAttribute('aria-expanded', on);
      if (on) { if (!log.children.length) render(); setTimeout(() => input.focus(), 250); }
    };
    fab.onclick = () => open(true); $('aiClose').onclick = () => open(false);
    $('aiClear').onclick = () => { history = []; save(); render(); };
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && !panel.hidden) open(false); });

    fetch('/api/assistant/status').then(r => r.json()).then(s => {
      modeEl.innerHTML = '<span class="ai-dot"></span> ' + (s.mode === 'ai' ? 'AI powered' : 'Smart assistant');
    }).catch(() => {});

    let busy = false;
    async function ask(text) {
      text = (text || '').trim(); if (!text || busy) return;
      busy = true; add('user', text); input.value = ''; chips.style.display = 'none';
      const typing = document.createElement('div'); typing.className = 'ai-msg bot ai-typing'; typing.innerHTML = '<i></i><i></i><i></i>'; log.appendChild(typing); scroll();
      try {
        const res = await fetch('/api/assistant', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': window.AGRO.csrf },
          body: JSON.stringify({ message: text, lang: lang(), history: history.slice(-8) }) });
        const d = await res.json(); typing.remove();
        if (!d.ok) add('bot', d.error || 'Something went wrong. Please try again.');
        else { history.push({ role: 'user', content: text }, { role: 'assistant', content: d.reply }); save(); add('bot', d.reply); addProducts(d.products); }
      } catch (e) { typing.remove(); add('bot', 'I could not reach the server. Please check your connection and try again.'); }
      busy = false;
    }
    form.addEventListener('submit', e => { e.preventDefault(); ask(input.value); });

    // Voice input where the browser supports it (Chrome/Edge/Safari)
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SR) {
      mic.hidden = false;
      const codes = { en: 'en-IN', te: 'te-IN', hi: 'hi-IN', ta: 'ta-IN', kn: 'kn-IN', mr: 'mr-IN' };
      mic.onclick = () => {
        const r = new SR(); r.lang = codes[lang()] || 'en-IN'; r.interimResults = false;
        mic.classList.add('rec'); r.onend = () => mic.classList.remove('rec'); r.onerror = () => mic.classList.remove('rec');
        r.onresult = ev => { input.value = ev.results[0][0].transcript; ask(input.value); };
        try { r.start(); } catch (e) { mic.classList.remove('rec'); }
      };
    }
  });
})();
