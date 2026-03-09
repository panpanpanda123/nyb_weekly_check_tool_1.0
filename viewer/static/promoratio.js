// 活动参与度监控 JavaScript

const API_BASE_PATH = '';

// 全局状态
let currentPage = 1;
let totalPages = 1;
let filters = {
    war_zone: '',
    regional_manager: '',
    store_search: '',
    sort_by: 'participation_rate',
    sort_order: 'asc'  // 默认升序，低的在前
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 活动参与度监控页面加载开始...');
    initPromoPage();
});

// 初始化页面
async function initPromoPage() {
    try {
        await loadFilterOptions();
        setupEventListeners();
        console.log('✅ 活动参与度监控页面初始化完成');
    } catch (error) {
        console.error('❌ 页面初始化失败:', error);
        showToast('页面初始化失败，请刷新重试', 'error');
    }
}

// 加载筛选选项
async function loadFilterOptions() {
    try {
        const response = await fetch(`${API_BASE_PATH}/api/promo/filters`);
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            
            // 填充战区选项
            const warZoneSelect = document.getElementById('warZoneFilter');
            warZoneSelect.innerHTML = '<option value="">全部</option>';
            data.war_zones.forEach(wz => {
                warZoneSelect.innerHTML += `<option value="${wz}">${wz}</option>`;
            });
            
            // 显示数据日期
            if (data.data_date) {
                const dataTimeInfo = document.getElementById('dataTimeInfo');
                const dataDate = document.getElementById('dataDate');
                dataDate.textContent = data.data_date;
                dataTimeInfo.style.display = 'block';
            }
            
            // 加载所有区域经理（不依赖战区）
            await loadAllRegionalManagers();
            
            console.log('✅ 筛选选项加载完成');
        } else {
            throw new Error(result.error || '加载筛选选项失败');
        }
    } catch (error) {
        console.error('加载筛选选项失败:', error);
        throw error;
    }
}

// 加载所有区域经理
async function loadAllRegionalManagers() {
    try {
        const response = await fetch(`${API_BASE_PATH}/api/promo/all-regional-managers`);
        const result = await response.json();
        
        if (result.success) {
            const datalist = document.getElementById('regionalManagerList');
            
            // 保存所有区域经理到全局变量
            window.allRegionalManagers = result.data.regional_managers;
            
            // 填充datalist
            datalist.innerHTML = '';
            result.data.regional_managers.forEach(rm => {
                const option = document.createElement('option');
                option.value = rm;
                datalist.appendChild(option);
            });
            
            console.log(`✅ 加载了 ${result.data.regional_managers.length} 个区域经理`);
        }
    } catch (error) {
        console.error('加载所有区域经理失败:', error);
    }
}

// 根据战区加载区域经理
async function loadRegionalManagers(warZone) {
    try {
        const datalist = document.getElementById('regionalManagerList');
        
        if (!warZone) {
            // 没有战区，显示所有区域经理
            datalist.innerHTML = '';
            if (window.allRegionalManagers) {
                window.allRegionalManagers.forEach(rm => {
                    const option = document.createElement('option');
                    option.value = rm;
                    datalist.appendChild(option);
                });
            }
            return;
        }
        
        const response = await fetch(`${API_BASE_PATH}/api/promo/regional-managers?war_zone=${encodeURIComponent(warZone)}`);
        const result = await response.json();
        
        if (result.success) {
            datalist.innerHTML = '';
            result.data.regional_managers.forEach(rm => {
                const option = document.createElement('option');
                option.value = rm;
                datalist.appendChild(option);
            });
        } else {
            throw new Error(result.error || '加载区域经理失败');
        }
    } catch (error) {
        console.error('加载区域经理失败:', error);
        showToast('加载区域经理失败', 'error');
    }
}

// 设置事件监听
function setupEventListeners() {
    // 选项卡切换
    document.getElementById('reviewTab').addEventListener('click', () => {
        window.location.href = '/';
    });
    document.getElementById('ratingTab').addEventListener('click', () => {
        window.location.href = '/rating';
    });
    document.getElementById('equipmentTab').addEventListener('click', () => {
        window.location.href = '/equipment';
    });
    
    // 战区变化 - 动态加载该战区的区域经理
    document.getElementById('warZoneFilter').addEventListener('change', async (e) => {
        const warZone = e.target.value;
        filters.war_zone = warZone;
        
        const regionalManagerInput = document.getElementById('regionalManagerFilter');
        
        // 加载对应的区域经理列表
        await loadRegionalManagers(warZone);
        
        // 清空输入框（因为列表变了）
        regionalManagerInput.value = '';
        filters.regional_manager = '';
    });
    
    // 区域经理输入变化
    const regionalManagerInput = document.getElementById('regionalManagerFilter');
    regionalManagerInput.addEventListener('input', (e) => {
        filters.regional_manager = e.target.value.trim();
    });
    
    regionalManagerInput.addEventListener('change', (e) => {
        filters.regional_manager = e.target.value.trim();
    });
    
    // 门店搜索
    const storeSearchInput = document.getElementById('storeSearch');
    const storeSearchBtn = document.getElementById('storeSearchBtn');
    const clearStoreSearchBtn = document.getElementById('clearStoreSearchBtn');
    
    storeSearchBtn.addEventListener('click', () => {
        filters.store_search = storeSearchInput.value.trim();
        if (filters.store_search) {
            clearStoreSearchBtn.style.display = 'inline-block';
        }
        currentPage = 1;
        searchStores();
    });
    
    clearStoreSearchBtn.addEventListener('click', () => {
        storeSearchInput.value = '';
        filters.store_search = '';
        clearStoreSearchBtn.style.display = 'none';
        currentPage = 1;
        searchStores();
    });
    
    storeSearchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            storeSearchBtn.click();
        }
    });
    
    // 排序方式变化
    document.getElementById('sortByFilter').addEventListener('change', (e) => {
        filters.sort_by = e.target.value;
    });
    
    document.getElementById('sortOrderFilter').addEventListener('change', (e) => {
        filters.sort_order = e.target.value;
    });
    
    // 搜索按钮
    document.getElementById('searchBtn').addEventListener('click', () => {
        currentPage = 1;
        searchStores();
    });
    
    // 清除筛选按钮
    document.getElementById('clearBtn').addEventListener('click', () => {
        document.getElementById('warZoneFilter').value = '';
        document.getElementById('regionalManagerFilter').value = '';
        storeSearchInput.value = '';
        clearStoreSearchBtn.style.display = 'none';
        document.getElementById('sortByFilter').value = 'participation_rate';
        document.getElementById('sortOrderFilter').value = 'desc';
        
        filters = {
            war_zone: '',
            regional_manager: '',
            store_search: '',
            sort_by: 'participation_rate',
            sort_order: 'asc'  // 默认升序
        };
        currentPage = 1;
        
        // 恢复显示所有区域经理
        const datalist = document.getElementById('regionalManagerList');
        datalist.innerHTML = '';
        if (window.allRegionalManagers) {
            window.allRegionalManagers.forEach(rm => {
                const option = document.createElement('option');
                option.value = rm;
                datalist.appendChild(option);
            });
        }
        
        // 清空结果显示欢迎消息
        const container = document.getElementById('resultsContainer');
        container.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">📊</div>
                <h2>欢迎使用活动参与度监控系统</h2>
                <p>请选择筛选条件并点击"搜索"按钮查看活动参与度</p>
            </div>
        `;
        document.getElementById('paginationContainer').style.display = 'none';
        document.getElementById('resultCount').textContent = '门店总数: 0';
    });
    
    // 导出按钮
    document.getElementById('exportBtn').addEventListener('click', exportData);
    
    // 上一页
    document.getElementById('prevPage').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            searchStores();
        }
    });
    
    // 下一页
    document.getElementById('nextPage').addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            searchStores();
        }
    });
}

// 搜索门店
async function searchStores(page = 1) {
    currentPage = page;
    
    try {
        showLoading();
        
        // 构建查询参数
        const params = new URLSearchParams({
            page: currentPage,
            per_page: 20,
            ...filters
        });
        
        const response = await fetch(`${API_BASE_PATH}/api/promo/search?${params}`);
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            totalPages = data.total_pages;
            
            // 更新统计信息
            document.getElementById('resultCount').textContent = `门店总数: ${data.total}`;
            
            // 渲染门店列表
            renderStoreList(data.stores);
            
            // 更新分页
            if (data.total > 0) {
                document.getElementById('paginationContainer').style.display = 'flex';
                document.getElementById('prevPage').disabled = currentPage === 1;
                document.getElementById('nextPage').disabled = !data.has_more;
                document.getElementById('pageInfo').textContent = `第 ${currentPage} / ${totalPages} 页`;
            } else {
                document.getElementById('paginationContainer').style.display = 'none';
            }
            
        } else {
            throw new Error(result.error || '搜索失败');
        }
    } catch (error) {
        console.error('搜索失败:', error);
        showError('搜索失败，请重试');
    }
}

// 渲染门店列表
function renderStoreList(stores) {
    const container = document.getElementById('resultsContainer');
    
    if (!stores || stores.length === 0) {
        container.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">📭</div>
                <h2>暂无活动参与度数据</h2>
                <p>当前筛选条件下没有找到门店数据</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = stores.map(store => {
        // 将参与度转换为百分比格式
        const participationRate = parseFloat(store.participation_rate) || 0;
        const participationPercent = (participationRate * 100).toFixed(1);
        
        // 根据参与度设置颜色
        let rateColor = '#dc3545'; // 红色 - 低
        if (participationRate >= 0.8) {
            rateColor = '#28a745'; // 绿色 - 高
        } else if (participationRate >= 0.5) {
            rateColor = '#ffc107'; // 黄色 - 中
        }
        
        return `
            <div class="store-card-compact" data-store-id="${store.store_id}">
                <!-- 门店信息 -->
                <div class="store-info-compact">
                    <div class="store-name-mini">${escapeHtml(store.store_name)}</div>
                    <div class="store-meta-mini">
                        ${escapeHtml(store.store_id)} · ${escapeHtml(store.war_zone || '-')} · ${escapeHtml(store.regional_manager || '-')}
                    </div>
                </div>
                
                <!-- 数据指标 - 紧凑排列 -->
                <div class="metrics-compact">
                    <div class="metric-mini">
                        <span class="metric-value-mini">${store.order_count}</span>
                        <span class="metric-label-mini">订单</span>
                    </div>
                    <div class="metric-mini">
                        <span class="metric-value-mini">${store.benefit_card_sales}</span>
                        <span class="metric-label-mini">权益卡</span>
                    </div>
                    <div class="metric-mini">
                        <span class="metric-value-mini">${store.promo_package_sales}</span>
                        <span class="metric-label-mini">套餐</span>
                    </div>
                    <div class="metric-mini participation">
                        <span class="metric-value-mini" style="color: ${rateColor}; font-weight: 700;">${participationPercent}%</span>
                        <span class="metric-label-mini">参与度</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// 显示加载中
function showLoading() {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">⏳</div>
            <h2>加载中...</h2>
            <p>正在获取活动参与度数据</p>
        </div>
    `;
}

// 显示错误
function showError(message) {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">❌</div>
            <h2>加载失败</h2>
            <p>${escapeHtml(message)}</p>
        </div>
    `;
}

// 导出数据
async function exportData() {
    try {
        showToast('正在导出...', 'info');
        window.location.href = `${API_BASE_PATH}/api/promo/export`;
        setTimeout(() => {
            showToast('✓ 导出成功', 'success');
        }, 1000);
    } catch (error) {
        console.error('导出失败:', error);
        showToast('✗ 导出失败', 'error');
    }
}

// 显示提示消息
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// HTML转义函数，防止XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
