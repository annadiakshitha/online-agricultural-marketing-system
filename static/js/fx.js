/* AgroConnect 2.0 – motion layer (progressive enhancement; the site works without it). */
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine = matchMedia('(hover: hover) and (pointer: fine)').matches;
  const $ = (s, r = document) => r.querySelector(s);

  document.addEventListener('DOMContentLoaded', () => {
    // Scroll progress bar, back-to-top, navbar hide/show
    const bar = document.createElement('div'); bar.id = 'scrollBar'; document.body.prepend(bar);
    const top = document.createElement('button'); top.id = 'toTop'; top.setAttribute('aria-label', 'Back to top'); top.innerHTML = '<i class="fa-solid fa-arrow-up"></i>';
    top.onclick = () => scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' }); document.body.appendChild(top);
    const nav = $('#navbar'); let lastY = 0, ticking = false;
    const onScroll = () => {
      const y = scrollY, h = document.documentElement.scrollHeight - innerHeight;
      bar.style.width = (h > 0 ? (y / h) * 100 : 0) + '%';
      top.classList.toggle('show', y > 700);
      if (nav && !document.querySelector('.nav-links.open, .search-bar.open')) nav.classList.toggle('nav-hidden', y > lastY && y > 320);
      const img = $('.hero-image'); if (img && y < 900 && !reduce) img.style.translate = `0 ${y * 0.12}px`;
      lastY = y; ticking = false;
    };
    addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });

    // Stagger siblings of .reveal so grids cascade in
    document.querySelectorAll('.category-grid, .feature-grid, .testimonial-grid, .steps, .blog-grid').forEach(g =>
      [...g.children].forEach((c, i) => { c.style.transitionDelay = (i % 4) * 90 + 'ms'; }));
    document.querySelectorAll('.section-head').forEach(h => h.classList.add('reveal-head'));
    if ('IntersectionObserver' in window) {
      const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); } }), { threshold: .15 });
      document.querySelectorAll('.reveal-head').forEach(el => io.observe(el));
    } else document.querySelectorAll('.reveal-head').forEach(el => el.classList.add('visible'));

    // Cart badge bump when the number changes
    document.querySelectorAll('[data-cart-count],[data-wish-count]').forEach(el => {
      let prev = el.textContent;
      new MutationObserver(() => { if (el.textContent !== prev) { prev = el.textContent; el.classList.remove('bump'); void el.offsetWidth; el.classList.add('bump'); } })
        .observe(el, { childList: true, characterData: true, subtree: true });
    });

    if (reduce) return;

    // Ripple on buttons
    document.addEventListener('click', e => {
      const b = e.target.closest('.btn'); if (!b) return;
      const r = b.getBoundingClientRect(), s = Math.max(r.width, r.height) / 4, el = document.createElement('span');
      el.className = 'ripple'; el.style.cssText = `width:${s}px;height:${s}px;left:${e.clientX - r.left - s / 2}px;top:${e.clientY - r.top - s / 2}px`;
      b.appendChild(el); setTimeout(() => el.remove(), 650);
    });

    if (fine) {
      // 3D tilt + cursor spotlight on cards (event delegation, so JS-rendered cards work too)
      const sel = '.product-card, .category-card, .feature-card, .blog-card';
      document.addEventListener('mousemove', e => {
        const c = e.target.closest && e.target.closest(sel); if (!c) return;
        const r = c.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
        c.style.setProperty('--mx', x + 'px'); c.style.setProperty('--my', y + 'px');
        if (!c.matches('.blog-card')) { c.classList.add('tilting'); c.style.transform = `perspective(900px) rotateX(${((y / r.height) - .5) * -7}deg) rotateY(${((x / r.width) - .5) * 9}deg) translateY(-4px)`; }
      });
      document.addEventListener('mouseout', e => {
        const c = e.target.closest && e.target.closest(sel);
        if (c && !c.contains(e.relatedTarget)) { c.classList.remove('tilting'); c.style.transform = ''; }
      });
      // soft glow that follows the cursor
      const g = document.createElement('div'); g.className = 'cursor-glow'; document.body.appendChild(g);
      addEventListener('mousemove', e => { g.style.left = e.clientX + 'px'; g.style.top = e.clientY + 'px'; }, { passive: true });
    }

    // Hero particles: drifting leaves / pollen on a light canvas
    const cv = $('#heroFx'); if (cv) {
      const ctx = cv.getContext && cv.getContext('2d'); if (!ctx) return; let w, h, parts = [], raf;
      const size = () => { w = cv.width = cv.offsetWidth; h = cv.height = cv.offsetHeight; parts = Array.from({ length: Math.min(46, Math.round(w / 32)) }, spawn); };
      const spawn = () => ({ x: Math.random() * w, y: Math.random() * h, r: Math.random() * 2.4 + .6, vx: Math.random() * .35 + .08, vy: -(Math.random() * .35 + .05), a: Math.random() * .5 + .15, leaf: Math.random() < .18, rot: Math.random() * 6, vr: (Math.random() - .5) * .02 });
      const draw = () => {
        ctx.clearRect(0, 0, w, h);
        for (const p of parts) {
          p.x += p.vx; p.y += p.vy; p.rot += p.vr; if (p.x > w + 20 || p.y < -20) { p.x = -10; p.y = Math.random() * h; }
          ctx.globalAlpha = p.a; ctx.fillStyle = '#7CFF9B';
          if (p.leaf) { ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.rot); ctx.beginPath(); ctx.ellipse(0, 0, 9, 4, 0, 0, 6.3); ctx.fill(); ctx.restore(); }
          else { ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 6.3); ctx.fill(); }
        }
        raf = requestAnimationFrame(draw);
      };
      size(); draw(); addEventListener('resize', size);
      document.addEventListener('visibilitychange', () => { if (document.hidden) cancelAnimationFrame(raf); else draw(); });
    }
  });
})();
