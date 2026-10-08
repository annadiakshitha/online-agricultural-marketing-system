/* AgroConnect – login / register UX */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.pw-toggle').forEach(btn => btn.addEventListener('click', () => {
    const input = btn.parentElement.querySelector('input'), show = input.type === 'password';
    input.type = show ? 'text' : 'password'; btn.querySelector('i').className = show ? 'fa-regular fa-eye-slash' : 'fa-regular fa-eye';
  }));
  document.querySelectorAll('.demo-fill').forEach(b => b.addEventListener('click', () => {
    document.getElementById('email').value = b.dataset.email; document.getElementById('password').value = b.dataset.pass;
  }));
  const seller = document.getElementById('sellerFields');
  if (seller) {
    const sync = () => { const r = document.querySelector('[name=role]:checked').value; seller.hidden = r === 'customer'; const b = document.getElementById('business'); if (b) b.closest('.field').hidden = r !== 'seller'; };
    document.querySelectorAll('[name=role]').forEach(r => r.addEventListener('change', sync)); sync();
  }
  const reg = document.getElementById('registerForm');
  if (reg) reg.addEventListener('submit', e => {
    const f = reg.elements; let msg = '';
    if (!f.name.value.trim() || !f.email.value.trim() || !f.phone.value.trim() || !f.password.value) msg = 'Please fill all required fields.';
    else if (f.password.value.length < 6) msg = 'Password must be at least 6 characters.';
    else if (f.password.value !== f.confirm_password.value) msg = 'Passwords do not match.';
    if (msg) { e.preventDefault(); toast(msg, 'error'); }
  });
  const login = document.getElementById('loginForm');
  if (login) login.addEventListener('submit', e => {
    if (!login.email.value.trim() || !login.password.value) { e.preventDefault(); toast('Please fill all required fields.', 'error'); }
  });
});
