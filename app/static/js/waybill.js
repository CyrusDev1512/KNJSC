/* Chi tiết là một giao dịch; tổng tiền luôn do máy chủ tính bằng Decimal. */
(function () {
  'use strict';
  function emptyNote(form) {
    var note = form && form.querySelector('[data-items-empty]');
    if (note) note.hidden = form.querySelector('.vd-items tbody').rows.length > 0;
  }
  function showDetail(cell) {
    var dialog = document.getElementById('vd-detail');
    document.getElementById('vd-detail-body').textContent = 'Đang tải chi tiết…';
    if (!dialog.open) dialog.showModal();
    htmx.ajax('GET', cell.dataset.waybillDetail, {target: '#vd-detail-body', swap: 'innerHTML'}).catch(function () {
      document.getElementById('vd-detail-body').textContent = 'Không tải được chi tiết. Đóng hộp rồi thử lại.';
    });
  }
  document.addEventListener('click', function (event) {
    var cell = event.target.closest('[data-waybill-detail]');
    if (cell) { event.preventDefault(); event.stopImmediatePropagation(); showDetail(cell); return; }
    if (event.target.closest('[data-close-detail]')) document.getElementById('vd-detail').close();
    var add = event.target.closest('[data-add-item]');
    if (add) {
      var form = add.closest('form'), body = form.querySelector('.vd-items tbody');
      // Còn dòng thì chép dòng đầu (giữ sản phẩm vừa tạo ở Lên đơn); hết dòng thì lấy dòng mẫu.
      var row = (body.rows[0] || form.querySelector('template[data-item-template]').content.firstElementChild).cloneNode(true);
      row.querySelectorAll('select').forEach(function (select) { select.value = ''; });
      row.querySelectorAll('input').forEach(function (input) { input.value = input.name === 'quantity' ? '1' : '0.00'; });
      body.appendChild(row); row.querySelector('select').focus();
      emptyNote(form);
    }
    var remove = event.target.closest('[data-remove-item]');
    // Hộp Chi tiết (bảng có `data-allow-empty`): Bỏ dòng xoá được cả dòng cuối, còn nút Thêm dòng để
    // thêm lại; Lưu khi không còn dòng là đơn không sản phẩm (chủ dự án 02.10.2026). Lên đơn vẫn giữ ≥1 dòng.
    if (remove) {
      var tr = remove.closest('tr'), table = tr.closest('table');
      if (tr.parentNode.rows.length > 1 || table.hasAttribute('data-allow-empty')) {
        var owner = tr.closest('form'); tr.remove(); emptyNote(owner);
      }
    }
  }, true);
  document.addEventListener('change', function (event) {
    if (!event.target.matches('select[name="product"]')) return;
    var row = event.target.closest('tr'), unit = row.querySelector('[name="unit"]');
    var option = event.target.selectedOptions[0];
    if (unit) unit.value = option ? option.dataset.unit || 'cái' : '';
  });
  document.addEventListener('keydown', function (event) {
    var cell = event.target.closest('[data-waybill-detail]');
    if (cell && event.key === 'Enter') { event.preventDefault(); event.stopImmediatePropagation(); showDetail(cell); }
  }, true);
  document.body.addEventListener('htmx:beforeSwap', function (event) {
    if (event.detail.xhr.status === 400 && /^vd-/.test(event.detail.target.id)) {
      event.detail.shouldSwap = true; event.detail.isError = false;
    }
  });
  document.body.addEventListener('waybillChanged', function (event) {
    var dialog = document.getElementById('vd-detail');
    if (!dialog || event.detail.kind !== 'detail') return;
    dialog.close();
    window.dispatchEvent(new CustomEvent('master-refresh'));
  });
})();
