// 门店评级系统前端逻辑

// API 基础路径配置 - 根据当前路径自动检测
const API_BASE_PATH = window.location.pathname.includes('/weeklycheck/') ? '/weeklycheck' : '';

// 全局状态
let filterOptions = {
    war_zones: [],
    regional_managers: []
};

let currentFilters = {
    war_zone: '',
    regional_manager: ''
};

let currentPage = 1;
let totalPages = 1;
let storesData = [];
let isLoading = false;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 门店评级系统加载开始...');
    
    // 加载筛选选项
    await loadFilterOptions();
    
    // 绑定事件
    bindEvents();
    
    // 显示首页统计
    await loadCompletionStats();
    
    console.log('✅ 页面初始化完成');
});

/**
 * 加载筛选选项
 */
async function loadFilterOptions() {
    try {
        showToast('正在加载筛选选项...', 'info');
        
        // 加载战区列表
        const warZonesResponse = await fetch(`${API_BASE_PATH}/api/rating/war-zones`);
        const warZonesData = await warZonesResponse.json();
        
        if (warZonesData.success) {
            filterOptions.war_zones = warZonesData.data.war_zones;
            populateSelect('warZoneFilter', filterOptions.war_zones);
        }
        
        console.log('✅ 筛选选项加载完成');
    } catch (error) {
        console.error('加载筛选选项失败:', error);
        showToast('加载筛选选项失败，请刷新页面重试', 'error');
    }
}

/**
 * 填充下拉菜单
 */
function populateSelect(selectId, options) {
    const select = document.getElementById(selectId);
    
    // 清空现有选项（保留"全部"选项）
    while (select.options.length > 1) {
        select.remove(1);
    }
    
    // 添加新选项
    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option;
        optionElement.textContent = option;
        select.appendChild(optionElement);
    });
}

/**
 * 绑定事件
 */
function bindEvents() {
    // 选项卡切换
    document.getElementById('reviewTab').addEventListener('click', function() {
        window.location.href = '/';
    });
    document.getElementById('equipmentTab').addEventListener('click', function() {
        window.location.href = '/equipment';
    });
    
    // 战区选择变化 - 级联更新区域经理
    document.getElementById('warZoneFilter').addEventListener('change', async function(e) {
        const warZone = e.target.value;
        currentFilters.war_zone = warZone;
        
        // 清空区域经理
        currentFilters.regional_manager = '';
        document.getElementById('regionalManagerFilter').value = '';
        
        if (warZone) {
            // 加载区域经理列表
            await loadRegionalManagers(warZone);
        } else {
            // 清空区域经理选项
            populateSelect('regionalManagerFilter', []);
        }
    });
    
    // 区域经理选择变化
    document.getElementById('regionalManagerFilter').addEventListener('change', function(e) {
        currentFilters.regional_manager = e.target.value;
    });
    
    // 搜索按钮
    document.getElementById('searchBtn').addEventListener('click', performSearch);
    
    // 清除筛选按钮
    document.getElementById('clearBtn').addEventListener('click', clearFilters);
    
    // 导出按钮
    document.getElementById('exportBtn').addEventListener('click', exportRatings);
    
    // 分页按钮
    document.getElementById('prevPageBtn').addEventListener('click', prevPage);
    document.getElementById('nextPageBtn').addEventListener('click', nextPage);
    
    // 确认对话框按钮
    document.getElementById('confirmYes').addEventListener('click', function() {
        hideConfirmDialog();
        nextPage();
    });
    
    document.getElementById('confirmNo').addEventListener('click', function() {
        hideConfirmDialog();
    });
}

/**
 * 根据战区加载区域经理列表
 */
async function loadRegionalManagers(warZone) {
    try {
        const response = await fetch(`${API_BASE_PATH}/api/rating/regional-managers?war_zone=${encodeURIComponent(warZone)}`);
        const data = await response.json();
        
        if (data.success) {
            filterOptions.regional_managers = data.data.regional_managers;
            populateSelect('regionalManagerFilter', filterOptions.regional_managers);
        } else {
            showToast('加载区域经理列表失败: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('加载区域经理列表失败:', error);
        showToast('加载区域经理列表失败', 'error');
    }
}

/**
 * 执行搜索
 */
async function performSearch() {
    // 重置分页
    currentPage = 1;
    
    // 加载门店列表
    await loadStores();
}

/**
 * 加载门店列表
 */
async function loadStores() {
    if (isLoading) return;
    
    try {
        isLoading = true;
        
        // 显示加载状态
        showLoading();
        
        // 构建查询参数
        const params = new URLSearchParams();
        if (currentFilters.war_zone) params.append('war_zone', currentFilters.war_zone);
        if (currentFilters.regional_manager) params.append('regional_manager', currentFilters.regional_manager);
        params.append('page', currentPage);
        params.append('per_page', 5);  // 每页5家门店
        
        const response = await fetch(`${API_BASE_PATH}/api/rating/stores?${params.toString()}`);
        const data = await response.json();
        
        if (data.success) {
            storesData = data.data.stores;
            totalPages = data.data.total_pages;
            
            renderStores(storesData);
            updatePagination();
            
            if (data.data.total === 0) {
                showToast('未找到符合条件的门店', 'info');
            } else {
                showToast(`找到 ${data.data.total} 家门店`, 'success');
            }
        } else {
            showToast('搜索失败: ' + data.error, 'error');
            showEmptyResults();
        }
    } catch (error) {
        console.error('搜索失败:', error);
        showToast('搜索失败，请重试', 'error');
        showEmptyResults();
    } finally {
        isLoading = false;
    }
}

/**
 * 渲染门店列表
 */
function renderStores(stores) {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = '';
    
    if (stores.length === 0) {
        showEmptyResults();
        return;
    }
    
    stores.forEach(store => {
        const card = createStoreCard(store);
        container.appendChild(card);
    });
    
    // 显示分页控制
    document.getElementById('paginationContainer').style.display = 'flex';
}

/**
 * 创建门店卡片
 */
function createStoreCard(store) {
    const card = document.createElement('div');
    card.className = 'store-card';
    card.dataset.storeId = store.store_id;
    
    const currentRating = store.current_rating || '';
    
    card.innerHTML = `
        <div class="store-header">
            <div class="store-name">${escapeHtml(store.store_name)}</div>
            <div class="store-meta">
                <div class="meta-item">
                    <span class="meta-label">ID:</span>
                    <span>${escapeHtml(store.store_id)}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">城市:</span>
                    <span>${escapeHtml(store.city || '-')}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">战区:</span>
                    <span>${escapeHtml(store.war_zone || '-')}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">区域经理:</span>
                    <span>${escapeHtml(store.regional_manager || '-')}</span>
                </div>
            </div>
        </div>
        <div class="store-body">
            <div class="revenue-display">
                <div class="revenue-label">1月堂食营业额</div>
                <div class="revenue-value">${escapeHtml(store.dine_in_revenue || '-')}</div>
            </div>
            <div class="rating-buttons">
                <button class="rating-btn rating-a ${currentRating === 'A' ? 'selected' : ''}" data-rating="A">A</button>
                <button class="rating-btn rating-b ${currentRating === 'B' ? 'selected' : ''}" data-rating="B">B</button>
                <button class="rating-btn rating-c ${currentRating === 'C' ? 'selected' : ''}" data-rating="C">C</button>
            </div>
        </div>
    `;
    
    // 绑定评级按钮事件
    const ratingButtons = card.querySelectorAll('.rating-btn');
    ratingButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            handleRating(store.store_id, this.dataset.rating, card);
        });
    });
    
    return card;
}

/**
 * 处理评级点击
 */
async function handleRating(storeId, rating, cardElement) {
    try {
        // 发送评级请求
        const response = await fetch(`${API_BASE_PATH}/api/rating/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                store_id: storeId,
                rating: rating
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 更新按钮状态
            const buttons = cardElement.querySelectorAll('.rating-btn');
            buttons.forEach(btn => {
                btn.classList.remove('selected');
                if (btn.dataset.rating === rating) {
                    btn.classList.add('selected');
                }
            });
            
            showToast(`✓ 评级已保存: ${rating}`, 'success');
            
            // 检查当前页是否全部完成
            if (isPageComplete()) {
                showConfirmDialog();
            }
        } else {
            showToast('✗ 评级保存失败: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('评级保存失败:', error);
        showToast('✗ 评级保存失败', 'error');
    }
}

/**
 * 检查当前页是否全部完成
 */
function isPageComplete() {
    const cards = document.querySelectorAll('.store-card');
    for (let card of cards) {
        const selectedBtn = card.querySelector('.rating-btn.selected');
        if (!selectedBtn) {
            return false;
        }
    }
    return true;
}

/**
 * 显示确认对话框
 */
function showConfirmDialog() {
    document.getElementById('confirmDialog').style.display = 'flex';
}

/**
 * 隐藏确认对话框
 */
function hideConfirmDialog() {
    document.getElementById('confirmDialog').style.display = 'none';
}

/**
 * 更新分页控制
 */
function updatePagination() {
    document.getElementById('pageInfo').textContent = `${currentPage} / ${totalPages}`;
    document.getElementById('prevPageBtn').disabled = currentPage <= 1;
    document.getElementById('nextPageBtn').disabled = currentPage >= totalPages;
}

/**
 * 上一页
 */
async function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        await loadStores();
    }
}

/**
 * 下一页
 */
async function nextPage() {
    if (currentPage < totalPages) {
        currentPage++;
        await loadStores();
    }
}

/**
 * 清除筛选条件
 */
function clearFilters() {
    // 重置所有筛选条件
    currentFilters = {
        war_zone: '',
        regional_manager: ''
    };
    
    // 重置分页
    currentPage = 1;
    totalPages = 1;
    
    // 重置下拉菜单
    document.getElementById('warZoneFilter').value = '';
    document.getElementById('regionalManagerFilter').value = '';
    
    // 清空区域经理选项
    populateSelect('regionalManagerFilter', []);
    
    // 显示首页统计
    loadCompletionStats();
    
    // 隐藏分页控制
    document.getElementById('paginationContainer').style.display = 'none';
    
    showToast('已清除所有筛选条件', 'info');
}

/**
 * 加载完成率统计
 */
async function loadCompletionStats() {
    try {
        // 构建查询参数
        const params = new URLSearchParams();
        if (currentFilters.war_zone) params.append('war_zone', currentFilters.war_zone);
        if (currentFilters.regional_manager) params.append('regional_manager', currentFilters.regional_manager);
        
        const response = await fetch(`${API_BASE_PATH}/api/rating/completion-stats?${params.toString()}`);
        const data = await response.json();
        
        if (data.success) {
            renderCompletionStats(data.data.stats);
        }
    } catch (error) {
        console.error('加载完成率统计失败:', error);
    }
}

/**
 * 渲染完成率统计
 */
function renderCompletionStats(stats) {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = '';
    
    // 创建统计标题
    const title = document.createElement('div');
    title.className = 'stats-title';
    title.innerHTML = '<h2>📊 各战区评级完成率</h2>';
    container.appendChild(title);
    
    // 创建统计列表
    const statsList = document.createElement('div');
    statsList.className = 'stats-list';
    
    stats.forEach(stat => {
        const statCard = document.createElement('div');
        statCard.className = 'stat-card';
        
        const completionRate = stat.completion_rate;
        const progressColor = completionRate >= 80 ? '#10b981' : 
                             completionRate >= 50 ? '#f59e0b' : '#ef4444';
        
        statCard.innerHTML = `
            <div class="stat-header">
                <span class="stat-zone">${escapeHtml(stat.war_zone)}</span>
                <span class="stat-rate" style="color: ${progressColor}">${completionRate}%</span>
            </div>
            <div class="stat-progress">
                <div class="stat-progress-bar" style="width: ${completionRate}%; background-color: ${progressColor}"></div>
            </div>
            <div class="stat-details">
                <span>已评级: ${stat.rated_stores} / ${stat.total_stores}</span>
            </div>
        `;
        
        statsList.appendChild(statCard);
    });
    
    container.appendChild(statsList);
    
    // 隐藏分页控制
    document.getElementById('paginationContainer').style.display = 'none';
}

/**
 * 导出评级结果
 */
async function exportRatings() {
    try {
        showToast('正在导出...', 'info');
        
        // 直接打开下载链接
        window.location.href = `${API_BASE_PATH}/api/rating/export`;
        
        setTimeout(() => {
            showToast('✓ 导出成功', 'success');
        }, 1000);
    } catch (error) {
        console.error('导出失败:', error);
        showToast('✗ 导出失败', 'error');
    }
}

/**
 * 显示加载状态
 */
function showLoading() {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>正在加载门店列表...</p>
        </div>
    `;
}

/**
 * 显示空结果提示
 */
function showEmptyResults() {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = `
        <div class="empty-results">
            <div class="empty-results-icon">🔍</div>
            <h3>未找到符合条件的门店</h3>
            <p>请尝试调整筛选条件后重新搜索</p>
        </div>
    `;
}

/**
 * 显示提示消息
 */
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

/**
 * HTML转义函数，防止XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
