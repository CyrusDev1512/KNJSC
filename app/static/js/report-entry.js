(() => {
  const map = document.getElementById('report-currency-map');
  const output = document.querySelector('[data-report-currency]');
  const market = document.querySelector('[data-report-market] select');
  if (!map || !output || !market) return;
  const currencies = JSON.parse(map.textContent);
  const sync = () => { output.value = currencies[market.value] || 'Chọn quốc gia'; };
  market.addEventListener('change', sync); sync();
})();
