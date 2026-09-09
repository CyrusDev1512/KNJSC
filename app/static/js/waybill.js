/* Chi tiết là một giao dịch; tổng tiền luôn do máy chủ tính bằng Decimal. */
(function () {
  'use strict';
  var grid = document.getElementById('luoi-vd');
  var groupHeader = grid && grid.querySelector('.vd-group-header');
  if (groupHeader) {
    var labels = {};
    groupHeader.querySelectorAll('[data-columns]').forEach(function (th) {
      th.dataset.columns.split(',').forEach(function (code) { labels[code] = th.textContent; });
    });
    var firstGroupLabel = groupHeader.querySelector('[data-columns] span').textContent;
    function addFrozenGroupLabel(corner) {
      corner.className = 'vd-group-corner';
      var frozenLabel = document.createElement('span');
      frozenLabel.className = 'vd-frozen-group-label';
      frozenLabel.textContent = firstGroupLabel;
      corner.appendChild(frozenLabel);
    }
    addFrozenGroupLabel(groupHeader.firstElementChild);
    var groupFrame = null;
    function keepGroupLabelsVisible() {
      groupFrame = null;
      var gridBox = grid.getBoundingClientRect();
      var frozenRight = gridBox.left;
      grid.querySelectorAll('.bt-hang-ten th.co-dinh').forEach(function (th) {
        frozenRight = Math.max(frozenRight, th.getBoundingClientRect().right);
      });
      var frozenLabel = groupHeader.querySelector('.vd-frozen-group-label');
      frozenLabel.style.width = Math.max(46, frozenRight - gridBox.left) + 'px';
      groupHeader.querySelectorAll('th span:not(.vd-frozen-group-label)').forEach(function (label) {
        var th = label.parentElement;
        label.style.transform = '';
        label.style.visibility = '';
        var thBox = th.getBoundingClientRect();
        var labelBox = label.getBoundingClientRect();
        var visibleLeft = Math.max(thBox.left, frozenRight);
        var visibleRight = Math.min(thBox.right, gridBox.right);
        if (visibleRight - visibleLeft < labelBox.width + 16) {
          label.style.visibility = 'hidden';
          return;
        }
        var wanted = visibleLeft + Math.max(8, (visibleRight - visibleLeft - labelBox.width) / 2);
        wanted = Math.max(thBox.left + 8, Math.min(wanted, thBox.right - labelBox.width - 8));
        label.style.transform = 'translateX(' + (wanted - labelBox.left) + 'px)';
      });
    }
    function scheduleGroupLabels() {
      if (!groupFrame) groupFrame = requestAnimationFrame(keepGroupLabelsVisible);
    }
    grid.addEventListener('gridColumnsChanged', function () {
      var corner = document.createElement('th');
      addFrozenGroupLabel(corner);
      groupHeader.replaceChildren(corner);
      var last = null;
      grid.querySelectorAll('.bt-hang-chu th').forEach(function (th) {
        if (th.hidden || (!th.dataset.cot && !th.dataset.trong)) return;
        var label = labels[th.dataset.cot] || '';
        if (last && last.dataset.label === label) last.colSpan += 1;
        else {
          last = document.createElement('th'); last.dataset.label = label;
          var span = document.createElement('span'); span.textContent = label; last.appendChild(span);
          last.scope = 'colgroup'; groupHeader.appendChild(last);
        }
      });
      scheduleGroupLabels();
    });
    grid.addEventListener('scroll', scheduleGroupLabels, {passive: true});
    window.addEventListener('resize', scheduleGroupLabels);
    scheduleGroupLabels();
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
      var body = add.closest('form').querySelector('.vd-items tbody');
      var row = body.rows[0].cloneNode(true);
      row.querySelector('select').value = '';
      row.querySelectorAll('input').forEach(function (input) { input.value = input.name === 'quantity' ? '1' : '0.00'; });
      body.appendChild(row); row.querySelector('select').focus();
    }
    var remove = event.target.closest('[data-remove-item]');
    if (remove && remove.closest('tbody').rows.length > 1) remove.closest('tr').remove();
  }, true);
  document.addEventListener('keydown', function (event) {
    var cell = event.target.closest('[data-waybill-detail]');
    if (cell && event.key === 'Enter') { event.preventDefault(); event.stopImmediatePropagation(); showDetail(cell); }
  }, true);
  document.body.addEventListener('htmx:beforeSwap', function (event) {
    if (event.detail.xhr.status === 400 && /^vd-/.test(event.detail.target.id)) {
      event.detail.shouldSwap = true; event.detail.isError = false;
    }
  });
  document.body.addEventListener('htmx:configRequest', function (event) {
    if (event.detail.elt.id === 'vd-statistics') {
      var group = document.getElementById('vd-group');
      if (group) event.detail.parameters.group = group.value;
    }
  });
  document.body.addEventListener('waybillChanged', function (event) {
    var dialog = document.getElementById('vd-detail');
    if (!grid || !dialog || event.detail.kind !== 'detail') return;
    dialog.close();
    htmx.ajax('GET', location.href, {target: '#luoi-vd tbody', select: '#luoi-vd tbody', swap: 'outerHTML'}).then(function () {
      // tbody cũ đã rời DOM sau outerHTML, không dựa vào contains ở afterSwap.
      htmx.trigger(document.body, 'waybillRefresh');
    });
  });
  document.body.addEventListener('htmx:afterSwap', function (event) {
    if (grid && grid.contains(event.detail.target)) htmx.trigger(document.body, 'waybillRefresh');
  });
  document.body.addEventListener('htmx:afterRequest', function (event) {
    if (event.detail.successful && event.detail.requestConfig.verb === 'post' && document.getElementById('vd-statistics')) {
      htmx.trigger(document.body, 'waybillRefresh');
    }
  });
})();
