"""Định vị ô ghi chú bằng bản ghi, không phụ thuộc cột nhận diện còn được vẽ."""


def ghi_chu_nhin_thay(trang, record_id, noi_dung):
    """Cuộn tới ô của dòng đang ở vùng nhìn; trả số đo và điểm không bị ghim che.

    Lưới vẽ dư cột ngoài khung. Chỉ thấy selector chưa đủ để bấm; cần phần giao
    với vùng cuộn, bên dưới tiêu đề và bên phải cột ghim. Không cuộn cả trang
    hoặc yêu cầu Playwright căn giữa một ô cao hơn màn hình.
    """
    ket_qua = trang.evaluate(
        """async ({id, text}) => {
            const vp = document.getElementById('mg-viewport');
            const frame = () => new Promise(r => requestAnimationFrame(
                () => requestAnimationFrame(r)));
            const rect = el => el ? el.getBoundingClientRect().toJSON() : null;
            const selector = `.mg-cell[data-code='ghi_chu'][data-id='${id}']`;
            const deadline = performance.now() + 5000;
            let diagnostic = {};
            vp.scrollLeft = 0;
            while (performance.now() < deadline) {
                await frame();
                const cell = document.querySelector(selector);
                const v = rect(vp), c = rect(cell);
                const head = rect(document.querySelector('.mg-head'));
                const pin = rect(document.querySelector('.mg-head > .mg-pin-region'));
                const area = {
                    left: Math.max(0, v.left + vp.clientLeft, pin?.right || 0),
                    right: Math.min(innerWidth, v.left + vp.clientLeft + vp.clientWidth),
                    top: Math.max(0, v.top + vp.clientTop, head?.bottom || 0),
                    bottom: Math.min(innerHeight, v.top + vp.clientTop + vp.clientHeight),
                };
                diagnostic = {id, cell: c, viewport: v, header: head, pinned: pin,
                              area, scrollLeft: vp.scrollLeft, scrollTop: vp.scrollTop};
                if (c && cell.textContent === text) {
                    const left = Math.max(c.left, area.left) + 3;
                    const right = Math.min(c.right, area.right) - 3;
                    const top = Math.max(c.top, area.top) + 3;
                    const bottom = Math.min(c.bottom, area.bottom) - 3;
                    if (right > left && bottom > top) {
                        const x = (left + right) / 2, y = (top + bottom) / 2;
                        const hit = document.elementFromPoint(x, y);
                        diagnostic.point = {x, y};
                        diagnostic.obstruction = hit ? {
                            tag: hit.tagName, id: hit.id, class: hit.className,
                            record: hit.dataset.id, code: hit.dataset.code,
                        } : null;
                        if (hit === cell || cell.contains(hit)) {
                            return {ok: true, ...diagnostic, r: cell.dataset.r,
                                    cao_o: Math.round(c.height), cao_chu: cell.scrollHeight,
                                    rong_o: Math.round(c.width), chu: cell.textContent,
                                    xuong_dong: cell.classList.contains('mg-wrap')};
                        }
                    }
                }
                // Bước nhỏ hơn phần cuộn còn lại trên điện thoại, không nhảy qua ô.
                const step = Math.max(32, (area.right - area.left) / 2);
                vp.scrollLeft = Math.min(vp.scrollWidth - vp.clientWidth, vp.scrollLeft + step);
            }
            return {ok: false, ...diagnostic};
        }""",
        {"id": str(record_id), "text": noi_dung},
    )
    assert ket_qua["ok"], f"Không thấy phần ô ghi chú có thể bấm sau 5 giây: {ket_qua}"
    return ket_qua


def bam_ghi_chu(trang, o):
    """Kiểm lại đích rồi bấm chuột thật, không force-click hoặc phát sự kiện giả."""
    assert trang.evaluate(
        """({id, point}) => {
            const hit = document.elementFromPoint(point.x, point.y)?.closest('.mg-cell');
            return hit?.dataset.id === String(id) && hit.dataset.code === 'ghi_chu';
        }""", o,
    ), f"Điểm bấm không còn trúng ô ghi chú: {o}"
    trang.mouse.click(o["point"]["x"], o["point"]["y"])
