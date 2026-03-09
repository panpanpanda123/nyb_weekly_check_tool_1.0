// 活动参与度监控 JavaScript

// 全局变量
let currentPage = 1;
let currentFilters = {
    war_zone: '',
    regional_manager: '',
    store_search: '',
    sort_by: 'participation_rate',
    sort_order: 'desc'
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadFilters();
    loadAllRegionalManagers();
    searchStores();
    
    // 绑定事件
    document.getElementById('warZoneFilter').addEventListener('change', onWarZoneChange);
    document.getElementById('storeSearch').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchStores();
        }
    });
    document.getElementById('sortByFilter').addEventListener('change', searchStores);
    document.getElementById('sortOrderFilter').addEventListener('change', searchStores);
});

// 加载筛选选项
async function loadFilters() {
    try {
        const response = await fetch('/api/promo/filters');
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            
            // 填充战区选项
            const warZoneSelect = document.getElementById('warZoneFilter');
            data.war_zones.forEach(zone => {
                const option = document.createElement('option');
                option.value = zone;
                option.textContent = zone;
                warZoneSelect.appendChild(option);
            });
            
            // 显示数据日期
            if (data.data_date) {
                document.getElementById('dataDate').textContent = data.data_date;
                document.getElementById('dataTimeInfo').style.display = 'block';
            }
        }
    } catch (error) {
        console.error('加载筛选选项失败:', error);
    }
}


// 加载所有区域经理（不依赖战区）
async function loadAllRegionalManagers() {
    try {
        const response = await fetch('/api/promo/all-regional-managers');
        const result = await response.json();
        
        if (result.success) {
            const select = document.getElementById('regionalManagerFilter');
            // 清空现有选项（保留"全部"选项）
            select.innerHTML = '<option value="">全部区域经理</option>';
            
            result.data.regional_managers.forEach(manager => {
                const option = document.createElement('option');
                option.value = manager;
                option.textContent = manager;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载区域经理列表失败:', error);
    }
}

// 战区变更事件
async function onWarZoneChange() {
    const warZone = document.getElementById('warZoneFilter').value;
    
    if (!warZone) {
        // 如果没有选择战区，加载所有区域经理
        loadAllRegionalManagers();
        return;
    }
    
    try {
        const response = await fetch(`/api/promo/regional-managers?war_zone=${encodeURIComponent(warZone)}`);
        const result = await response.json();
        
        if (result.success) {
            const select = document.getElementById('regionalManagerFilter');
            select.innerHTML = '<option value="">全部区域经理</option>';
            
            result.data.regional_managers.forEach(manager => {
                const option = document.createElement('option');
                option.value = manager;
                option.textContent = manager;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载区域经理列表失败:', error);
    }
}

// 搜索门店
async function searchStores(page = 1) {
    currentPage = page;
    
    // 更新筛选条件
    currentFilters.war_zone = document.getElementById('warZoneFilter').value;
    currentFilters.regional_manager = document.getElementById('regionalManagerFilter').value;
    currentFilters.store_search = document.getElementById('storeSearch').value.trim();
    currentFilters.sort_by = document.getElementById('sortByFilter').value;
    currentFilters.sort_order = document.getElementById('sortOrderFilter').value;
    
    // 显示加载提示
    showLoading(true);
    
    try {
        const params = new URLSearchParams({
            page: currentPage,
            per_page: 20,
            ...currentFilters
        });
        
        const response = await fetch(`/api/promo/search?${params}`);
        const result = await response.json();
        
        if (result.success) {
            displayStores(result.data);
        } else {
            alert('搜索失败: ' + result.error);
        }
    } catch (error) {
        console.error('搜索失败:', error);
        alert('搜索失败，请稍后重试');
    } finally {
        showLoading(false);
    }
}


// 显示门店列表
function displayStores(data) {
    const container = document.getElementById('storeListContainer');
    
    // 更新统计信息
    document.getElementById('totalStores').textContent = data.total;
    
    // 清空容器
    container.innerHTML = '';
    
    if (data.stores.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <div class="empty-state-text">暂无数据</div>
                <div class="empty-state-hint">请尝试调整筛选条件</div>
            </div>
        `;
        document.getElementById('pagination').innerHTML = '';
        return;
    }
    
    // 渲染门店卡片
    data.stores.forEach(store => {
        const card = createStoreCard(store);
        container.appendChild(card);
    });
    
    // 渲染分页
    renderPagination(data);
}

// 创建门店卡片
function createStoreCard(store) {
    const card = document.createElement('div');
    card.className = 'store-card';
    
    card.innerHTML = `
        <div class="store-header">
            <div class="store-info">
                <div class="store-title">
                    ${store.store_name || store.store_id}
                </div>
                <div class="store-meta">
                    <span>门店ID: ${store.store_id}</span>
                    <span>战区: ${store.war_zone || '-'}</span>
                    <span>区域经理: ${store.regional_manager || '-'}</span>
                </div>
            </div>
            <div class="participation-badge">
                ${store.participation_rate}
            </div>
        </div>
        <div class="promo-metrics">
            <div class="metric-item">
                <div class="metric-label">订单量</div>
                <div class="metric-value">${store.order_count}</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">权益卡销量</div>
                <div class="metric-value">${store.benefit_card_sales}</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">活动套餐销量</div>
                <div class="metric-value">${store.promo_package_sales}</div>
            </div>
        </div>
    `;
    
    return card;
}

// 渲染分页
function renderPagination(data) {
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';
    
    if (data.total_pages <= 1) {
        return;
    }
    
    // 上一页按钮
    if (data.page > 1) {
        const prevBtn = document.createElement('button');
        prevBtn.className = 'page-btn';
        prevBtn.textContent = '上一页';
        prevBtn.onclick = () => searchStores(data.page - 1);
        pagination.appendChild(prevBtn);
    }
    
    // 页码信息
    const pageInfo = document.createElement('span');
    pageInfo.className = 'page-info';
    pageInfo.textContent = `第 ${data.page} / ${data.total_pages} 页`;
    pagination.appendChild(pageInfo);
    
    // 下一页按钮
    if (data.has_more) {
        const nextBtn = document.createElement('button');
        nextBtn.className = 'page-btn';
        nextBtn.textContent = '下一页';
        nextBtn.onclick = () => searchStores(data.page + 1);
        pagination.appendChild(nextBtn);
    }
}

// 显示/隐藏加载提示
function showLoading(show) {
    const indicator = document.getElementById('loadingIndicator');
    indicator.style.display = show ? 'flex' : 'none';
}

// 导出数据
async function exportData() {
    try {
        showLoading(true);
        window.location.href = '/api/promo/export';
    } catch (error) {
        console.error('导出失败:', error);
        alert('导出失败，请稍后重试');
    } finally {
        setTimeout(() => showLoading(false), 1000);
    }
}
