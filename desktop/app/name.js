'use strict';
(async () => {
  const s = await window.desk.settings();
  const n = document.getElementById('n');
  n.value = s.name || '';
  n.focus();
  document.getElementById('f').addEventListener('submit', (e) => { e.preventDefault(); window.desk.setName(n.value); });
})();
