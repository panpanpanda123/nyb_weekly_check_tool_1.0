// 审核结果展示系统前端逻辑

// API 基础路径配置（根据部署路径调整）
// 子域名weeklycheck.blitzepanda.top直接代理到根路径，不需要前缀
const API_BASE_PATH = '';

// 全局状态
let filterOptions = {
    war_zones: [],
    provinces: [],
    cities: [],
    regional_managers: [],
    operators: [],
    review_results: []
};

let currentFilters = {
    war_zone: '',
    province: '',
    city: '',
    regional_manager: '',
    operator: '',
    review_result: '',
    store_search: ''
};

let searchResults = [];
let currentPage = 1;
let totalPages = 1;
let isLoading = false;
let processedStores = new Set();  // 记录已处理的门店ID
let currentView = 'pending';  // 当前视图：pending 或 completed

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 页面加载开始...');
    
    // 绑定功能选项卡切换
    bindFunctionTabs();
    
    // 加载已处理的项目记录
    loadProcessedItems();
    
    // 加载筛选选项
    await loadFilterOptions();
    
    // 绑定事件
    bindEvents();
    
    console.log('✅ 页面初始化完成');
});

/**
 * 绑定功能选项卡切换
 */
function bindFunctionTabs() {
    const reviewTab = document.getElementById('reviewTab');
    const ratingTab = document.getElementById('ratingTab');
    
    if (reviewTab) {
        reviewTab.addEventListener('click', function() {
            // 当前已在周清审核页面，无需操作
        });
    }
    
    if (ratingTab) {
        ratingTab.addEventListener('click', function() {
            window.location.href = '/rating';
        });
    }
    
    const equipmentTab = document.getElementById('equipmentTab');
    if (equipmentTab) {
        equipmentTab.addEventListener('click', function() {
            window.location.href = '/equipment';
        });
    }
}

// 监听浏览器返回按钮，用于关闭图片模态框
window.addEventListener('popstate', function(event) {
    const modal = document.getElementById('imageModal');
    if (modal && modal.classList.contains('show')) {
        // 如果模态框是打开的，关闭它（不触发history.back()）
        modal.classList.remove('show');
        document.body.style.overflow = 'auto';
    }
});

/**
 * 加载筛选选项
 */
async function loadFilterOptions() {
    try {
        showToast('正在加载筛选选项...', 'info');
        
        const response = await fetch(`${API_BASE_PATH}/api/filters`);
        const data = await response.json();
        
        if (data.success) {
            filterOptions = data.data;
            
            // 填充战区下拉菜单
            populateSelect('warZoneFilter', filterOptions.war_zones);
            
            // 填充区域经理下拉菜单
            populateSelect('regionalManagerFilter', filterOptions.regional_managers);
            
            // 填充运营下拉菜单
            populateSelect('operatorFilter', filterOptions.operators);
            
            console.log('✅ 筛选选项加载完成');
        } else {
            showToast('加载筛选选项失败: ' + data.error, 'error');
        }
        
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
    // 门店搜索框
    const storeSearchInput = document.getElementById('storeSearch');
    const storeSearchBtn = document.getElementById('storeSearchBtn');
    const clearStoreSearchBtn = document.getElementById('clearStoreSearchBtn');
    
    // 门店搜索按钮
    storeSearchBtn.addEventListener('click', performStoreSearch);
    
    // 回车键触发搜索
    storeSearchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performStoreSearch();
        }
    });
    
    // 输入框变化时显示/隐藏清除按钮
    storeSearchInput.addEventListener('input', function(e) {
        if (e.target.value.trim()) {
            clearStoreSearchBtn.style.display = 'inline-block';
        } else {
            clearStoreSearchBtn.style.display = 'none';
        }
    });
    
    // 清除门店搜索
    clearStoreSearchBtn.addEventListener('click', function() {
        storeSearchInput.value = '';
        clearStoreSearchBtn.style.display = 'none';
        showWelcomeMessage();
        updateResultCount(0);
        showToast('已清除搜索', 'info');
    });
    
    // 战区选择变化 - 级联更新省份
    document.getElementById('warZoneFilter').addEventListener('change', async function(e) {
        const warZone = e.target.value;
        currentFilters.war_zone = warZone;
        
        // 清空省份和城市
        currentFilters.province = '';
        currentFilters.city = '';
        document.getElementById('provinceFilter').value = '';
        document.getElementById('cityFilter').value = '';
        
        if (warZone) {
            // 启用省份下拉菜单并加载省份列表
            await loadProvinces(warZone);
            document.getElementById('provinceFilter').disabled = false;
        } else {
            // 禁用省份和城市下拉菜单
            document.getElementById('provinceFilter').disabled = true;
            document.getElementById('cityFilter').disabled = true;
            populateSelect('provinceFilter', []);
            populateSelect('cityFilter', []);
        }
    });
    
    // 省份选择变化 - 级联更新城市
    document.getElementById('provinceFilter').addEventListener('change', async function(e) {
        const province = e.target.value;
        currentFilters.province = province;
        
        // 清空城市
        currentFilters.city = '';
        document.getElementById('cityFilter').value = '';
        
        if (province) {
            // 启用城市下拉菜单并加载城市列表
            await loadCities(province);
            document.getElementById('cityFilter').disabled = false;
        } else {
            // 禁用城市下拉菜单
            document.getElementById('cityFilter').disabled = true;
            populateSelect('cityFilter', []);
        }
    });
    
    // 城市选择变化
    document.getElementById('cityFilter').addEventListener('change', function(e) {
        currentFilters.city = e.target.value;
    });
    
    // 区域经理选择变化
    document.getElementById('regionalManagerFilter').addEventListener('change', function(e) {
        currentFilters.regional_manager = e.target.value;
    });
    
    // 运营选择变化
    document.getElementById('operatorFilter').addEventListener('change', function(e) {
        currentFilters.operator = e.target.value;
    });
    
    // 搜索按钮
    document.getElementById('searchBtn').addEventListener('click', performSearch);
    
    // 清除筛选按钮
    document.getElementById('clearBtn').addEventListener('click', clearFilters);
    
    // ESC键关闭模态框
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeImageModal();
        }
    });
    
    // 清除已完成记录
    document.getElementById('clearProcessedBtn').addEventListener('click', function() {
        if (confirm('确定要清除所有已完成记录吗？')) {
            clearProcessedItems();
            if (searchResults.length > 0) {
                renderResults(searchResults);
            }
        }
    });
}

/**
 * 根据战区加载省份列表
 */
async function loadProvinces(warZone) {
    try {
        const response = await fetch(`${API_BASE_PATH}/api/filters/provinces?war_zone=${encodeURIComponent(warZone)}`);
        const data = await response.json();
        
        if (data.success) {
            populateSelect('provinceFilter', data.data.provinces);
        } else {
            showToast('加载省份列表失败: ' + data.error, 'error');
        }
        
    } catch (error) {
        console.error('加载省份列表失败:', error);
        showToast('加载省份列表失败', 'error');
    }
}

/**
 * 根据省份加载城市列表
 */
async function loadCities(province) {
    try {
        const response = await fetch(`${API_BASE_PATH}/api/filters/cities?province=${encodeURIComponent(province)}`);
        const data = await response.json();
        
        if (data.success) {
            populateSelect('cityFilter', data.data.cities);
        } else {
            showToast('加载城市列表失败: ' + data.error, 'error');
        }
        
    } catch (error) {
        console.error('加载城市列表失败:', error);
        showToast('加载城市列表失败', 'error');
    }
}

/**
 * 执行门店搜索（精确匹配门店编号或模糊匹配门店名称）
 */
async function performStoreSearch() {
    try {
        const searchInput = document.getElementById('storeSearch');
        const searchValue = searchInput.value.trim();
        
        if (!searchValue) {
            showToast('请输入门店编号或门店名称', 'warning');
            return;
        }
        
        // 重置分页
        currentPage = 1;
        currentFilters.store_search = searchValue;
        
        // 执行搜索
        await loadSearchResults();
        
    } catch (error) {
        console.error('搜索失败:', error);
        showToast('搜索失败，请重试', 'error');
        showEmptyResults();
    }
}

/**
 * 加载搜索结果（支持分页）
 */
async function loadSearchResults() {
    if (isLoading) return;
    
    try {
        isLoading = true;
        
        // 显示加载状态
        if (currentPage === 1) {
            showLoading();
        }
        
        // 构建查询参数
        const params = new URLSearchParams();
        if (currentFilters.war_zone) params.append('war_zone', currentFilters.war_zone);
        if (currentFilters.province) params.append('province', currentFilters.province);
        if (currentFilters.city) params.append('city', currentFilters.city);
        if (currentFilters.regional_manager) params.append('regional_manager', currentFilters.regional_manager);
        if (currentFilters.operator) params.append('operator', currentFilters.operator);
        if (currentFilters.store_search) params.append('store_search', currentFilters.store_search);
        params.append('page', currentPage);
        params.append('per_page', 20);  // 每页20个门店
        
        const response = await fetch(`${API_BASE_PATH}/api/search?${params.toString()}`);
        const data = await response.json();
        
        if (data.success) {
            const stores = data.data.stores;
            totalPages = data.data.total_pages;
            
            if (currentPage === 1) {
                searchResults = stores;
                renderResults(searchResults);
            } else {
                searchResults = searchResults.concat(stores);
                appendResults(stores);
            }
            
            updateResultCount(data.data.total_stores);
            
            if (data.data.total_stores === 0) {
                showToast('未找到不合格门店', 'info');
            } else if (currentPage === 1) {
                showToast(`找到 ${data.data.total_stores} 个不合格门店`, 'success');
            }
        } else {
            showToast('搜索失败: ' + data.error, 'error');
            if (currentPage === 1) {
                showEmptyResults();
            }
        }
        
    } catch (error) {
        console.error('搜索失败:', error);
        showToast('搜索失败，请重试', 'error');
        if (currentPage === 1) {
            showEmptyResults();
        }
    } finally {
        isLoading = false;
    }
    
    // 延迟更新分页按钮，确保 renderResults 完成后再更新
    setTimeout(() => {
        const paginationContainer = document.getElementById('loadMoreContainer');
        if (paginationContainer && currentPage < totalPages) {
            console.log('显示分页按钮，currentPage:', currentPage, 'totalPages:', totalPages);
            showPaginationButton();
        } else if (paginationContainer && currentPage >= totalPages) {
            console.log('隐藏分页按钮，已是最后一页');
            hidePaginationButton();
        }
    }, 50);
}

/**
 * 加载更多结果
 */
async function loadMore() {
    if (currentPage < totalPages) {
        currentPage++;
        await loadSearchResults();
    }
}

/**
 * 执行搜索
 */
async function performSearch() {
    // 重置分页
    currentPage = 1;
    currentFilters.store_search = '';  // 清除门店搜索
    
    // 执行搜索
    await loadSearchResults();
}

/**
 * 清除筛选条件
 */
function clearFilters() {
    // 重置所有筛选条件
    currentFilters = {
        war_zone: '',
        province: '',
        city: '',
        regional_manager: '',
        operator: '',
        review_result: '',
        store_search: ''
    };
    
    // 重置分页
    currentPage = 1;
    totalPages = 1;
    
    // 重置下拉菜单
    document.getElementById('warZoneFilter').value = '';
    document.getElementById('provinceFilter').value = '';
    document.getElementById('cityFilter').value = '';
    document.getElementById('regionalManagerFilter').value = '';
    document.getElementById('operatorFilter').value = '';
    
    // 清除门店搜索
    const storeSearchInput = document.getElementById('storeSearch');
    if (storeSearchInput) {
        storeSearchInput.value = '';
        const clearBtn = document.getElementById('clearStoreSearchBtn');
        if (clearBtn) clearBtn.style.display = 'none';
    }
    
    // 禁用省份和城市下拉菜单
    document.getElementById('provinceFilter').disabled = true;
    document.getElementById('cityFilter').disabled = true;
    
    // 清空省份和城市选项
    populateSelect('provinceFilter', []);
    populateSelect('cityFilter', []);
    
    // 显示欢迎消息
    showWelcomeMessage();
    updateResultCount(0, 0);
    hidePaginationButton();
    
    showToast('已清除所有筛选条件', 'info');
}

/**
 * 切换视图
 */
function switchView(view) {
    currentView = view;
    
    // 更新标签样式
    document.getElementById('pendingTab').classList.toggle('active', view === 'pending');
    document.getElementById('completedTab').classList.toggle('active', view === 'completed');
    
    if (view === 'pending') {
        // 显示待处理视图
        if (searchResults.length > 0) {
            renderResults(searchResults);
        } else {
            showWelcomeMessage();
        }
    } else {
        // 显示已完成视图
        renderCompletedView();
    }
}

/**
 * 渲染已完成视图
 */
function renderCompletedView() {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = '';
    
    // 获取所有已完成的项目（从所有搜索结果中筛选，不只是当前页）
    const completedResults = searchResults.filter(r => processedItems.has(r.id));
    
    if (completedResults.length === 0) {
        container.innerHTML = `
            <div class="empty-results">
                <div class="empty-results-icon">📋</div>
                <h3>暂无已完成项目</h3>
                <p>标记为"已处理"的项目会显示在这里</p>
            </div>
        `;
        return;
    }
    
    // 显示统计信息
    const statsDiv = document.createElement('div');
    statsDiv.className = 'completed-stats';
    statsDiv.innerHTML = `
        <div class="stats-info">
            📊 已完成项目：${completedResults.length} 条
        </div>
    `;
    container.appendChild(statsDiv);
    
    completedResults.forEach(result => {
        const card = createCompletedCard(result);
        container.appendChild(card);
    });
}

/**
 * 创建已完成卡片（不显示"已处理"按钮）
 */
function createCompletedCard(result) {
    const card = document.createElement('div');
    card.className = 'result-card completed-card';
    card.dataset.resultId = result.id;
    
    const imageUrl = result.image_url || '';
    const reviewResult = result.review_result || '';
    const problemNote = result.problem_note || '';
    
    card.innerHTML = `
        <div class="card-header">
            <div class="store-info">
                <div class="store-name">${escapeHtml(result.store_name)}</div>
                <div class="store-details">
                    <span>门店编号: ${escapeHtml(result.store_id)}</span>
                    <span>|</span>
                    <span>战区: ${escapeHtml(result.war_zone || '-')}</span>
                    <span>|</span>
                    <span>省份: ${escapeHtml(result.province || '-')}</span>
                    <span>|</span>
                    <span>城市: ${escapeHtml(result.city || '-')}</span>
                </div>
            </div>
            <div class="item-name">📋 ${escapeHtml(result.item_name)}</div>
        </div>
        <div class="card-body">
            <div class="image-container clickable-image">
                ${imageUrl ? 
                    `<img alt="${escapeHtml(result.item_name)}" loading="lazy" referrerpolicy="no-referrer" data-retry="0">
                     <div class="image-loading">⏳ 加载中...</div>` :
                    '<div class="image-placeholder">📷 暂无图片</div>'
                }
            </div>
            <div class="review-status ${reviewResult === '合格' ? 'pass' : 'fail'}">
                <span class="status-icon">${reviewResult === '合格' ? '✓' : '✗'}</span>
                <span class="status-text">${reviewResult === '合格' ? '合格' : '不合格'} (已完成)</span>
                <div class="action-buttons">
                    ${reviewResult === '不合格' ? `
                        <button class="copy-btn" title="一键复制问题信息">
                            📋 复制
                        </button>
                    ` : ''}
                    <button class="restore-btn" title="恢复到待处理">
                        ↩️ 恢复
                    </button>
                </div>
            </div>
            ${reviewResult === '不合格' && problemNote ? `
                <div class="problem-note">
                    <div class="problem-label">❗ 问题描述:</div>
                    <div class="problem-text">${escapeHtml(problemNote)}</div>
                </div>
            ` : ''}
        </div>
    `;
    
    // 设置图片
    if (imageUrl) {
        const imageContainer = card.querySelector('.image-container');
        const img = imageContainer.querySelector('img');
        const loadingDiv = imageContainer.querySelector('.image-loading');
        
        if (img) {
            // 设置 crossOrigin 以支持 Canvas 处理（用于复制功能）
            img.crossOrigin = 'anonymous';
            
            img.onload = function() {
                if (loadingDiv) loadingDiv.style.display = 'none';
            };
            
            img.onerror = function() {
                handleImageErrorWithRetry(this, imageUrl, loadingDiv);
            };
            
            img.src = imageUrl;
        }
        
        imageContainer.onclick = function() {
            openImageModal(imageUrl, result.store_name + ' - ' + result.item_name);
        };
    }
    
    // 绑定复制按钮
    const copyBtn = card.querySelector('.copy-btn');
    if (copyBtn) {
        copyBtn.onclick = function(e) {
            e.stopPropagation();
            copyProblemInfo(result);
        };
    }
    
    // 绑定恢复按钮
    const restoreBtn = card.querySelector('.restore-btn');
    if (restoreBtn) {
        restoreBtn.onclick = function(e) {
            e.stopPropagation();
            restoreItem(result.id, card);
        };
    }
    
    return card;
}

/**
 * 恢复项目到待处理
 */
function restoreItem(resultId, cardElement) {
    try {
        // 从已处理列表移除
        processedItems.delete(resultId);
        
        // 保存到localStorage
        localStorage.setItem('processedItems', JSON.stringify([...processedItems]));
        
        // 添加淡出动画
        cardElement.style.transition = 'opacity 0.3s, transform 0.3s';
        cardElement.style.opacity = '0';
        cardElement.style.transform = 'scale(0.9)';
        
        setTimeout(() => {
            cardElement.remove();
            showToast('✓ 已恢复到待处理', 'success');
            
            // 如果已完成列表为空，显示提示
            const remainingCards = document.querySelectorAll('.completed-card').length;
            if (remainingCards === 0) {
                renderCompletedView();
            }
        }, 300);
        
    } catch (error) {
        console.error('恢复失败:', error);
        showToast('✗ 恢复失败', 'error');
    }
}

/**
 * 渲染搜索结果（门店卡片）
 */
function renderResults(stores) {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = '';
    
    const unprocessedStores = currentView === 'pending' 
        ? stores.filter(s => !processedStores.has(s.store_id))
        : stores;
    
    const loadMoreContainer = document.createElement('div');
    loadMoreContainer.id = 'loadMoreContainer';
    loadMoreContainer.style.gridColumn = '1 / -1';
    loadMoreContainer.style.textAlign = 'center';
    loadMoreContainer.style.padding = '20px';
    
    if (unprocessedStores.length === 0) {
        if (currentView === 'pending') {
            container.innerHTML = `
                <div class="empty-results">
                    <div class="empty-results-icon">🎉</div>
                    <h3>当前页的门店已全部处理完成</h3>
                    <p>点击"下一页"继续查看更多门店</p>
                </div>
            `;
            container.appendChild(loadMoreContainer);
        } else {
            showEmptyResults();
        }
        return;
    }
    
    unprocessedStores.forEach(store => {
        const card = createStoreCard(store);
        container.appendChild(card);
    });
    
    container.appendChild(loadMoreContainer);
}

/**
 * 追加搜索结果
 */
function appendResults(stores) {
    const container = document.getElementById('resultsContainer');
    const loadMoreContainer = document.getElementById('loadMoreContainer');
    
    const unprocessedStores = currentView === 'pending'
        ? stores.filter(s => !processedStores.has(s.store_id))
        : stores;
    
    unprocessedStores.forEach(store => {
        const card = createStoreCard(store);
        if (loadMoreContainer) {
            container.insertBefore(card, loadMoreContainer);
        } else {
            container.appendChild(card);
        }
    });
}

/**
 * 创建门店卡片
 */
function createStoreCard(store) {
    const card = document.createElement('div');
    card.className = 'store-card';
    card.dataset.storeId = store.store_id;
    
    const itemCount = store.items.length;
    
    card.innerHTML = `
        <div class="store-card-header">
            <div class="store-info">
                <div class="store-name">${escapeHtml(store.store_name)}</div>
                <div class="store-details">
                    <span>门店编号: ${escapeHtml(store.store_id)}</span>
                    <span>|</span>
                    <span>${escapeHtml(store.war_zone || '-')} / ${escapeHtml(store.province || '-')} / ${escapeHtml(store.city || '-')}</span>
                </div>
            </div>
            <div class="store-badge">
                <span class="badge-count">${itemCount}</span>
                <span class="badge-label">个不合格项</span>
            </div>
        </div>
        <div class="store-card-actions">
            <button class="btn-view-details">📋 查看详情</button>
            <button class="btn-mark-done">✓ 标记已处理</button>
        </div>
        <div class="store-details-panel" style="display:none;"></div>
    `;
    
    // 查看详情按钮
    card.querySelector('.btn-view-details').onclick = function() {
        toggleStoreDetails(card, store);
    };
    
    // 标记已处理按钮
    card.querySelector('.btn-mark-done').onclick = function() {
        markStoreAsProcessed(store.store_id, card);
    };
    
    return card;
}

/**
 * 切换门店详情显示
 */
function toggleStoreDetails(card, store) {
    const panel = card.querySelector('.store-details-panel');
    const btn = card.querySelector('.btn-view-details');
    
    if (panel.style.display === 'none') {
        // 显示详情
        panel.innerHTML = store.items.map(item => `
            <div class="item-detail">
                <div class="item-header">
                    <span class="item-name">📋 ${escapeHtml(item.item_name)}</span>
                    <button class="btn-copy-item">📋 复制</button>
                </div>
                ${item.image_url ? `
                    <div class="item-image">
                        <img alt="${escapeHtml(item.item_name)}" loading="lazy" referrerpolicy="no-referrer">
                    </div>
                ` : ''}
                ${item.problem_note ? `
                    <div class="item-problem">❗ ${escapeHtml(item.problem_note)}</div>
                ` : ''}
            </div>
        `).join('');
        
        // 设置图片src和事件
        panel.querySelectorAll('.item-detail').forEach((itemEl, index) => {
            const item = store.items[index];
            
            // 设置复制按钮事件
            const copyBtn = itemEl.querySelector('.btn-copy-item');
            if (copyBtn) {
                copyBtn.onclick = function(e) {
                    e.stopPropagation();
                    copyItemInfo(item);
                };
            }
            
            // 设置图片
            const img = itemEl.querySelector('img');
            if (img && item.image_url) {
                img.crossOrigin = 'anonymous';
                img.src = item.image_url;
                
                img.onerror = function() {
                    this.style.display = 'none';
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'image-error';
                    errorDiv.textContent = '❌ 图片加载失败';
                    this.parentElement.appendChild(errorDiv);
                };
                
                // 点击图片打开模态框
                itemEl.querySelector('.item-image').onclick = function() {
                    openImageModal(item.image_url, store.store_name + ' - ' + item.item_name);
                };
            }
        });
        
        panel.style.display = 'block';
        btn.textContent = '🔼 收起详情';
    } else {
        // 隐藏详情
        panel.style.display = 'none';
        btn.textContent = '📋 查看详情';
    }
}

/**
 * 标记门店为已处理
 */
function markStoreAsProcessed(storeId, cardElement) {
    processedStores.add(storeId);
    localStorage.setItem('processedStores', JSON.stringify([...processedStores]));
    
    cardElement.style.transition = 'opacity 0.3s, transform 0.3s';
    cardElement.style.opacity = '0';
    cardElement.style.transform = 'scale(0.9)';
    
    setTimeout(() => {
        cardElement.remove();
        showToast('✓ 已标记为已处理', 'success');
        
        const remainingCards = document.querySelectorAll('.store-card').length;
        if (remainingCards === 0) {
            const container = document.getElementById('resultsContainer');
            const emptyDiv = document.createElement('div');
            emptyDiv.className = 'empty-results';
            emptyDiv.style.gridColumn = '1 / -1';
            emptyDiv.innerHTML = `
                <div class="empty-results-icon">🎉</div>
                <h3>当前页的门店已全部处理完成</h3>
                <p>点击"下一页"继续查看更多门店</p>
            `;
            const paginationContainer = document.getElementById('loadMoreContainer');
            if (paginationContainer) {
                container.insertBefore(emptyDiv, paginationContainer);
            } else {
                container.appendChild(emptyDiv);
            }
        }
    }, 300);
}

/**
 * 复制单个检查项信息
 */
function copyItemInfo(item) {
    const textContent = `【不合格项目】
门店编号：${item.store_id}
门店名称：${item.store_name}
检查项：${item.item_name}
问题描述：${item.problem_note || '无'}`;
    
    navigator.clipboard.writeText(textContent).then(() => {
        showToast('✓ 已复制', 'success');
    }).catch(() => {
        showToast('✗ 复制失败', 'error');
    });
}

/**
 * 显示分页按钮
 */
function showPaginationButton() {
    const container = document.getElementById('loadMoreContainer');
    console.log('显示分页按钮:', container, 'currentPage:', currentPage, 'totalPages:', totalPages);
    if (container) {
        container.innerHTML = `
            <div class="pagination-info">第 ${currentPage} / ${totalPages} 页</div>
            <button onclick="loadNextPage()" class="next-page-btn" ${isLoading ? 'disabled' : ''}>
                ${isLoading ? '⏳ 加载中...' : '下一页 →'}
            </button>
        `;
    } else {
        console.error('找不到分页容器！');
    }
}

/**
 * 隐藏分页按钮
 */
function hidePaginationButton() {
    const container = document.getElementById('loadMoreContainer');
    console.log('隐藏分页按钮:', container, 'currentPage:', currentPage, 'totalPages:', totalPages);
    if (container) {
        container.innerHTML = '<div class="no-more-results">✓ 已加载全部结果（第 ' + currentPage + ' / ' + totalPages + ' 页）</div>';
    }
}

/**
 * 加载下一页
 */
async function loadNextPage() {
    if (currentPage < totalPages && !isLoading) {
        currentPage++;
        await loadSearchResults();
    }
}

/**
 * 创建结果卡片
 */
function createResultCard(result) {
    const card = document.createElement('div');
    card.className = 'result-card';
    card.dataset.resultId = result.id;
    card.dataset.storeId = result.store_id;
    
    const imageUrl = result.image_url || '';
    const reviewResult = result.review_result || '';
    const problemNote = result.problem_note || '';
    
    card.innerHTML = `
        <div class="card-header">
            <div class="store-info">
                <div class="store-name">${escapeHtml(result.store_name)}</div>
                <div class="store-details">
                    <span>门店编号: ${escapeHtml(result.store_id)}</span>
                    <span>|</span>
                    <span>战区: ${escapeHtml(result.war_zone || '-')}</span>
                    <span>|</span>
                    <span>省份: ${escapeHtml(result.province || '-')}</span>
                    <span>|</span>
                    <span>城市: ${escapeHtml(result.city || '-')}</span>
                </div>
            </div>
            <div class="item-name">📋 ${escapeHtml(result.item_name)}</div>
        </div>
        <div class="card-body">
            <div class="image-container clickable-image">
                ${imageUrl ? 
                    `<img alt="${escapeHtml(result.item_name)}" loading="lazy" referrerpolicy="no-referrer" data-retry="0">
                     <div class="image-loading">⏳ 加载中...</div>` :
                    '<div class="image-placeholder">📷 暂无图片</div>'
                }
            </div>
            <div class="review-status ${reviewResult === '合格' ? 'pass' : 'fail'}">
                <span class="status-icon">${reviewResult === '合格' ? '✓' : '✗'}</span>
                <span class="status-text">${reviewResult === '合格' ? '合格' : '不合格'}</span>
                <div class="action-buttons">
                    ${reviewResult === '不合格' ? `
                        <button class="copy-btn" title="一键复制问题信息">
                            📋 复制
                        </button>
                    ` : ''}
                    <button class="mark-done-btn" title="标记已处理">
                        ✓ 已处理
                    </button>
                </div>
            </div>
            ${reviewResult === '不合格' && problemNote ? `
                <div class="problem-note">
                    <div class="problem-label">❗ 问题描述:</div>
                    <div class="problem-text">${escapeHtml(problemNote)}</div>
                </div>
            ` : ''}
        </div>
    `;
    
    // 使用JavaScript直接设置img的src属性，避免HTML转义问题
    if (imageUrl) {
        const imageContainer = card.querySelector('.image-container');
        const img = imageContainer.querySelector('img');
        const loadingDiv = imageContainer.querySelector('.image-loading');
        
        if (img) {
            // 设置 crossOrigin 以支持 Canvas 处理（用于复制功能）
            img.crossOrigin = 'anonymous';
            
            // 设置加载和错误处理
            img.onload = function() {
                if (loadingDiv) loadingDiv.style.display = 'none';
            };
            
            img.onerror = function() {
                handleImageErrorWithRetry(this, imageUrl, loadingDiv);
            };
            
            img.src = imageUrl;  // 直接设置src，图片从图床加载，不经过服务器
        }
        
        // 设置点击事件
        imageContainer.onclick = function() {
            openImageModal(imageUrl, result.store_name + ' - ' + result.item_name);
        };
    }
    
    // 绑定复制按钮事件
    const copyBtn = card.querySelector('.copy-btn');
    if (copyBtn) {
        copyBtn.onclick = function(e) {
            e.stopPropagation();
            copyProblemInfo(result);
        };
    }
    
    // 绑定已处理按钮事件
    const markDoneBtn = card.querySelector('.mark-done-btn');
    if (markDoneBtn) {
        markDoneBtn.onclick = function(e) {
            e.stopPropagation();
            markAsProcessed(result.id, card);
        };
    }
    
    return card;
}

/**
 * 处理图片加载错误（带重试机制）
 */
function handleImageErrorWithRetry(img, originalUrl, loadingDiv) {
    const container = img.parentElement;
    const retryCount = parseInt(img.dataset.retry || '0');
    const maxRetries = 3;
    
    if (retryCount < maxRetries) {
        // 重试加载
        img.dataset.retry = (retryCount + 1).toString();
        
        if (loadingDiv) {
            loadingDiv.textContent = `⏳ 重试中 (${retryCount + 1}/${maxRetries})...`;
            loadingDiv.style.display = 'block';
        }
        
        // 延迟重试，避免立即失败
        setTimeout(() => {
            img.src = originalUrl + '?retry=' + Date.now(); // 添加时间戳避免缓存
        }, 1000 * (retryCount + 1)); // 递增延迟：1秒、2秒、3秒
    } else {
        // 重试失败，显示错误信息
        if (loadingDiv) loadingDiv.style.display = 'none';
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'image-error';
        errorDiv.innerHTML = `
            ❌ 图片加载失败
            <br><small style="font-size:10px;">网络较慢或图片不存在</small>
            <br><button onclick="retryLoadImage(this, '${escapeHtml(originalUrl)}')" 
                        style="margin-top:5px;padding:5px 10px;cursor:pointer;border:none;background:#667eea;color:white;border-radius:4px;">
                🔄 重新加载
            </button>
        `;
        
        img.style.display = 'none';
        container.appendChild(errorDiv);
    }
}

/**
 * 手动重试加载图片
 */
function retryLoadImage(button, imageUrl) {
    const errorDiv = button.parentElement;
    const container = errorDiv.parentElement;
    const img = container.querySelector('img');
    
    if (img) {
        // 重置重试计数
        img.dataset.retry = '0';
        img.style.display = 'block';
        
        // 移除错误提示
        errorDiv.remove();
        
        // 显示加载提示
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'image-loading';
        loadingDiv.textContent = '⏳ 加载中...';
        container.appendChild(loadingDiv);
        
        // 重新加载图片
        img.src = imageUrl + '?retry=' + Date.now();
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
            <p>正在搜索审核结果...</p>
        </div>
    `;
}

/**
 * 显示欢迎消息
 */
function showWelcomeMessage() {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">👋</div>
            <h2>欢迎使用审核结果展示系统</h2>
            <p>请选择筛选条件并点击"搜索"按钮查看审核结果</p>
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
            <h3>未找到符合条件的审核结果</h3>
            <p>请尝试调整筛选条件后重新搜索</p>
        </div>
    `;
}

/**
 * 更新结果计数
 */
function updateResultCount(totalStores) {
    document.getElementById('resultCount').textContent = `不合格门店: ${totalStores}`;
}

/**
 * 处理图片加载错误（旧版本，保留兼容）
 */
function handleImageError(img) {
    const container = img.parentElement;
    container.innerHTML = '<div class="image-error">❌ 图片加载失败</div>';
}

/**
 * 打开图片模态框
 */
function openImageModal(imageSrc, caption) {
    if (!imageSrc || imageSrc === 'null' || imageSrc === 'undefined') {
        showToast('图片不可用', 'error');
        return;
    }
    
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    const modalCaption = document.getElementById('modalCaption');
    
    modal.classList.add('show');
    modalImg.src = imageSrc;
    modalCaption.textContent = caption;
    
    // 防止背景滚动
    document.body.style.overflow = 'hidden';
    
    // 添加历史记录状态，这样手机返回键可以关闭模态框
    history.pushState({ modalOpen: true }, '', '');
}

/**
 * 关闭图片模态框
 */
function closeImageModal() {
    const modal = document.getElementById('imageModal');
    modal.classList.remove('show');
    
    // 恢复背景滚动
    document.body.style.overflow = 'auto';
    
    // 如果当前历史状态是模态框打开状态，返回上一页
    if (history.state && history.state.modalOpen) {
        history.back();
    }
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
 * 标记为已处理
 */
async function markAsProcessed(resultId, cardElement) {
    try {
        // 添加到已处理列表
        processedItems.add(resultId);
        
        // 保存到localStorage
        localStorage.setItem('processedItems', JSON.stringify([...processedItems]));
        
        // 添加淡出动画
        cardElement.style.transition = 'opacity 0.3s, transform 0.3s';
        cardElement.style.opacity = '0';
        cardElement.style.transform = 'scale(0.9)';
        
        // 等待动画完成后移除卡片
        setTimeout(() => {
            cardElement.remove();
            
            // 检查当前页是否还有卡片
            const remainingCards = document.querySelectorAll('.result-card').length;
            
            if (remainingCards === 0) {
                // 当前页没有卡片了，显示提示
                const container = document.getElementById('resultsContainer');
                const emptyDiv = document.createElement('div');
                emptyDiv.className = 'empty-results';
                emptyDiv.style.gridColumn = '1 / -1';
                emptyDiv.innerHTML = `
                    <div class="empty-results-icon">🎉</div>
                    <h3>当前页的项目已全部处理完成</h3>
                    <p>点击"下一页"继续查看更多项目</p>
                `;
                
                // 在分页容器之前插入
                const paginationContainer = document.getElementById('loadMoreContainer');
                if (paginationContainer) {
                    container.insertBefore(emptyDiv, paginationContainer);
                } else {
                    container.appendChild(emptyDiv);
                }
                
                showToast('✓ 当前页已全部处理完成', 'success');
            } else {
                showToast('✓ 已标记为已处理', 'success');
            }
        }, 300);
        
    } catch (error) {
        console.error('标记失败:', error);
        showToast('✗ 标记失败', 'error');
    }
}

/**
 * 从localStorage加载已处理的门店
 */
function loadProcessedItems() {
    try {
        const saved = localStorage.getItem('processedStores');
        if (saved) {
            processedStores = new Set(JSON.parse(saved));
        }
    } catch (error) {
        console.error('加载已处理门店失败:', error);
        processedStores = new Set();
    }
}

/**
 * 清除已处理记录
 */
function clearProcessedItems() {
    processedStores.clear();
    localStorage.removeItem('processedStores');
    showToast('✓ 已清除所有已处理记录', 'info');
}

/**
 * 复制问题信息（图片+门店信息+问题描述）
 * 优化版：支持复制页面已加载的缩略图
 * 兼容 HTTP 和 HTTPS 环境
 */
async function copyProblemInfo(result) {
    try {
        const imageUrl = result.image_url || '';
        const storeId = result.store_id || '';
        const storeName = result.store_name || '';
        const itemName = result.item_name || '';
        const problemNote = result.problem_note || '';
        
        // 构建文本内容
        const textContent = `【不合格项目】
门店编号：${storeId}
门店名称：${storeName}
检查项：${itemName}
问题描述：${problemNote}`;
        
        // 检查是否在安全上下文（HTTPS 或 localhost）
        const isSecureContext = window.isSecureContext;
        
        // 检查浏览器是否支持 Clipboard API
        if (!isSecureContext || !navigator.clipboard || !window.ClipboardItem) {
            // HTTP 环境或旧版浏览器：只复制文本
            copyTextFallback(textContent, !isSecureContext);
            return;
        }
        
        // 如果没有图片，只复制文本
        if (!imageUrl) {
            await navigator.clipboard.writeText(textContent);
            showToast('✓ 已复制文字信息（无图片）', 'success');
            return;
        }
        
        // 尝试复制图片
        showToast('⏳ 正在处理图片...', 'info');
        
        // 方案1：从页面上已加载的 img 元素获取图片
        const imgElement = findImageElement(result.id);
        if (imgElement && imgElement.complete && imgElement.naturalHeight > 0) {
            const blob = await convertImageToBlob(imgElement);
            if (blob) {
                await copyImageAndText(blob, textContent);
                return;
            }
        }
        
        // 方案2：尝试通过 fetch 获取（可能遇到 CORS）
        try {
            const response = await fetch(imageUrl, {
                mode: 'cors',
                credentials: 'omit'
            });
            
            if (response.ok) {
                const blob = await response.blob();
                await copyImageAndText(blob, textContent);
                return;
            }
        } catch (fetchError) {
            console.warn('Fetch 失败，尝试 Canvas 方案:', fetchError);
        }
        
        // 方案3：使用 Canvas 绘制（绕过部分 CORS 限制）
        if (imgElement) {
            try {
                const blob = await convertImageToBlobViaCanvas(imgElement);
                if (blob) {
                    await copyImageAndText(blob, textContent);
                    return;
                }
            } catch (canvasError) {
                console.warn('Canvas 方案失败:', canvasError);
            }
        }
        
        // 所有方案都失败，降级为只复制文本
        await navigator.clipboard.writeText(textContent);
        showToast('⚠️ 图片复制失败（跨域限制），已复制文字信息', 'warning');
        
    } catch (error) {
        console.error('复制失败:', error);
        showToast('✗ 复制失败，请手动复制', 'error');
    }
}

/**
 * 查找对应的图片元素
 */
function findImageElement(resultId) {
    const card = document.querySelector(`[data-result-id="${resultId}"]`);
    if (card) {
        return card.querySelector('.image-container img');
    }
    return null;
}

/**
 * 将 img 元素转换为 Blob（使用 Canvas）
 */
async function convertImageToBlob(imgElement) {
    try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // 设置 canvas 尺寸为图片实际尺寸
        canvas.width = imgElement.naturalWidth;
        canvas.height = imgElement.naturalHeight;
        
        // 绘制图片
        ctx.drawImage(imgElement, 0, 0);
        
        // 转换为 Blob
        return new Promise((resolve) => {
            canvas.toBlob((blob) => {
                resolve(blob);
            }, 'image/png');
        });
    } catch (error) {
        console.error('转换图片失败:', error);
        return null;
    }
}

/**
 * 使用 Canvas 转换图片（处理跨域图片）
 */
async function convertImageToBlobViaCanvas(imgElement) {
    try {
        // 创建新的 Image 对象，设置 crossOrigin
        const img = new Image();
        img.crossOrigin = 'anonymous';
        
        return new Promise((resolve, reject) => {
            img.onload = () => {
                try {
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    
                    canvas.width = img.naturalWidth;
                    canvas.height = img.naturalHeight;
                    
                    ctx.drawImage(img, 0, 0);
                    
                    canvas.toBlob((blob) => {
                        resolve(blob);
                    }, 'image/png');
                } catch (err) {
                    reject(err);
                }
            };
            
            img.onerror = () => {
                reject(new Error('图片加载失败'));
            };
            
            img.src = imgElement.src;
        });
    } catch (error) {
        console.error('Canvas 转换失败:', error);
        return null;
    }
}

/**
 * 复制图片和文本到剪贴板
 */
async function copyImageAndText(imageBlob, textContent) {
    try {
        const clipboardItem = new ClipboardItem({
            'text/plain': new Blob([textContent], { type: 'text/plain' }),
            'image/png': imageBlob
        });
        
        await navigator.clipboard.write([clipboardItem]);
        showToast('✓ 已复制图片和文字，可直接粘贴发送', 'success');
    } catch (error) {
        console.error('写入剪贴板失败:', error);
        // 降级为只复制文本
        await navigator.clipboard.writeText(textContent);
        showToast('⚠️ 图片复制失败，已复制文字信息', 'warning');
    }
}

/**
 * 降级方案：只复制文本（旧版浏览器或 HTTP 环境）
 */
function copyTextFallback(textContent, isHttpEnv = false) {
    try {
        const textarea = document.createElement('textarea');
        textarea.value = textContent;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        
        if (isHttpEnv) {
            showToast('✓ 已复制文字信息（需要 HTTPS 才能复制图片）', 'success');
        } else {
            showToast('✓ 已复制文字信息（浏览器不支持图片复制）', 'success');
        }
    } catch (error) {
        console.error('降级复制失败:', error);
        showToast('✗ 复制失败，请手动复制', 'error');
    }
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
