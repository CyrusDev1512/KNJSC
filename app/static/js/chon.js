/* Ô chọn có mục "＋ Thêm mới…" — FR-8.7, Q58.

   Chọn mục đó thì mở hộp gõ giá trị mới ngay cạnh ô; máy chủ thêm giá trị
   (vào danh sách của cột, hoặc vào danh mục sản phẩm) rồi trả về đúng các
   <option> mới. Tệp này chép danh sách đó vào mọi ô chọn cùng nhóm
   (data-nhom), chọn giá trị vừa thêm ở ô đã hỏi, và bắn "change" để nơi
   dùng ô tự lo tiếp: màn hình Lên đơn thì tính lại tiền, biểu mẫu thì giữ giá
   trị vừa chọn. Bảng dữ liệu không có ô chọn vì chỉ để xem (ADR-014).

   Bắt sự kiện ở mức document nên ô do HTMX thay vào sau vẫn chạy. */
(function () {
  var THEM = "__them__";   // cùng chuỗi với forms_builder.choice_registry.ADD_SENTINEL

  function hopCua(select) {
    var chon = select.dataset.themHop;
    if (chon) return document.querySelector(chon);
    var cha = select.closest(".o-chon");
    return cha ? cha.querySelector(".o-chon-them") : null;
  }

  // Nhớ giá trị trước khi đổi, để chọn "Thêm mới…" xong còn trả lại
  document.addEventListener("focusin", function (e) {
    if (e.target.matches("select[data-nhom]")) e.target.dataset.truoc = e.target.value;
  });

  // Pha capture: chặn trước khi bảng dữ liệu hay Lên đơn nghe thấy "change"
  document.addEventListener("change", function (e) {
    var o = e.target;
    if (!o.matches || !o.matches("select[data-nhom]") || o.value !== THEM) return;
    e.stopPropagation();
    o.value = o.dataset.truoc || "";
    var hop = hopCua(o);
    if (!hop) return;
    hop.hidden = false;
    hop._cho = o;
    var nhap = hop.querySelector("input");
    if (nhap) { nhap.value = ""; nhap.focus(); }
  }, true);

  document.addEventListener("keydown", function (e) {
    var hop = e.target.closest && e.target.closest(".o-chon-them");
    if (!hop || !e.target.matches("input")) return;
    if (e.key === "Enter") {
      e.preventDefault();                       // không gửi cả biểu mẫu bao ngoài
      var nut = hop.querySelector("button");
      if (nut) nut.click();
    } else if (e.key === "Escape") {
      hop.hidden = true;
      if (hop._cho) hop._cho.focus();
    }
  });

  document.addEventListener("htmx:afterRequest", function (e) {
    var hop = e.detail.elt.closest && e.detail.elt.closest(".o-chon-them");
    if (!hop) return;
    var loi = hop.querySelector(".o-chon-loi");
    if (!e.detail.successful) {
      if (loi) loi.textContent = e.detail.xhr.responseText || "Không thêm được.";
      return;
    }
    if (loi) loi.textContent = "";

    var mau = document.createElement("select");
    mau.innerHTML = e.detail.xhr.responseText;
    var moi = mau.querySelector("option[selected]");
    var giaTri = moi ? moi.value : "";
    mau.querySelectorAll("option[selected]").forEach(function (op) { op.removeAttribute("selected"); });

    document.querySelectorAll('select[data-nhom="' + hop.dataset.nhom + '"]').forEach(function (s) {
      var hien = s.value;
      s.innerHTML = mau.innerHTML;
      s.value = hien;
    });
    hop.hidden = true;
    var cho = hop._cho;
    if (cho) {
      cho.value = giaTri;
      cho.dataset.truoc = giaTri;
      cho.dispatchEvent(new Event("change", { bubbles: true }));
      cho.focus();
    }
  });

})();
