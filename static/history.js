/* history.js — Modal phục hồi thao tác và logic ràng buộc UI chặt chẽ */

const HISTORY_ICON = {
  THEM_LOP: '➕', XOA_LOP: '🗑', SUA_LOP: '✏️',
  THEM_SV:  '➕', XOA_SV:  '🗑', SUA_SV:  '✏️',
  THEM_MH:  '➕', XOA_MH:  '🗑', SUA_MH:  '✏️',
  THEM_LTC: '➕', XOA_LTC: '🚫', SUA_LTC: '✏️',
  THEM_GV:  '➕', XOA_GV:  '🗑', SUA_GV:  '✏️',
};

const CHILD_HINT = {
  XOA_LOP: 'Lưu ý: Nếu lớp đã có sinh viên thì xóa sẽ bị lỗi ràng buộc DB.',
  THEM_LOP: 'Hành động tạo Mới. Cần trọn vẹn xóa con trước khi hoàn tác.',
};

function _buildModal() {
  if (document.getElementById('historyModal')) return;
  document.body.insertAdjacentHTML('beforeend', `
  <div id="historyModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:9999;align-items:center;justify-content:center;">
    <div style="background:#1a1a1a;border:1px solid #3f3f46;border-radius:14px;width:min(640px,95vw);max-height:85vh;display:flex;flex-direction:column;overflow:hidden;">
      <div style="display:flex;justify-content:space-between;align-items:center;padding:1rem 1.25rem;border-bottom:1px solid #3f3f46;">
        <h2 style="font-size:1rem;font-weight:700;">↩ Lịch sử thao tác (Sơ đồ Nhánh Cây)</h2>
        <button onclick="closeHistory()" style="background:none;border:none;color:#a1a1aa;font-size:1.3rem;cursor:pointer;line-height:1;">✕</button>
      </div>
      <div id="historyList" style="overflow-y:auto;padding:.75rem 1rem;flex:1;"></div>
      <div id="historyFooter" style="padding:.75rem 1.25rem;border-top:1px solid #3f3f46;font-size:.78rem;color:#a1a1aa;">
        Hành động Con hiển thị thụt lề dưới hành động Cha. Không thể Hoàn Tác nhánh Cha nếu Nhánh con đang án ngữ.
      </div>
    </div>
  </div>`);
}

let historyDataRaw = [];

async function openHistory() {
  _buildModal();
  const modal = document.getElementById('historyModal');
  const list  = document.getElementById('historyList');
  modal.style.display = 'flex';
  list.innerHTML = '<p style="color:#a1a1aa;text-align:center;padding:1rem;">Đang tải...</p>';

  try {
    const res  = await fetch('/history');
    historyDataRaw = await res.json();
    if (!historyDataRaw || historyDataRaw.length === 0) {
      list.innerHTML = '<p style="color:#a1a1aa;text-align:center;padding:2rem;">Chưa có thao tác nào được ghi lại trong phiên này.</p>';
      return;
    }
    
    const nodes = historyDataRaw.map((item, id) => ({...item, id, isChild: false}));
    
    for(let i = 0; i < nodes.length; i++) {
        let child = nodes[i];
        for(let j = i + 1; j < nodes.length; j++) {
            let parent = nodes[j];
            if (parent.type.startsWith('THEM_') || parent.type.startsWith('SUA_')) {
                const keyMap = { 'THEM_LOP': 'malop', 'THEM_SV': 'masv', 'THEM_MH': 'mamh', 'THEM_GV': 'magv' };
                const key = keyMap[parent.type] || parent.type.split('_')[1].toLowerCase();
                if (child.data[key] && child.data[key] === parent.data[key]) {
                   child.isChild = true;
                   child.parentId = j;
                   break;
                }
            }
        }
    }
    
    list.innerHTML = nodes.map(node => {
      const icon = HISTORY_ICON[node.type] || '•';
      const hint = CHILD_HINT[node.type] || '';
      let prefix = '';
      let bgStyle = 'background:#1a1a1a; margin-bottom:.6rem;';
      if (node.isChild) {
          prefix = '<span style="color:#fbbf24;margin-right:8px;font-family:monospace;">├─</span>';
          bgStyle = 'background:#111; margin-left:1.5rem; margin-bottom:.6rem; border-left: 2px solid #52525b; border-bottom-left-radius: 0; border-top-left-radius: 0;';
      }

      return `
      <div style="display:flex;align-items:center;gap:.6rem;padding:.65rem .75rem;border-radius:6px;border:1px solid #2a2a2a;${bgStyle}">
        ${prefix}
        <span style="font-size:1rem;">${icon}</span>
        <div style="flex:1;min-width:0;">
          <div style="font-size:.83rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:600;">${node.label}</div>
          ${hint ? `<div style="font-size:.72rem;color:#c28;margin-top:.2rem;">${hint}</div>` : ''}
        </div>
        <button onclick="doSingleTreeUndo(${node.id})"
            style="background:transparent;color:#fca5a5;border:1px solid #fca5a5;border-radius:6px;padding:.3rem .7rem;font-size:.75rem;font-weight:600;cursor:pointer;white-space:nowrap;transition:0.1s;">
            Hoàn tác
        </button>
      </div>`;
    }).join('');
  } catch(e) {
    list.innerHTML = `<p style="color:#fca5a5;text-align:center;padding:1rem;">Lỗi tải lịch sử: ${e}</p>`;
  }
}

async function doSingleTreeUndo(idx) {
    const targetAction = historyDataRaw[idx];
    let blockers = [];
    for(let j = 0; j < idx; j++) {
        let check = historyDataRaw[j];
        const pType = targetAction.type;
        const key = pType.startsWith('THEM_') ? pType.split('_')[1].toLowerCase() : null;
        if (key && check.data[key] && check.data[key] === targetAction.data[key]) {
            blockers.push(j);
        }
    }
    if (blockers.length > 0) {
        alert("❌ Bị chặn: Không thể hoàn tác hành động Nguồn (Cha) vì đang có các hành động Nhánh (Con) bám vào nó. Vui lòng Undo các hành động Con trước!");
        return;
    }
    if (!confirm('Xác nhận hoàn tác thao tác này?')) return;
    try {
        const res  = await fetch('/history/undo', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({index: idx}) 
        });
        const data = await res.json();
        if (!data.ok) alert('Hoàn tác thất bại: ' + (data.msg || ''));
        else { closeHistory(); location.reload(); }
    } catch(e) { alert('Lỗi kết nối: ' + e); }
}

function closeHistory() {
  const modal = document.getElementById('historyModal');
  if (modal) modal.style.display = 'none';
}

document.addEventListener('click', function(e) {
  const modal = document.getElementById('historyModal');
  if (modal && e.target === modal) closeHistory();
});

// -----------------------------------------------------------
// Module: Ràng buộc UI (v4 — logic đơn giản, nhất quán)
// Nút Lưu: mờ mặc định → sáng khi user click vào bất kỳ ô input nào
// Nút Tạo mới: luôn là INSERT
// Nút Lưu dữ liệu: luôn là UPDATE (chỉ hoạt động khi có bản ghi đang chọn)
// -----------------------------------------------------------

let formHasError = false;

function setValidationMsg(inputId, msg, isError) {
    const errId = 'err_' + inputId;
    let err = document.getElementById(errId);
    if (!err) {
        err = document.createElement('div');
        err.id = errId;
        err.style.cssText = 'font-size:0.75rem;margin-top:0.35rem;font-weight:600;display:none;';
        const target = document.getElementById(inputId);
        if (target) target.parentNode.appendChild(err);
    }
    if (!msg) {
        err.style.display = 'none';
        return;
    }
    err.style.display = 'block';
    err.textContent = (isError ? '❌ ' : '✅ ') + msg;
    err.style.color = isError ? '#fca5a5' : '#10b981';
    
    const inputEl = document.getElementById(inputId);
    if (inputEl) {
        inputEl.style.borderColor = isError ? '#fca5a5' : 'var(--border)';
    }
}

/**
 * Bật/tắt nút Lưu dựa trên trạng thái lỗi.
 * Gọi hàm này khi có lỗi validation hoặc khi lỗi được giải quyết.
 * @param {'error'|'ok'} state
 */
function updateSaveButton(state) {
    if (state === 'error') {
        updateActionButtons('error');
    } else {
        formHasError = false;
        const isEditing = typeof sel !== 'undefined' && sel !== null && sel !== '';
        updateActionButtons(isEditing ? 'editing' : 'adding');
        
        // Thêm trường hợp nếu đang adding mà user đã bắt đầu gõ thì bật nút Ghi
        const btnGhi = document.getElementById('btnGhi');
        if (!isEditing && btnGhi && btnGhi.dataset.formActive === 'true') {
            btnGhi.disabled = false;
        }
    }
}
function updateActionButtons(state) {
    const btnThem = document.getElementById('btnThem');
    const btnGhi = document.getElementById('btnGhi');
    const btnXoa = document.getElementById('btnXoa');
    const btnHuy = document.getElementById('btnHuy');

    if (state === 'error') {
        formHasError = true;
        if (btnThem) btnThem.disabled = true;
        if (btnGhi) btnGhi.disabled = true;
        if (btnXoa) btnXoa.disabled = true;
        if (btnHuy) btnHuy.disabled = true;
        return;
    }

    formHasError = false;

    if (state === 'idle') {
        if (btnThem) btnThem.disabled = window.IS_FROZEN_CONTEXT ? true : false;
        if (btnGhi) { btnGhi.disabled = true; btnGhi.dataset.formActive = 'false'; }
        if (btnXoa) btnXoa.disabled = true;
        if (btnHuy) btnHuy.disabled = true;
    } else if (state === 'editing') {
        if (btnThem) btnThem.disabled = true;
        if (btnGhi) { btnGhi.disabled = false; btnGhi.dataset.formActive = 'true'; }
        if (btnXoa) btnXoa.disabled = false;
        if (btnHuy) btnHuy.disabled = false;
    } else if (state === 'adding') {
        if (btnThem) btnThem.disabled = window.IS_FROZEN_CONTEXT ? true : false;
        if (btnGhi) { btnGhi.disabled = true; btnGhi.dataset.formActive = 'false'; }
        if (btnXoa) btnXoa.disabled = true;
        if (btnHuy) btnHuy.disabled = true;
    }
}

/**
 * Tiện ích khóa thông tin (ReadOnly & Disabled) cho các field chỉ định
 */
function toggleFormLock(isLocked, inputIds) {
    inputIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.readOnly = isLocked;
            // Select/Radio/Checkbox cần thuộc tính disabled
            if (el.tagName === 'SELECT' || el.type === 'checkbox' || el.type === 'radio') {
                el.disabled = isLocked;
            }
            if (isLocked) {
                el.style.backgroundColor = 'rgba(39, 39, 42, 0.4)';
                el.style.color = '#52525b';
                el.style.borderColor = '#fca5a5';
                el.style.cursor = 'not-allowed';
            } else {
                el.style.backgroundColor = '';
                el.style.color = '';
                el.style.borderColor = 'var(--border)';
            }
        }
    });
}

/**
 * [PLANT_LTC_BUGS_2026] Áp dụng style làm mờ cho 1 trường readOnly
 * (khóa chính). Dùng khi chọn dòng để sửa - mã không được sửa nhưng
 * phải có giao diện mờ để user biết là không chỉnh được.
 */
function applyReadonlyStyle(el, isFrozen) {
    if (!el) return;
    el.readOnly = true;
    if (el.tagName === 'SELECT') {
        el.disabled = true;
    }
    el.style.backgroundColor = 'rgba(39, 39, 42, 0.4)';
    el.style.color = '#52525b';
    el.style.borderColor = isFrozen ? '#fca5a5' : '#52525b';
    el.style.cursor = 'not-allowed';
    el.title = isFrozen ? '🔒 Dữ liệu lịch sử đã bị đóng băng' : '🔒 Khóa chính - không thể chỉnh sửa';
}

/**
 * [PLANT_LTC_BUGS_2026] Xóa style làm mờ khi tạo mới
 */
function clearReadonlyStyle(el) {
    if (!el) return;
    el.readOnly = false;
    if (el.tagName === 'SELECT') {
        el.disabled = false;
    }
    el.style.backgroundColor = '';
    el.style.color = '';
    el.style.borderColor = 'var(--border)';
    el.style.cursor = '';
    el.title = '';
}

/**
 * Kích hoạt nút Lưu khi user click vào bất kỳ ô input nào trong form.
 * Gọi ở DOMContentLoaded cho từng trang.
 */
function enableSaveOnInputFocus() {
    // Tăng cường CSS cho các nút bị disabled để nhìn mờ rõ rệt hơn
    if (!document.getElementById('css-global-btn-freeze')) {
        const style = document.createElement('style');
        style.id = 'css-global-btn-freeze';
        style.textContent = `
            .btn:disabled { 
                filter: grayscale(1) !important; 
                opacity: 0.4 !important; 
                cursor: not-allowed !important;
                pointer-events: none !important;
            }
            .frozen-row { opacity: 0.7; }
        `;
        document.head.appendChild(style);
    }

    document.querySelectorAll('.form-grid input, .form-grid select, .form-grid textarea').forEach(el => {
        el.addEventListener('focus', () => {
            if (!formHasError) {
                // Sửa lỗi: Chỉ bật nút Ghi nếu form đang ở chế độ chỉnh sửa (có chọn dòng)
                const isSelected = typeof sel !== 'undefined' && sel !== null && sel !== '';
                const btnGhi = document.getElementById('btnGhi');
                if (btnGhi && isSelected) {
                    btnGhi.disabled = false;
                    btnGhi.dataset.formActive = 'true';
                }
            }
        });
        
        // Critical Bounds Validation Ngầm Realtime (Dành cho CRITICAL.md)
        el.addEventListener('input', () => {
            let errorMsg = null;
            if (el.id === 'fHK' || el.id === 'fHOCKY') {
                const cv = parseInt(el.value);
                if (cv < 1 || cv > 3) errorMsg = "Học kỳ bắt buộc từ 1 đến 3.";
            } else if (el.id === 'fNHOM') {
                const cv = parseInt(el.value);
                if (cv < 1) errorMsg = "Nhóm môn học tối thiểu là 1.";
            } else if (el.id === 'fSOSV' || el.id === 'fSOSVTOITHIEU') {
                const cv = parseInt(el.value);
                if (cv <= 0) errorMsg = "Số sinh viên chuẩn tối thiểu > 0.";
            } else if (el.id === 'fSOTIET_LT' || el.id === 'fSOTIET_TH') {
                const cv = parseInt(el.value);
                if (cv < 0) errorMsg = "Số tiết không được mang giá trị âm.";
            } else if (el.id === 'fDIEM_CC' || el.id === 'fDIEM_GK' || el.id === 'fDIEM_CK') {
                const cv = parseFloat(el.value);
                if (cv < 0 || cv > 10) errorMsg = "Điểm số cấu thành phải từ 0 - 10.";
            }
            
            if (errorMsg) {
                setValidationMsg(el.id, errorMsg, true);
                updateSaveButton('error'); // Khóa cấm nút
            } else {
                setValidationMsg(el.id, '', false); // Clear
                // check if any other errors exist
                const anyError = document.querySelector('[id^="err_f"][style*="display: block"]');
                if (!anyError) {
                    updateSaveButton('ok'); // Trả lại formHasError = false
                }
            }
        });
    });
}

async function checkCanDelete(typeStr, idVal) {
    const btnXoa = document.getElementById('btnXoa');
    if (!btnXoa || !idVal) return;
    try {
        const res = await fetch(`/api/can_delete?type=${typeStr}&id=${encodeURIComponent(idVal)}`);
        const data = await res.json();
        // Không được re-enable nếu form đang có lỗi (VD: báo lỗi đóng băng)
        if (!formHasError) {
            btnXoa.disabled = !data.can_delete;
        } else {
            btnXoa.disabled = true;
        }
        btnXoa.title = data.can_delete ? '' : 'Không thể xóa vì dữ liệu đang có ràng buộc con.';
    } catch(e) { console.error(e); }
}

function checkRealtime(inputId, typeStr) {
    const el = document.getElementById(inputId);
    if (!el) return;
    
    let timer = null;
    el.addEventListener('input', () => {
        setValidationMsg(inputId, null);
        
        if (el.readOnly) return; 
        const val = el.value.trim();
        if (!val) {
            return;
        }
        
        clearTimeout(timer);
        timer = setTimeout(async () => {
            try {
                if(el.readOnly) return; 
                const res = await fetch(`/api/check_exists?type=${typeStr}&id=${encodeURIComponent(val)}`);
                const data = await res.json();
                
                if (data.exists && !el.readOnly) {
                    setValidationMsg(inputId, 'Mã này đã tồn tại!', true);
                    updateActionButtons('error');
                } else if (!data.exists && !el.readOnly) {
                    setValidationMsg(inputId, 'Mã hợp lệ.', false);
                    resetValidationState(inputId); // Khôi phục trạng thái nút khi mã hợp lệ
                }
            } catch(e) {}
        }, 500);
    });
}

function resetValidationState(inputId) {
    setValidationMsg(inputId, null);
    const el = document.getElementById(inputId);
    if (el) {
        el.style.borderColor = 'var(--border)';
    }
    // Sửa lỗi: Chỉ reset trạng thái nút nếu không còn any input nào bị lỗi hiển thị
    const visibleErrors = Array.from(document.querySelectorAll('[id^="err_"]')).some(err => err.style.display === 'block');
    
    if (!visibleErrors) {
        formHasError = false;
        // Tình trạng nút phụ thuộc vào việc có dữ liệu đang chọn hay không
        const isEditing = typeof sel !== 'undefined' && sel !== null && sel !== '';
        updateActionButtons(isEditing ? 'editing' : 'adding');
    }
}
