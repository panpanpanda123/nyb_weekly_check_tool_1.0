// 活动参与度监控 JavaScript（新版）

const API_BASE_PATH = '';
let currentPage = 1;
let totalPages = 1;
let overviewData = null;
let currentOverviewTab = 'war_zone';

let filters = {
    war_zone: '',
    war_zone_manager: '',
    regional_manager: '',
    city_operator: '',
    store_search: '',
    sort_by: 'participation_rate',
    sort_order: 'asc'
};

document.addEventListener('DOMContentLoaded', function() {
    initPromoPage();
});

async function initPromoPage() {
    try {
        await Promise.all([loadFilterOptions(), loadOverview()]);
        setupEventListeners();
    } catch (error) {
        console.error('初始化失败:', error);
        showToast('页面初始化失败，请刷新', 'error');
    }
}

// ========== 概览 ==========

async function loadOverview() {
    try {
        const resp = await fetch(`${API_BASE_PATH}/api/promo/overview`);
        const result = await resp.json();
        if (!result.success) throw new Error(result.error);

        overviewData = result.data;
        document.getElementById('globalAvg').textContent =
            (overviewData.global_avg * 100).toFixed(1) + '%';
        document.getElementById('totalStores').textContent =
            overviewData.total_stores + '家';

        renderOverviewTab(currentOverviewTab);
    } catch (e) {
        console.error('加载概览失败:', e);
        document.getElementById('overviewContent').innerHTML =
            '<div class="loading-text">概览加载失败</div>';
    }
}

function renderOverviewTab(tab) {
    if (!overviewData) return;
    currentOverviewTab = tab;

    // 更新tab样式
    document.querySelectorAll('.overview-tab').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });

    const keyMap = {
        'war_zone': 'by_war_zone',
        'war_zone_manager': 'by_war_zone_manager',
        'regional_manager': 'by_regional_manager',
        'city_operator': 'by_city_operator',
    };
    const items = overviewData[keyMap[tab]] || [];
    const container = document.getElementById('overviewContent');

    if (!items.length) {
        container.innerHTML = '<div class="loading-text">暂无数据</div>';
        return;
    }

    // 找最大值用于柱状图宽度
    const maxRate = Math.max(...items.map(i => i.avg_rate), 0.01);

    container.innerHTML = `
        <div class="rank-list">
            ${items.map((item, idx) => {
                const pct = (item.avg_rate * 100).toFixed(1);
                const barWidth = Math.max(5, (item.avg_rate / maxRate) * 100);
                const color = item.avg_rate >= 0.15 ? '#28a745'
                    : item.avg_rate >= 0.10 ? '#ffc107'
                    : '#dc3545';
                return `
                    <div class="rank-item" data-tab="${tab}" data-name="${escapeHtml(item.name)}">
                        <div class="rank-index">${idx + 1}</div>
                        <div class="rank-info">
                            <div class="rank-name">${escapeHtml(item.name)}</div>
                            <div class="rank-bar-bg">
                                <div class="rank-bar" style="width:${barWidth}%;background:${color};"></div>
                            </div>
                        </div>
                        <div class="rank-stats">
                            <span class="rank-rate" style="color:${color}">${pct}%</span>
                            <span class="rank-detail">${item.store_count}店 / ${item.total_orders}单</span>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;

    // 点击排名项可以筛选
    container.querySelectorAll('.rank-item').forEach(el => {
        el.addEventListener('click', () => {
            const t = el.dataset.tab;
            const name = el.dataset.name;
            if (t === 'war_zone') {
                document.getElementById('warZoneFilter').value = name;
                filters.war_zone = name;
            } else if (t === 'war_zone_manager') {
                document.getElementById('warZoneManagerFilter').value = name;
                filters.war_zone_manager = name;
            } else if (t === 'regional_manager') {
                document.getElementById('regionalManagerFilter').value = name;
                filters.regional_manager = name;
            } else if (t === 'city_operator') {
                document.getElementById('cityOperatorFilter').value = name;
                filters.city_operator = name;
            }
            currentPage = 1;
            searchStores();
            // 滚动到明细区域
            document.getElementById('resultsContainer').scrollIntoView({ behavior: 'smooth' });
        });
    });
}

// ========== 筛选 ==========

async function loadFilterOptions() {
    const resp = await fetch(`${API_BASE_PATH}/api/promo/filters`);
    const result = await resp.json();
    if (!result.success) throw new Error(result.error);

    const data = result.data;

    fillSelect('warZoneFilter', data.war_zones);
    fillSelect('warZoneManagerFilter', data.war_zone_managers);
    fillSelect('cityOperatorFilter', data.city_operators);

    // 区域经理用datalist
    await loadAllRegionalManagers();

    if (data.data_date) {
        document.getElementById('dataDate').textContent = data.data_date;
        document.getElementById('dataTimeInfo').style.display = 'block';
    }
}

function fillSelect(id, options) {
    const sel = document.getElementById(id);
    sel.innerHTML = '<option value="">全部</option>';
    options.forEach(o => {
        sel.innerHTML += `<option value="${escapeHtml(o)}">${escapeHtml(o)}</option>`;
    });
}

async function loadAllRegionalManagers() {
    const resp = await fetch(`${API_BASE_PATH}/api/promo/all-regional-managers`);
    const result = await resp.json();
    if (result.success) {
        window.allRegionalManagers = result.data.regional_managers;
        updateRegionalManagerDatalist(result.data.regional_managers);
    }
}

function updateRegionalManagerDatalist(managers) {
    const dl = document.getElementById('regionalManagerList');
    dl.innerHTML = '';
    managers.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m;
        dl.appendChild(opt);
    });
}

// ========== 事件 ==========

function setupEventListeners() {
    // 导航
    document.getElementById('reviewTab').addEventListener('click', () => window.location.href = '/');
    document.getElementById('ratingTab').addEventListener('click', () => window.location.href = '/rating');
    document.getElementById('equipmentTab').addEventListener('click', () => window.location.href = '/equipment');

    // 概览tab切换
    document.querySelectorAll('.overview-tab').forEach(btn => {
        btn.addEventListener('click', () => renderOverviewTab(btn.dataset.tab));
    });

    // 筛选变化
    document.getElementById('warZoneFilter').addEventListener('change', async (e) => {
        filters.war_zone = e.target.value;
        const resp = await fetch(`${API_BASE_PATH}/api/promo/regional-managers?war_zone=${encodeURIComponent(filters.war_zone)}&war_zone_manager=${encodeURIComponent(filters.war_zone_manager)}`);
        const result = await resp.json();
        if (result.success) updateRegionalManagerDatalist(result.data.regional_managers);
        document.getElementById('regionalManagerFilter').value = '';
        filters.regional_manager = '';
    });

    document.getElementById('warZoneManagerFilter').addEventListener('change', (e) => {
        filters.war_zone_manager = e.target.value;
    });

    document.getElementById('regionalManagerFilter').addEventListener('change', (e) => {
        filters.regional_manager = e.target.value.trim();
    });
    document.getElementById('regionalManagerFilter').addEventListener('input', (e) => {
        filters.regional_manager = e.target.value.trim();
    });

    document.getElementById('cityOperatorFilter').addEventListener('change', (e) => {
        filters.city_operator = e.target.value;
    });

    // 门店搜索
    const storeInput = document.getElementById('storeSearch');
    const clearStoreBtn = document.getElementById('clearStoreSearchBtn');
    document.getElementById('storeSearchBtn').addEventListener('click', () => {
        filters.store_search = storeInput.value.trim();
        if (filters.store_search) clearStoreBtn.style.display = 'inline-block';
        currentPage = 1;
        searchStores();
    });
    clearStoreBtn.addEventListener('click', () => {
        storeInput.value = '';
        filters.store_search = '';
        clearStoreBtn.style.display = 'none';
        currentPage = 1;
        searchStores();
    });
    storeInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') document.getElementById('storeSearchBtn').click();
    });

    // 排序
    document.getElementById('sortByFilter').addEventListener('change', (e) => filters.sort_by = e.target.value);
    document.getElementById('sortOrderFilter').addEventListener('change', (e) => filters.sort_order = e.target.value);

    // 搜索/清除
    document.getElementById('searchBtn').addEventListener('click', () => { currentPage = 1; searchStores(); });
    document.getElementById('clearBtn').addEventListener('click', clearFilters);

    // 导出
    document.getElementById('exportBtn').addEventListener('click', () => {
        showToast('正在导出...', 'info');
        window.location.href = `${API_BASE_PATH}/api/promo/export`;
        setTimeout(() => showToast('✓ 导出成功', 'success'), 1000);
    });

    // 分页
    document.getElementById('prevPage').addEventListener('click', () => {
        if (currentPage > 1) { currentPage--; searchStores(); }
    });
    document.getElementById('nextPage').addEventListener('click', () => {
        if (currentPage < totalPages) { currentPage++; searchStores(); }
    });
}

function clearFilters() {
    document.getElementById('warZoneFilter').value = '';
    document.getElementById('warZoneManagerFilter').value = '';
    document.getElementById('regionalManagerFilter').value = '';
    document.getElementById('cityOperatorFilter').value = '';
    document.getElementById('storeSearch').value = '';
    document.getElementById('clearStoreSearchBtn').style.display = 'none';
    document.getElementById('sortByFilter').value = 'participation_rate';
    document.getElementById('sortOrderFilter').value = 'asc';

    filters = {
        war_zone: '', war_zone_manager: '', regional_manager: '',
        city_operator: '', store_search: '',
        sort_by: 'participation_rate', sort_order: 'asc'
    };
    currentPage = 1;

    if (window.allRegionalManagers) updateRegionalManagerDatalist(window.allRegionalManagers);

    document.getElementById('resultsContainer').innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">📊</div>
            <h2>点击"搜索"查看门店明细</h2>
        </div>`;
    document.getElementById('paginationContainer').style.display = 'none';
    document.getElementById('resultCount').textContent = '门店总数: 0';
}

// ========== 搜索 ==========

async function searchStores(page) {
    if (page !== undefined) currentPage = page;

    try {
        showLoading();
        const params = new URLSearchParams({ page: currentPage, per_page: 20, ...filters });
        const resp = await fetch(`${API_BASE_PATH}/api/promo/search?${params}`);
        const result = await resp.json();

        if (!result.success) throw new Error(result.error);

        const data = result.data;
        totalPages = data.total_pages;
        document.getElementById('resultCount').textContent = `门店总数: ${data.total}`;
        renderStoreList(data.stores);

        if (data.total > 0) {
            document.getElementById('paginationContainer').style.display = 'flex';
            document.getElementById('prevPage').disabled = currentPage === 1;
            document.getElementById('nextPage').disabled = currentPage >= totalPages;
            document.getElementById('pageInfo').textContent = `第 ${currentPage} / ${totalPages} 页`;
        } else {
            document.getElementById('paginationContainer').style.display = 'none';
        }
    } catch (e) {
        console.error('搜索失败:', e);
        showError('搜索失败，请重试');
    }
}

function renderStoreList(stores) {
    const container = document.getElementById('resultsContainer');

    if (!stores || !stores.length) {
        container.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">📭</div>
                <h2>暂无数据</h2>
            </div>`;
        return;
    }

    container.innerHTML = stores.map(s => {
        const rate = s.participation_rate || 0;
        const pct = (rate * 100).toFixed(1);
        const color = rate >= 0.15 ? '#28a745' : rate >= 0.10 ? '#ffc107' : '#dc3545';

        return `
            <div class="store-card-compact">
                <div class="store-info-compact">
                    <div class="store-name-mini">${escapeHtml(s.store_name)}</div>
                    <div class="store-meta-mini">
                        ${escapeHtml(s.store_id)} · ${escapeHtml(s.war_zone)} · ${escapeHtml(s.war_zone_manager)} · ${escapeHtml(s.regional_manager)} · ${escapeHtml(s.city_operator)}
                    </div>
                </div>
                <div class="metrics-compact">
                    <div class="metric-mini">
                        <span class="metric-value-mini">${s.order_count}</span>
                        <span class="metric-label-mini">堂食订单</span>
                    </div>
                    <div class="metric-mini">
                        <span class="metric-value-mini">${s.pos_order_count}</span>
                        <span class="metric-label-mini">POS</span>
                    </div>
                    <div class="metric-mini">
                        <span class="metric-value-mini">${s.scan_order_count}</span>
                        <span class="metric-label-mini">扫码</span>
                    </div>
                    <div class="metric-mini">
                        <span class="metric-value-mini">${s.benefit_card_sales}</span>
                        <span class="metric-label-mini">权益卡</span>
                    </div>
                    <div class="metric-mini">
                        <span class="metric-value-mini">${s.promo_package_sales}</span>
                        <span class="metric-label-mini">套餐</span>
                    </div>
                    <div class="metric-mini participation">
                        <span class="metric-value-mini" style="color:${color};font-weight:700;">${pct}%</span>
                        <span class="metric-label-mini">参与度</span>
                    </div>
                </div>
            </div>`;
    }).join('');
}

// ========== 工具 ==========

function showLoading() {
    document.getElementById('resultsContainer').innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">⏳</div>
            <h2>加载中...</h2>
        </div>`;
}

function showError(msg) {
    document.getElementById('resultsContainer').innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">❌</div>
            <h2>${escapeHtml(msg)}</h2>
        </div>`;
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => toast.classList.remove('show'), 3000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
