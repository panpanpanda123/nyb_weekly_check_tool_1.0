// 周清审核(运营) 前端逻辑

let allItems = [];
let reviews = {};
let currentOperator = '全部';
let currentPage = 1;
let totalPages = 1;
let currentView = 'pending';
let searchMode = false;
let currentFocusIndex = 0;
let visibleCards = [];

document.addEventListener('DOMContentLoaded', async function() {
    await loadOperators();
    await loadReviews();
    await loadItems();
    updateAdminPanel();

    document.getElementById('operatorFilter').addEventListener('change', function(e) {
        currentOperator = e.target.value;
        currentPage = 1;
        searchMode = false;
        document.getElementById('storeSearch').value = '';
        document.getElementById('clearSearchBtn').style.display = 'none';
        loadItems();
        loadReviews();
        updateAdminPanel();
    });

    document.getElementById('pendingTab').addEventListener('click', () => switchView('pending'));
    document.getElementById('completedTab').addEventListener('click', () => switchView('completed'));
    document.getElementById('searchBtn').addEventListener('click', performSearch);
    document.getElementById('storeSearch').addEventListener('keydown', e => { if (e.key === 'Enter') performSearch(); });
    document.getElementById('clearSearchBtn').addEventListener('click', clearSearch);
    document.getElementById('exportBtn').addEventListener('click', exportCSV);
    document.getElementById('syncBtn').addEventListener('click', syncToViewer);
    document.getElementById('uploadFile').addEventListener('change', uploadNewFile);
    document.getElementById('uploadWhitelist').addEventListener('change', uploadWhitelistFile);
    document.getElementById('prevPage').addEventListener('click', () => { if (currentPage > 1) { currentPage--; loadItems(); } });
    document.getElementById('nextPage').addEventListener('click', () => { if (currentPage < totalPages) { currentPage++; loadItems(); } });

    setupKeyboardNav();
});

function setupKeyboardNav() {
    document.addEventListener('keydown', function(e) {
        const ae = document.activeElement;
        if (ae.tagName === 'INPUT' || ae.tagName === 'TEXTAREA' || ae.tagName === 'SELECT') return;
        updateVisibleCards();
        if (visibleCards.length === 0) return;
        switch(e.key) {
            case 'ArrowLeft': case 'ArrowUp': e.preventDefault(); moveFocus(-1); break;
            case 'ArrowRight': case 'ArrowDown': e.preventDefault(); moveFocus(1); break;
            case 'Enter': e.preventDefault(); markCurrentPass(); break;
            case ' ': e.preventDefault(); markCurrentFail(); break;
        }
    });
}

function updateVisibleCards() {
    visibleCards = Array.from(document.querySelectorAll('.item-card'));
    if (currentFocusIndex >= visibleCards.length) currentFocusIndex = Math.max(0, visibleCards.length - 1);
}

function moveFocus(dir) {
    if (visibleCards.length === 0) return;
    if (visibleCards[currentFocusIndex]) visibleCards[currentFocusIndex].classList.remove('keyboard-focus');
    currentFocusIndex = (currentFocusIndex + dir + visibleCards.length) % visibleCards.length;
    if (visibleCards[currentFocusIndex]) {
        visibleCards[currentFocusIndex].classList.add('keyboard-focus');
        visibleCards[currentFocusIndex].scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function markCurrentPass() {
    if (!visibleCards[currentFocusIndex]) return;
    const id = visibleCards[currentFocusIndex].dataset.itemId;
    if (id) { submitReview(id, '合格'); setTimeout(() => { updateVisibleCards(); moveFocus(1); }, 150); }
}

function markCurrentFail() {
    if (!visibleCards[currentFocusIndex]) return;
    const id = visibleCards[currentFocusIndex].dataset.itemId;
    if (id) submitReview(id, '不合格');
}

async function loadOperators() {
    try {
        const res = await fetch('/api/inspection/operators');
        const ops = await res.json();
        const sel = document.getElementById('operatorFilter');
        // 保留当前选中值
        const current = sel.value;
        // 清空除"全部"外的选项
        while (sel.options.length > 1) sel.remove(1);
        ops.forEach(op => {
            const o = document.createElement('option');
            o.value = op; o.textContent = op;
            sel.appendChild(o);
        });
        // 恢复选中值
        if (current && [...sel.options].some(o => o.value === current)) {
            sel.value = current;
            currentOperator = current;
        }
    } catch(e) { console.error('加载运营人员失败:', e); }
}

async function loadItems() {
    if (searchMode) return;
    try {
        const params = new URLSearchParams({ operator: currentOperator, page: currentPage, per_page: 10 });
        const res = await fetch(`/api/inspection/items?${params}`);
        const data = await res.json();
        allItems = data.items || [];
        totalPages = data.total_pages || 1;

        document.getElementById('reviewedCount').textContent =
            `进度: ${data.total_completed_stores}/${data.total_completed_stores + data.total_pending_stores}`;

        if (currentView === 'pending') renderPendingItems();
        updatePagination();
    } catch(e) { console.error('加载数据失败:', e); showToast('加载失败，请刷新', 'error'); }
}

async function loadReviews() {
    try {
        const params = new URLSearchParams();
        if (currentOperator !== '全部') params.append('operator', currentOperator);
        const res = await fetch(`/api/inspection/reviews?${params}`);
        reviews = await res.json();
    } catch(e) { console.error('加载审核记录失败:', e); }
}

function renderPendingItems() {
    const container = document.getElementById('itemsContainer');
    container.innerHTML = '';

    const pendingItems = allItems.filter(item => {
        const r = reviews[item.id];
        if (!r) return true;
        if (r['审核结果'] === '不合格' && (!r['问题描述'] || !r['问题描述'].trim())) return true;
        if (!r['审核结果']) return true;
        return false;
    });

    if (pendingItems.length === 0 && allItems.length === 0) {
        container.innerHTML = '<div class="empty-msg">📭 暂无检查项数据，请上传Excel</div>';
        return;
    }
    if (pendingItems.length === 0) {
        container.innerHTML = '<div class="empty-msg">🎉 当前页已全部审核完成</div>';
        return;
    }

    pendingItems.forEach(item => container.appendChild(createItemCard(item)));

    setTimeout(() => {
        updateVisibleCards();
        currentFocusIndex = 0;
        if (visibleCards.length > 0) visibleCards[0].classList.add('keyboard-focus');
    }, 100);
}

function createItemCard(item) {
    const card = document.createElement('div');
    card.className = 'item-card';
    card.dataset.itemId = item.id;
    card.dataset.storeId = item['门店编号'];

    const review = reviews[item.id];
    const status = review ? review['审核结果'] : null;
    const note = review ? review['问题描述'] || '' : '';
    const imageUrl = item['标准图'] || '';

    card.innerHTML = `
        <div class="card-header">
            <div class="store-info">
                <div class="store-name">${esc(item['门店名称'])}</div>
                <div class="store-details">
                    <span>${esc(item['门店编号'])}</span>
                    <span>|</span>
                    <span>${esc(item['所属区域'])}</span>
                    <span class="op-badge">👤 ${esc(item['负责运营'])}</span>
                </div>
            </div>
            <div class="item-name">📋 ${esc(item['检查项名称'])}</div>
        </div>
        <div class="card-body">
            <div class="image-container clickable-image">
                ${imageUrl ?
                    `<img alt="${esc(item['检查项名称'])}" loading="lazy" referrerpolicy="no-referrer" data-retry="0">
                     <div class="image-loading">⏳ 加载中...</div>` :
                    '<div class="image-placeholder">📷 暂无图片</div>'}
            </div>
            <div class="review-buttons">
                <button class="review-btn pass ${status === '合格' ? 'active' : ''}"
                        onclick="submitReview('${item.id}', '合格')">✓ 合格</button>
                <button class="review-btn fail ${status === '不合格' ? 'active' : ''}"
                        onclick="submitReview('${item.id}', '不合格')">✗ 不合格</button>
            </div>
            <div class="problem-input-container" id="problem-${item.id}"
                 style="display:${status === '不合格' && !note ? 'block' : 'none'};">
                <label class="problem-label">❗ 问题描述:</label>
                <textarea class="problem-input" id="textarea-${item.id}"
                          placeholder="请输入具体问题..."
                          onkeydown="handleProblemKey(event, '${item.id}')">${esc(note)}</textarea>
                <button class="save-problem-btn" onclick="saveProblem('${item.id}')">✓ 保存</button>
            </div>
        </div>
    `;

    if (imageUrl) {
        const imgContainer = card.querySelector('.image-container');
        const img = imgContainer.querySelector('img');
        const loading = imgContainer.querySelector('.image-loading');
        if (img) {
            img.onload = () => { if (loading) loading.style.display = 'none'; };
            img.onerror = () => handleImgError(img, imageUrl, loading);
            img.src = imageUrl;
        }
        imgContainer.onclick = () => openImageModal(imageUrl, item['门店名称'] + ' - ' + item['检查项名称']);
    }

    return card;
}

async function submitReview(itemId, result) {
    try {
        const problemContainer = document.getElementById(`problem-${itemId}`);
        const existing = reviews[itemId];

        if (result === '不合格') {
            if (existing && existing['审核结果'] === '不合格' && existing['问题描述']) {
                if (problemContainer.style.display === 'none') {
                    problemContainer.style.display = 'block';
                    setTimeout(() => problemContainer.querySelector('.problem-input').focus(), 100);
                } else {
                    problemContainer.style.display = 'none';
                }
                return;
            }
            problemContainer.style.display = 'block';
            setTimeout(() => problemContainer.querySelector('.problem-input').focus(), 100);
        } else {
            problemContainer.style.display = 'none';
        }

        const res = await fetch('/api/inspection/review', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId, '审核结果': result })
        });
        const data = await res.json();

        if (data.success) {
            reviews[itemId] = reviews[itemId] || {};
            reviews[itemId]['审核结果'] = result;
            if (result === '合格') reviews[itemId]['问题描述'] = '';

            updateCardStatus(itemId, result);
            showToast(result === '合格' ? '✓ 已标记合格' : '请输入问题描述', result === '合格' ? 'success' : 'info');

            if (result === '合格') {
                checkAndRemoveCompletedStore(itemId);
            }
        } else {
            showToast('提交失败: ' + (data.error || ''), 'error');
        }
    } catch(e) { showToast('网络错误', 'error'); }
}

function updateCardStatus(itemId, result) {
    const card = document.querySelector(`[data-item-id="${itemId}"]`);
    if (!card) return;
    card.querySelectorAll('.review-btn').forEach(btn => btn.classList.remove('active'));
    if (result === '合格') card.querySelector('.review-btn.pass').classList.add('active');
    else card.querySelector('.review-btn.fail').classList.add('active');
}

function checkAndRemoveCompletedStore(itemId) {
    const card = document.querySelector(`[data-item-id="${itemId}"]`);
    if (!card) return;
    const storeId = card.dataset.storeId;
    const storeCards = document.querySelectorAll(`[data-store-id="${storeId}"]`);
    let allDone = true;
    storeCards.forEach(c => {
        const id = c.dataset.itemId;
        const r = reviews[id];
        if (!r || !r['审核结果']) { allDone = false; return; }
        if (r['审核结果'] === '不合格' && (!r['问题描述'] || !r['问题描述'].trim())) { allDone = false; }
    });
    if (allDone) {
        storeCards.forEach(c => {
            c.style.transition = 'opacity 0.3s, transform 0.3s';
            c.style.opacity = '0';
            c.style.transform = 'scale(0.95)';
            setTimeout(() => c.remove(), 300);
        });
        setTimeout(() => {
            showToast(`✓ 门店 ${storeId} 审核完成`, 'success');
            loadItems();
        }, 400);
    }
}

function handleProblemKey(event, itemId) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        saveProblem(itemId);
    }
}

async function saveProblem(itemId) {
    const textarea = document.getElementById(`textarea-${itemId}`);
    const note = textarea.value.trim();
    if (!note) { showToast('⚠️ 请输入问题描述', 'error'); textarea.focus(); return; }

    try {
        const res = await fetch('/api/inspection/review/problem', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId, '问题描述': note })
        });
        const data = await res.json();
        if (data.success) {
            reviews[itemId] = reviews[itemId] || {};
            reviews[itemId]['问题描述'] = note;
            document.getElementById(`problem-${itemId}`).style.display = 'none';
            showToast('✓ 已保存', 'success');
            checkAndRemoveCompletedStore(itemId);
        } else {
            showToast('保存失败', 'error');
        }
    } catch(e) { showToast('网络错误', 'error'); }
}

function switchView(view) {
    currentView = view;
    document.getElementById('pendingTab').classList.toggle('active', view === 'pending');
    document.getElementById('completedTab').classList.toggle('active', view === 'completed');
    document.getElementById('pagination').style.display = view === 'pending' ? 'flex' : 'none';
    if (view === 'pending') { searchMode = false; loadItems(); }
    else loadCompletedStores();
}

async function loadCompletedStores() {
    try {
        const params = new URLSearchParams({ operator: currentOperator });
        const res = await fetch(`/api/inspection/completed?${params}`);
        const stores = await res.json();
        renderCompletedStores(stores);
    } catch(e) { showToast('加载失败', 'error'); }
}

function renderCompletedStores(stores) {
    const container = document.getElementById('itemsContainer');
    container.innerHTML = '';
    if (stores.length === 0) {
        container.innerHTML = '<div class="empty-msg">暂无已完成的门店</div>';
        return;
    }
    stores.forEach(store => {
        const card = document.createElement('div');
        card.className = 'completed-store-card';
        card.innerHTML = `
            <div class="completed-header">
                <div class="store-info">
                    <div class="store-name">✓ ${esc(store.store_name)}</div>
                    <div class="store-details">
                        <span>${esc(store.store_id)}</span>
                        <span>|</span>
                        <span>👤 ${esc(store.operator)}</span>
                    </div>
                </div>
                <div class="completed-time">${esc(store.completed_time)}</div>
            </div>
            <div class="completed-stats">
                <span class="stat-badge">共${store.total_count}项</span>
                <span class="stat-badge pass">合格${store.pass_count}</span>
                <span class="stat-badge fail">不合格${store.fail_count}</span>
            </div>
        `;
        container.appendChild(card);
    });
}

function performSearch() {
    const keyword = document.getElementById('storeSearch').value.trim();
    if (!keyword) { showToast('请输入门店编号或名称', 'error'); return; }
    searchMode = true;
    const matched = allItems.filter(item =>
        item['门店编号'] === keyword || item['门店名称'] === keyword
    );
    if (matched.length === 0) {
        showToast('未找到匹配门店', 'error');
        return;
    }
    document.getElementById('clearSearchBtn').style.display = 'inline-block';
    const container = document.getElementById('itemsContainer');
    container.innerHTML = `<div class="search-header">🔍 搜索结果：${matched.length} 个检查项</div>`;
    matched.forEach(item => container.appendChild(createItemCard(item)));
}

function clearSearch() {
    searchMode = false;
    document.getElementById('storeSearch').value = '';
    document.getElementById('clearSearchBtn').style.display = 'none';
    loadItems();
}

function updatePagination() {
    const pag = document.getElementById('pagination');
    if (currentView !== 'pending') { pag.style.display = 'none'; return; }
    pag.style.display = totalPages > 1 ? 'flex' : 'none';
    document.getElementById('pageInfo').textContent = `${currentPage}/${totalPages}`;
    document.getElementById('prevPage').disabled = currentPage <= 1;
    document.getElementById('nextPage').disabled = currentPage >= totalPages;
}

function updateAdminPanel() {
    const panel = document.getElementById('adminPanel');
    const op = currentOperator;
    panel.style.display = (op === '袁') ? 'block' : 'none';
}

async function exportCSV() {
    try {
        showToast('⏳ 正在导出...', 'info');
        const res = await fetch('/api/inspection/export');
        if (!res.ok) { const d = await res.json(); showToast(d.error || '导出失败', 'error'); return; }
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `审核结果_${new Date().toISOString().slice(0,10)}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('✓ 导出成功', 'success');
    } catch(e) { showToast('导出失败', 'error'); }
}

async function syncToViewer() {
    if (!confirm('确定将审核结果同步到展示系统？这会覆盖展示系统中的现有数据。')) return;
    try {
        showToast('⏳ 正在同步...', 'info');
        const res = await fetch('/api/inspection/sync-to-viewer', { method: 'POST' });
        const data = await res.json();
        if (data.success) showToast(`✓ ${data.message}`, 'success');
        else showToast(data.error || '同步失败', 'error');
    } catch(e) { showToast('同步失败', 'error'); }
}

async function uploadNewFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    if (!confirm(`确定上传 ${file.name} 开始新周期？这会清空现有审核数据。`)) {
        e.target.value = ''; return;
    }
    try {
        showToast('⏳ 正在上传检查项...', 'info');
        const fd = new FormData();
        fd.append('file', file);
        const res = await fetch('/api/inspection/upload', { method: 'POST', body: fd });
        const data = await res.json();
        if (data.success) {
            showToast(`✓ ${data.message}`, 'success');
            reviews = {};
            currentPage = 1;
            await loadOperators();
            await loadReviews();
            await loadItems();
        } else {
            showToast(data.error || '上传失败', 'error');
        }
    } catch(e) { showToast('上传失败', 'error'); }
    e.target.value = '';
}

async function uploadWhitelistFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    if (!confirm(`确定上传白名单 ${file.name}？这会更新所有门店的运营人员关联。`)) {
        e.target.value = ''; return;
    }
    try {
        showToast('⏳ 正在上传白名单...', 'info');
        const fd = new FormData();
        fd.append('file', file);
        const res = await fetch('/api/upload/whitelist', { method: 'POST', body: fd });
        const data = await res.json();
        if (data.success) {
            showToast(`✓ ${data.message}`, 'success');
        } else {
            showToast(data.error || '上传失败', 'error');
        }
    } catch(e) { showToast('白名单上传失败', 'error'); }
    e.target.value = '';
}

// 图片相关
function handleImgError(img, url, loadingDiv) {
    const retry = parseInt(img.dataset.retry || '0');
    if (retry < 3) {
        img.dataset.retry = (retry + 1).toString();
        if (loadingDiv) { loadingDiv.textContent = `⏳ 重试(${retry+1}/3)...`; loadingDiv.style.display = 'block'; }
        setTimeout(() => { img.src = url + '?r=' + Date.now(); }, 1000 * (retry + 1));
    } else {
        if (loadingDiv) loadingDiv.style.display = 'none';
        img.style.display = 'none';
        const err = document.createElement('div');
        err.className = 'image-error';
        err.innerHTML = '❌ 图片加载失败<br><button onclick="retryImg(this)" style="margin-top:5px;padding:4px 10px;cursor:pointer;border:none;background:#667eea;color:white;border-radius:4px;">🔄 重试</button>';
        err.dataset.url = url;
        img.parentElement.appendChild(err);
    }
}

function retryImg(btn) {
    const errDiv = btn.parentElement;
    const container = errDiv.parentElement;
    const img = container.querySelector('img');
    if (img) {
        img.dataset.retry = '0'; img.style.display = 'block'; errDiv.remove();
        img.src = errDiv.dataset.url + '?m=' + Date.now();
    }
}

function openImageModal(src, caption) {
    if (!src) return;
    const modal = document.getElementById('imageModal');
    document.getElementById('modalImage').src = src;
    document.getElementById('modalCaption').textContent = caption;
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeImageModal() {
    document.getElementById('imageModal').classList.remove('show');
    document.body.style.overflow = 'auto';
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeImageModal(); });
window.addEventListener('popstate', () => {
    const m = document.getElementById('imageModal');
    if (m && m.classList.contains('show')) { m.classList.remove('show'); document.body.style.overflow = 'auto'; }
});

function showToast(msg, type = 'success') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = `toast ${type} show`;
    setTimeout(() => t.classList.remove('show'), 3000);
}

function esc(text) {
    if (!text) return '';
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
}
