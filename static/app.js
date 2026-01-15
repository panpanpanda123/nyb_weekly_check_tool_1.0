// 门店检查项图片审核系统前端逻辑

// 全局状态
let allItems = [];
let reviews = {};
let currentOperator = '全部';
let displayedStores = new Set(); // 当前显示的门店
let completedStores = []; // 已完成的门店列表
let currentView = 'pending'; // 'pending' 或 'completed'
let searchMode = false; // 是否处于搜索模式
let searchKeyword = ''; // 搜索关键词
const ITEMS_PER_PAGE = 10;

// 键盘导航状态
let keyboardNavEnabled = true; // 是否启用键盘导航
let currentFocusIndex = 0; // 当前聚焦的卡片索引
let visibleCards = []; // 当前可见的卡片元素

document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 页面加载开始...');
    
    // 按顺序加载数据
    await loadOperators();
    console.log('✅ 运营人员列表加载完成');
    
    await loadItems();  // 先加载检查项数据
    console.log('✅ 检查项数据加载完成');
    
    await loadReviews();  // 再加载审核记录
    console.log('✅ 审核记录加载完成');
    
    console.log('🎉 所有数据加载完成！');
    
    // 运营人员筛选事件
    document.getElementById('operatorFilter').addEventListener('change', function(e) {
        currentOperator = e.target.value;
        displayedStores.clear();
        clearSearch(); // 切换运营人员时清除搜索
        loadItems();
        updateStatsPanel();
        updateAdminPanel();
    });
    
    // 视图切换
    document.getElementById('pendingTab').addEventListener('click', () => {
        clearSearch(); // 切换视图时清除搜索
        switchView('pending');
    });
    document.getElementById('completedTab').addEventListener('click', () => {
        clearSearch(); // 切换视图时清除搜索
        switchView('completed');
    });
    
    // 搜索功能
    document.getElementById('searchBtn').addEventListener('click', performSearch);
    document.getElementById('storeSearch').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    document.getElementById('clearSearchBtn').addEventListener('click', clearSearch);
    
    // 管理员按钮
    document.getElementById('exportBtn').addEventListener('click', exportCurrentData);
    document.getElementById('uploadFile').addEventListener('change', uploadNewFile);
    
    // 键盘导航
    setupKeyboardNavigation();
});

/**
 * 设置键盘导航
 */
function setupKeyboardNavigation() {
    document.addEventListener('keydown', function(e) {
        // 如果焦点在输入框或文本域，不处理键盘导航
        const activeElement = document.activeElement;
        if (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA' || activeElement.tagName === 'SELECT') {
            return;
        }
        
        // 更新可见卡片列表
        updateVisibleCards();
        
        if (visibleCards.length === 0) return;
        
        switch(e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                moveFocus(-1);
                break;
            case 'ArrowRight':
                e.preventDefault();
                moveFocus(1);
                break;
            case 'ArrowUp':
                e.preventDefault();
                moveFocus(-1);
                break;
            case 'ArrowDown':
                e.preventDefault();
                moveFocus(1);
                break;
            case 'Enter':
                e.preventDefault();
                markCurrentAsPass();
                break;
            case ' ':
                e.preventDefault();
                markCurrentAsFail();
                break;
        }
    });
}

/**
 * 更新可见卡片列表
 */
function updateVisibleCards() {
    visibleCards = Array.from(document.querySelectorAll('.item-card'));
    // 确保当前索引在有效范围内
    if (currentFocusIndex >= visibleCards.length) {
        currentFocusIndex = visibleCards.length - 1;
    }
    if (currentFocusIndex < 0 && visibleCards.length > 0) {
        currentFocusIndex = 0;
    }
}

/**
 * 移动焦点
 */
function moveFocus(direction) {
    if (visibleCards.length === 0) return;
    
    // 移除当前高亮
    if (visibleCards[currentFocusIndex]) {
        visibleCards[currentFocusIndex].classList.remove('keyboard-focus');
    }
    
    // 计算新索引
    currentFocusIndex += direction;
    
    // 循环处理
    if (currentFocusIndex < 0) {
        currentFocusIndex = visibleCards.length - 1;
    } else if (currentFocusIndex >= visibleCards.length) {
        currentFocusIndex = 0;
    }
    
    // 添加新高亮
    if (visibleCards[currentFocusIndex]) {
        visibleCards[currentFocusIndex].classList.add('keyboard-focus');
        // 滚动到可见区域
        visibleCards[currentFocusIndex].scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

/**
 * 标记当前项为合格
 */
function markCurrentAsPass() {
    if (visibleCards.length === 0 || !visibleCards[currentFocusIndex]) return;
    
    const card = visibleCards[currentFocusIndex];
    const itemId = card.dataset.itemId;
    
    if (itemId) {
        submitReview(itemId, '合格');
        // 完成后自动向右移动光标
        setTimeout(() => {
            updateVisibleCards();
            if (visibleCards.length > 0) {
                // 自动向右移动一格
                moveFocus(1);
            }
        }, 100);
    }
}

/**
 * 标记当前项为不合格
 */
function markCurrentAsFail() {
    if (visibleCards.length === 0 || !visibleCards[currentFocusIndex]) return;
    
    const card = visibleCards[currentFocusIndex];
    const itemId = card.dataset.itemId;
    
    if (itemId) {
        submitReview(itemId, '不合格');
        // 不移动焦点，等待用户输入问题描述
    }
}

/**
 * 执行搜索
 */
function performSearch() {
    const searchInput = document.getElementById('storeSearch');
    const keyword = searchInput.value.trim();
    
    if (keyword === '') {
        showToast('⚠️ 请输入门店编号或名称', 'error');
        return;
    }
    
    searchKeyword = keyword;
    searchMode = true;
    
    // 精确搜索匹配的门店
    const matchedItems = allItems.filter(item => {
        const storeId = item['门店编号'].toString();
        const storeName = item['门店名称'];
        // 精确匹配：门店编号或门店名称完全相等
        return storeId === keyword || storeName === keyword;
    });
    
    if (matchedItems.length === 0) {
        showToast('❌ 未找到匹配的门店（请输入完整的门店编号或名称）', 'error');
        return;
    }
    
    // 显示搜索结果
    renderSearchResults(matchedItems);
    
    // 显示清除按钮
    document.getElementById('clearSearchBtn').style.display = 'inline-block';
    
    // 切换到待审核视图
    currentView = 'pending';
    document.getElementById('pendingTab').classList.add('active');
    document.getElementById('completedTab').classList.remove('active');
}

/**
 * 清除搜索
 */
function clearSearch() {
    searchMode = false;
    searchKeyword = '';
    document.getElementById('storeSearch').value = '';
    document.getElementById('clearSearchBtn').style.display = 'none';
    
    // 重新渲染当前视图
    if (currentView === 'pending') {
        renderPendingItems();
    } else {
        renderCompletedStores();
    }
}

/**
 * 渲染搜索结果
 */
function renderSearchResults(items) {
    const container = document.getElementById('itemsContainer');
    container.innerHTML = '';
    
    // 按门店分组
    const storeGroups = {};
    items.forEach(item => {
        const storeId = item['门店编号'];
        if (!storeGroups[storeId]) {
            storeGroups[storeId] = {
                storeId: storeId,
                storeName: item['门店名称'],
                operator: item['负责运营'],
                items: []
            };
        }
        storeGroups[storeId].items.push(item);
    });
    
    // 显示搜索结果标题
    const resultHeader = document.createElement('div');
    resultHeader.className = 'search-result-header';
    const storeCount = Object.keys(storeGroups).length;
    resultHeader.textContent = `🔍 搜索结果：找到 ${storeCount} 家门店，共 ${items.length} 个检查项`;
    container.appendChild(resultHeader);
    
    // 渲染每个门店的检查项
    Object.values(storeGroups).forEach(store => {
        store.items.forEach(item => {
            const card = createItemCard(item);
            container.appendChild(card);
        });
    });
}

/**
 * 切换视图
 */
function switchView(view) {
    currentView = view;
    document.getElementById('pendingTab').classList.toggle('active', view === 'pending');
    document.getElementById('completedTab').classList.toggle('active', view === 'completed');
    
    if (view === 'pending') {
        renderPendingItems();
    } else {
        renderCompletedStores();
    }
}

/**
 * 加载运营人员列表
 */
async function loadOperators() {
    try {
        const response = await fetch('/api/operators');
        const operators = await response.json();
        
        const select = document.getElementById('operatorFilter');
        operators.forEach(operator => {
            const option = document.createElement('option');
            option.value = operator;
            option.textContent = operator;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('加载运营人员列表失败:', error);
    }
}

/**
 * 加载检查项数据
 */
async function loadItems() {
    try {
        let url = '/api/items';
        if (currentOperator && currentOperator !== '全部') {
            url += `?operator=${encodeURIComponent(currentOperator)}`;
        }
        
        const response = await fetch(url);
        const items = await response.json();
        allItems = items;
        
        console.log(`📦 加载了 ${items.length} 个检查项`);
        
        if (items.length === 0) {
            document.getElementById('itemsContainer').innerHTML = '<div class="loading"><p>暂无检查项数据</p></div>';
            document.getElementById('totalCount').textContent = `总计: 0`;
            return;
        }
        
        document.getElementById('totalCount').textContent = `总计: ${items.length}`;
        // 不在这里渲染，等reviews加载完再渲染
        updateAdminPanel();
        
    } catch (error) {
        console.error('加载数据失败:', error);
        showToast('加载数据失败，请刷新页面重试', 'error');
    }
}

/**
 * 加载已有的审核结果
 */
async function loadReviews() {
    try {
        console.log('🔄 开始从数据库加载审核结果...');
        const response = await fetch('/api/reviews');
        const reviewList = await response.json();
        
        console.log(`✅ 成功加载 ${reviewList.length} 条审核记录`);
        
        reviews = {};
        reviewList.forEach(review => {
            reviews[review.item_id] = review;
        });
        
        console.log(`📊 reviews对象中有 ${Object.keys(reviews).length} 条记录`);
        console.log(`📦 allItems数组中有 ${allItems.length} 个检查项`);
        
        // 检查已完成的门店
        updateReviewCount();
        checkCompletedStores();
        
        console.log(`✅ 识别到 ${completedStores.length} 家已完成的门店`);
        
        // 渲染页面
        renderPendingItems();
        updateStatsPanel();
        
        console.log('✅ 审核数据加载完成，页面已渲染');
        
    } catch (error) {
        console.error('❌ 加载审核结果失败:', error);
        showToast('❌ 加载审核数据失败，请刷新页面', 'error');
    }
}

/**
 * 检查已完成的门店
 */
function checkCompletedStores() {
    const storeItems = {};
    
    // 按门店分组
    allItems.forEach(item => {
        const storeId = item['门店编号'];
        if (!storeItems[storeId]) {
            storeItems[storeId] = {
                storeId: storeId,
                storeName: item['门店名称'],
                operator: item['负责运营'],
                items: [],
                completedTime: null
            };
        }
        storeItems[storeId].items.push(item);
    });
    
    // 检查每个门店是否完成
    completedStores = [];
    Object.values(storeItems).forEach(store => {
        // 检查所有检查项是否都已审核，且不合格的都有问题描述
        const allCompleted = store.items.every(item => {
            const review = reviews[item.id];
            if (!review) return false;
            
            // 如果是不合格，必须有问题描述
            if (review['审核结果'] === '不合格') {
                return review['问题描述'] && review['问题描述'].trim() !== '';
            }
            
            return true;
        });
        
        if (allCompleted && store.items.length > 0) {
            // 获取最后完成时间
            const times = store.items.map(item => reviews[item.id]?.['审核时间']).filter(t => t);
            store.completedTime = times.length > 0 ? times.sort().reverse()[0] : null;
            completedStores.push(store);
        }
    });
    
    // 按完成时间倒序排列
    completedStores.sort((a, b) => {
        if (!a.completedTime) return 1;
        if (!b.completedTime) return -1;
        return b.completedTime.localeCompare(a.completedTime);
    });
}

/**
 * 渲染待审核检查项（分页）
 */
function renderPendingItems() {
    // 如果处于搜索模式，不执行正常渲染
    if (searchMode) {
        return;
    }
    
    const container = document.getElementById('itemsContainer');
    container.innerHTML = '';
    
    // 获取未完成的门店
    const completedStoreIds = new Set(completedStores.map(s => s.storeId));
    
    // 过滤：排除已完成门店 AND 排除无现场结果的检查项
    const pendingItems = allItems.filter(item => {
        // 排除已完成的门店
        if (completedStoreIds.has(item['门店编号'])) {
            return false;
        }
        
        // 排除无现场结果的检查项（这些已经自动标记为不合格）
        if (item['无现场结果'] === true) {
            return false;
        }
        
        return true;
    });
    
    if (pendingItems.length === 0) {
        container.innerHTML = '<div class="loading"><p>🎉 所有门店已审核完成！</p></div>';
        return;
    }
    
    // 按门店分组
    const storeGroups = {};
    pendingItems.forEach(item => {
        const storeId = item['门店编号'];
        if (!storeGroups[storeId]) {
            storeGroups[storeId] = [];
        }
        storeGroups[storeId].push(item);
    });
    
    // 获取要显示的门店（最多10个）
    const storeIds = Object.keys(storeGroups);
    const displayStoreIds = storeIds.slice(0, ITEMS_PER_PAGE);
    
    // 渲染这些门店的检查项
    displayStoreIds.forEach(storeId => {
        const items = storeGroups[storeId];
        items.forEach(item => {
            const card = createItemCard(item);
            container.appendChild(card);
        });
    });
    
    displayedStores = new Set(displayStoreIds);
    
    // 初始化键盘导航
    setTimeout(() => {
        updateVisibleCards();
        currentFocusIndex = 0;
        if (visibleCards.length > 0) {
            visibleCards[0].classList.add('keyboard-focus');
        }
    }, 100);
}

/**
 * 渲染已完成门店列表
 */
function renderCompletedStores() {
    const container = document.getElementById('itemsContainer');
    container.innerHTML = '';
    
    if (completedStores.length === 0) {
        container.innerHTML = '<div class="loading"><p>暂无已完成的门店</p></div>';
        return;
    }
    
    // 按当前运营人员筛选已完成门店
    let filteredStores = completedStores;
    if (currentOperator && currentOperator !== '全部') {
        filteredStores = completedStores.filter(store => store.operator === currentOperator);
    }
    
    if (filteredStores.length === 0) {
        container.innerHTML = '<div class="loading"><p>暂无已完成的门店</p></div>';
        return;
    }
    
    filteredStores.forEach(store => {
        const card = createCompletedStoreCard(store);
        container.appendChild(card);
    });
}

/**
 * 创建已完成门店卡片
 */
function createCompletedStoreCard(store) {
    const card = document.createElement('div');
    card.className = 'completed-store-card';
    card.dataset.storeId = store.storeId;
    
    const completedCount = store.items.length;
    const passCount = store.items.filter(item => reviews[item.id]?.['审核结果'] === '合格').length;
    const failCount = completedCount - passCount;
    
    card.innerHTML = `
        <div class="completed-header" onclick="toggleStoreDetails('${store.storeId}')">
            <div class="store-info">
                <div class="store-name">
                    <span class="expand-icon" id="expand-${store.storeId}">▶</span>
                    ✓ ${store.storeName}
                </div>
                <div class="store-details">
                    <span>门店编号: ${store.storeId}</span>
                    <span>|</span>
                    <span>👤 ${store.operator}</span>
                </div>
            </div>
            <div class="completed-time">${store.completedTime || ''}</div>
        </div>
        <div class="completed-stats">
            <span class="stat-badge">共${completedCount}项</span>
            <span class="stat-badge pass">合格${passCount}</span>
            <span class="stat-badge fail">不合格${failCount}</span>
            <span class="edit-hint">💡 点击展开编辑</span>
        </div>
        <div class="store-items-detail" id="detail-${store.storeId}" style="display: none;">
            <!-- 检查项详情将在这里动态加载 -->
        </div>
    `;
    
    return card;
}

/**
 * 切换门店详情显示
 */
function toggleStoreDetails(storeId) {
    const detailContainer = document.getElementById(`detail-${storeId}`);
    const expandIcon = document.getElementById(`expand-${storeId}`);
    
    if (detailContainer.style.display === 'none') {
        // 展开：加载并显示检查项
        detailContainer.style.display = 'block';
        expandIcon.textContent = '▼';
        
        // 加载该门店的所有检查项
        const store = completedStores.find(s => s.storeId === storeId);
        if (store) {
            renderStoreItems(storeId, store.items);
        }
    } else {
        // 收起
        detailContainer.style.display = 'none';
        expandIcon.textContent = '▶';
    }
}

/**
 * 渲染门店的检查项详情（用于编辑）
 */
function renderStoreItems(storeId, items) {
    const detailContainer = document.getElementById(`detail-${storeId}`);
    detailContainer.innerHTML = '';
    
    items.forEach(item => {
        const itemCard = createEditableItemCard(item);
        detailContainer.appendChild(itemCard);
    });
}

/**
 * 创建可编辑的检查项卡片（用于已完成列表）
 */
function createEditableItemCard(item) {
    const card = document.createElement('div');
    card.className = 'editable-item-card';
    card.dataset.itemId = item.id;
    
    const review = reviews[item.id];
    const reviewStatus = review ? review['审核结果'] : null;
    const problemNote = review ? review['问题描述'] || '' : '';
    
    const imageUrl = item['标准图'] || '';
    
    card.innerHTML = `
        <div class="editable-item-header">
            <div class="item-name">📋 ${escapeHtml(item['检查项名称'])}</div>
            <div class="review-status ${reviewStatus === '合格' ? 'status-pass' : 'status-fail'}">
                ${reviewStatus === '合格' ? '✓ 合格' : '✗ 不合格'}
            </div>
        </div>
        <div class="editable-item-body">
            <div class="image-preview clickable-image">
                ${imageUrl ? 
                    `<img alt="${escapeHtml(item['检查项名称'])}" loading="lazy" referrerpolicy="no-referrer" data-retry="0">
                     <div class="image-loading">⏳ 加载中...</div>` :
                    '<div class="image-placeholder">📷 暂无图片</div>'
                }
            </div>
            <div class="review-section">
                <div class="review-buttons">
                    <button class="review-btn pass ${reviewStatus === '合格' ? 'active' : ''}" 
                            onclick="submitReview('${item.id}', '合格')">
                        ✓ 合格
                    </button>
                    <button class="review-btn fail ${reviewStatus === '不合格' ? 'active' : ''} ${reviewStatus === '不合格' && problemNote ? 'completed' : ''}" 
                            onclick="submitReview('${item.id}', '不合格')">
                        ✗ 不合格
                    </button>
                </div>
                ${reviewStatus === '不合格' && problemNote ? `
                    <div class="problem-display">
                        <strong>问题描述：</strong>${escapeHtml(problemNote)}
                    </div>
                ` : ''}
                <div class="problem-input-container" id="problem-${item.id}" style="display: none;">
                    <label class="problem-label">❗ 问题描述:</label>
                    <textarea class="problem-input" id="textarea-${item.id}"
                              placeholder="请输入具体问题..."
                              onkeydown="handleProblemKeydown(event, '${item.id}')">${escapeHtml(problemNote)}</textarea>
                    <button class="save-problem-btn" onclick="saveProblemNoteAndRefreshWithButton('${item.id}')">✓ 保存并完成</button>
                </div>
            </div>
        </div>
    `;
    
    // 使用JavaScript直接设置img的src属性
    if (imageUrl) {
        const imagePreview = card.querySelector('.image-preview');
        const img = imagePreview.querySelector('img');
        const loadingDiv = imagePreview.querySelector('.image-loading');
        
        if (img) {
            img.onload = function() {
                if (loadingDiv) loadingDiv.style.display = 'none';
            };
            
            img.onerror = function() {
                handleImageErrorWithRetry(this, imageUrl);
            };
            
            img.src = imageUrl;  // 直接设置src，避免HTML转义
        }
        
        // 设置data属性用于点击事件
        imagePreview.dataset.imageUrl = imageUrl;
        imagePreview.dataset.caption = item['门店名称'] + ' - ' + item['检查项名称'];
    }
    
    return card;
}

/**
 * 保存问题描述并刷新显示（用于已完成列表编辑）
 */
async function saveProblemNoteAndRefresh(itemId, problemNote, closeAfterSave = false) {
    await saveProblemNote(itemId, problemNote, closeAfterSave);
    
    // 刷新已完成列表
    checkCompletedStores();
    
    // 如果当前在已完成视图，重新渲染
    if (currentView === 'completed') {
        renderCompletedStores();
    }
}

/**
 * 创建检查项卡片
 */
function createItemCard(item) {
    const card = document.createElement('div');
    card.className = 'item-card';
    card.dataset.itemId = item.id;
    card.dataset.storeId = item['门店编号'];
    
    const review = reviews[item.id];
    const reviewStatus = review ? review['审核结果'] : null;
    const problemNote = review ? review['问题描述'] || '' : '';
    const operator = item['负责运营'] || '未分配';
    
    const imageUrl = item['标准图'] || '';
    
    // 创建卡片结构
    card.innerHTML = `
        <div class="card-header">
            <div class="store-info">
                <div class="store-name">${escapeHtml(item['门店名称'])}</div>
                <div class="store-details">
                    <span>门店编号: ${escapeHtml(item['门店编号'])}</span>
                    <span>|</span>
                    <span>区域: ${escapeHtml(item['所属区域'])}</span>
                    <span class="operator-badge">👤 ${escapeHtml(operator)}</span>
                </div>
            </div>
            <div class="item-name">📋 ${escapeHtml(item['检查项名称'])}</div>
        </div>
        <div class="card-body">
            <div class="image-container clickable-image">
                ${imageUrl ? 
                    `<img alt="${escapeHtml(item['检查项名称'])}" loading="lazy" referrerpolicy="no-referrer" data-retry="0">
                     <div class="image-loading">⏳ 加载中...</div>` :
                    '<div class="image-placeholder">📷 暂无图片</div>'
                }
            </div>
            <div class="review-buttons">
                <button class="review-btn pass ${reviewStatus === '合格' ? 'active' : ''}" 
                        onclick="submitReview('${item.id}', '合格')">
                    ✓ 合格
                </button>
                <button class="review-btn fail ${reviewStatus === '不合格' ? 'active' : ''}" 
                        onclick="submitReview('${item.id}', '不合格')">
                    ✗ 不合格
                </button>
            </div>
            <div class="problem-input-container" id="problem-${item.id}" style="display: ${reviewStatus === '不合格' && problemNote === '' ? 'block' : 'none'};">
                <label class="problem-label">❗ 问题描述:</label>
                <textarea class="problem-input" id="textarea-${item.id}"
                          placeholder="请输入具体问题..."
                          onkeydown="handleProblemKeydown(event, '${item.id}')">${escapeHtml(problemNote)}</textarea>
                <button class="save-problem-btn" onclick="saveProblemNoteWithButton('${item.id}')">✓ 保存并完成</button>
            </div>
        </div>
    `;
    
    // 使用JavaScript直接设置img的src属性，避免HTML转义问题
    if (imageUrl) {
        const imageContainer = card.querySelector('.image-container');
        const img = imageContainer.querySelector('img');
        const loadingDiv = imageContainer.querySelector('.image-loading');
        
        if (img) {
            // 设置加载和错误处理
            img.onload = function() {
                if (loadingDiv) loadingDiv.style.display = 'none';
            };
            
            img.onerror = function() {
                handleImageErrorWithRetry(this, imageUrl);
            };
            
            img.src = imageUrl;  // 直接设置src，不经过HTML解析
        }
        
        // 设置data属性用于点击事件
        imageContainer.dataset.imageUrl = imageUrl;
        imageContainer.dataset.caption = item['门店名称'] + ' - ' + item['检查项名称'];
    }
    
    return card;
}

/**
 * 处理图片加载错误（带重试机制）
 */
function handleImageErrorWithRetry(img, originalUrl) {
    const container = img.parentElement;
    const loadingDiv = container.querySelector('.image-loading');
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
            <br><small style="font-size:10px;">网络较慢，请稍后刷新</small>
            <br><button onclick="retryLoadImage(this)" style="margin-top:5px;padding:5px 10px;cursor:pointer;">🔄 重新加载</button>
        `;
        errorDiv.dataset.imageUrl = originalUrl;
        
        img.style.display = 'none';
        container.appendChild(errorDiv);
    }
}

/**
 * 手动重试加载图片
 */
function retryLoadImage(button) {
    const errorDiv = button.parentElement;
    const container = errorDiv.parentElement;
    const img = container.querySelector('img');
    const imageUrl = errorDiv.dataset.imageUrl;
    
    if (img && imageUrl) {
        errorDiv.remove();
        img.style.display = 'block';
        img.dataset.retry = '0';
        
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'image-loading';
        loadingDiv.textContent = '⏳ 重新加载中...';
        container.appendChild(loadingDiv);
        
        img.src = imageUrl + '?manual=' + Date.now();
    }
}

/**
 * 处理图片加载错误（旧版本，保留兼容性）
 */
function handleImageError(img) {
    handleImageErrorWithRetry(img, img.src);
}

/**
 * 处理问题描述输入框的回车键
 */
function handleProblemKeydown(event, itemId) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        // 回车键触发保存按钮
        saveProblemNoteWithButton(itemId);
    }
}

/**
 * 通过按钮保存问题描述
 */
function saveProblemNoteWithButton(itemId) {
    const textarea = document.getElementById(`textarea-${itemId}`);
    const problemNote = textarea.value.trim();
    
    if (problemNote === '') {
        showToast('⚠️ 请输入问题描述', 'error');
        textarea.focus();
        return;
    }
    
    // 保存并关闭输入框
    saveProblemNote(itemId, problemNote, true);
}

/**
 * 通过按钮保存问题描述并刷新（用于已完成列表）
 */
function saveProblemNoteAndRefreshWithButton(itemId) {
    const textarea = document.getElementById(`textarea-${itemId}`);
    const problemNote = textarea.value.trim();
    
    if (problemNote === '') {
        showToast('⚠️ 请输入问题描述', 'error');
        textarea.focus();
        return;
    }
    
    // 保存并关闭输入框
    saveProblemNoteAndRefresh(itemId, problemNote, true);
}

/**
 * 提交审核结果
 */
async function submitReview(itemId, result) {
    try {
        const problemContainer = document.getElementById(`problem-${itemId}`);
        const existingReview = reviews[itemId];
        
        // 如果选择"不合格"
        if (result === '不合格') {
            // 如果已经有问题描述，切换输入框显示状态
            if (existingReview && existingReview['审核结果'] === '不合格' && existingReview['问题描述']) {
                // 已有问题描述，切换输入框
                if (problemContainer.style.display === 'none') {
                    problemContainer.style.display = 'block';
                    const textarea = problemContainer.querySelector('.problem-input');
                    setTimeout(() => textarea.focus(), 100);
                } else {
                    problemContainer.style.display = 'none';
                }
                return; // 不重新提交审核
            } else {
                // 没有问题描述，显示输入框
                problemContainer.style.display = 'block';
                const textarea = problemContainer.querySelector('.problem-input');
                setTimeout(() => textarea.focus(), 100);
            }
        } else {
            // 选择"合格"，隐藏输入框
            problemContainer.style.display = 'none';
        }
        
        const response = await fetch('/api/review', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                item_id: itemId,
                '审核结果': result
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const item = allItems.find(i => i.id === itemId);
            if (item) {
                reviews[itemId] = {
                    item_id: itemId,
                    '审核结果': result,
                    '问题描述': existingReview ? existingReview['问题描述'] : '',
                    '审核时间': new Date().toLocaleString('zh-CN')
                };
            }
            
            updateCardReviewStatus(itemId, result);
            updateReviewCount();
            
            // 只有合格时才立即检查门店完成状态
            // 不合格需要等待填写问题描述
            if (result === '合格') {
                checkStoreCompletion(item['门店编号']);
            }
            
            showToast(`✓ 审核成功: ${result}`, 'success');
        } else {
            showToast('❌ 审核失败: ' + (data.error || '未知错误'), 'error');
        }
        
    } catch (error) {
        console.error('提交审核失败:', error);
        showToast('❌ 提交失败，请重试', 'error');
    }
}

/**
 * 保存问题描述
 */
async function saveProblemNote(itemId, problemNote, closeAfterSave = false) {
    try {
        console.log('💾 [调试] saveProblemNote 开始，itemId:', itemId, '问题描述:', problemNote);
        
        // 更新本地reviews
        if (reviews[itemId]) {
            reviews[itemId]['问题描述'] = problemNote;
            console.log('💾 [调试] 已更新本地reviews');
        } else {
            console.warn('⚠️ [调试] reviews中没有找到itemId:', itemId);
        }
        
        // 提交到后端
        const response = await fetch('/api/review/problem', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                item_id: itemId,
                '问题描述': problemNote
            })
        });
        
        const data = await response.json();
        console.log('💾 [调试] 后端响应:', data);
        
        if (data.success) {
            console.log('✅ [调试] 问题描述已保存到后端');
            
            // 如果需要关闭输入框
            if (closeAfterSave && problemNote.trim() !== '') {
                const problemContainer = document.getElementById(`problem-${itemId}`);
                if (problemContainer) {
                    problemContainer.style.display = 'none';
                }
                
                // 更新按钮状态为已完成（红色）
                const card = document.querySelector(`[data-item-id="${itemId}"]`);
                if (card) {
                    const failBtn = card.querySelector('.review-btn.fail');
                    if (failBtn) {
                        failBtn.classList.add('active');
                        failBtn.classList.add('completed');
                    }
                }
                
                showToast('✓ 问题描述已保存', 'success');
                
                // 完成后自动向右移动光标
                setTimeout(() => {
                    updateVisibleCards();
                    if (visibleCards.length > 0) {
                        moveFocus(1);
                    }
                }, 100);
            }
            
            // 保存后重新检查门店是否完成（关键修复！）
            const item = allItems.find(i => i.id === itemId);
            if (item && problemNote.trim() !== '') {
                console.log('🔍 [调试] 准备检查门店完成状态，门店编号:', item['门店编号']);
                checkStoreCompletion(item['门店编号']);
            } else {
                console.warn('⚠️ [调试] 未找到item或问题描述为空，不检查门店完成状态');
            }
        }
        
    } catch (error) {
        console.error('❌ [调试] 保存问题描述失败:', error);
    }
}

/**
 * 检查门店是否完成
 */
function checkStoreCompletion(storeId) {
    console.log('🔍 [调试] 检查门店完成状态，门店编号:', storeId);
    
    const storeItems = allItems.filter(item => item['门店编号'] === storeId);
    console.log('🔍 [调试] 该门店的检查项数量:', storeItems.length);
    
    // 检查是否所有检查项都已审核，且不合格的都有问题描述
    const itemsStatus = storeItems.map(item => {
        const review = reviews[item.id];
        const status = {
            itemId: item.id,
            itemName: item['检查项名称'],
            hasReview: !!review,
            reviewResult: review ? review['审核结果'] : null,
            problemNote: review ? review['问题描述'] : null,
            isComplete: false
        };
        
        if (!review) {
            status.isComplete = false;
        } else if (review['审核结果'] === '不合格') {
            status.isComplete = review['问题描述'] && review['问题描述'].trim() !== '';
        } else {
            status.isComplete = true;
        }
        
        return status;
    });
    
    console.log('🔍 [调试] 检查项详细状态:', itemsStatus);
    
    const allCompleted = itemsStatus.every(item => item.isComplete);
    console.log('🔍 [调试] 所有检查项是否完成:', allCompleted);
    
    if (allCompleted && storeItems.length > 0) {
        console.log('✅ [调试] 门店已完成，准备移除');
        // 门店完成，隐藏并加载新的
        setTimeout(() => {
            checkCompletedStores();
            if (currentView === 'pending') {
                renderPendingItems();
                // 门店完成后，光标自动回到最左侧（第一个卡片）
                setTimeout(() => {
                    updateVisibleCards();
                    currentFocusIndex = 0;
                    if (visibleCards.length > 0) {
                        visibleCards[0].classList.add('keyboard-focus');
                        visibleCards[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }, 100);
            }
            showToast(`🎉 门店 ${storeId} 已完成审核！`, 'success');
            updateStatsPanel();
            updateAdminPanel();
        }, 500);
    } else {
        console.log('⚠️ [调试] 门店未完成，还有检查项待处理');
    }
}

/**
 * 更新卡片的审核状态显示
 */
function updateCardReviewStatus(itemId, result) {
    const card = document.querySelector(`[data-item-id="${itemId}"]`);
    if (!card) return;
    
    const buttons = card.querySelectorAll('.review-btn');
    buttons.forEach(btn => {
        btn.classList.remove('active');
        btn.classList.remove('completed');
    });
    
    if (result === '合格') {
        card.querySelector('.review-btn.pass').classList.add('active');
    } else if (result === '不合格') {
        const failBtn = card.querySelector('.review-btn.fail');
        failBtn.classList.add('active');
        
        // 如果有问题描述，添加completed样式
        const review = reviews[itemId];
        if (review && review['问题描述'] && review['问题描述'].trim() !== '') {
            failBtn.classList.add('completed');
        }
    }
}

/**
 * 更新已审核计数
 */
function updateReviewCount() {
    const count = Object.keys(reviews).length;
    document.getElementById('reviewedCount').textContent = `已审核: ${count}`;
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
 * 导出审核结果
 */
async function exportReviews() {
    try {
        if (Object.keys(reviews).length === 0) {
            showToast('⚠️ 暂无审核结果可导出', 'error');
            return;
        }
        
        const response = await fetch('/api/export');
        
        if (!response.ok) {
            const error = await response.json();
            showToast('❌ ' + (error.error || '导出失败'), 'error');
            return;
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `审核结果_${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showToast('✓ 导出成功', 'success');
        
    } catch (error) {
        console.error('导出失败:', error);
        showToast('❌ 导出失败，请重试', 'error');
    }
}

/**
 * 更新统计面板（所有运营人员都显示）
 */
async function updateStatsPanel() {
    const statsPanel = document.getElementById('statsPanel');
    
    console.log('📊 更新统计面板，当前运营人员:', currentOperator);
    console.log('📊 当前reviews数量:', Object.keys(reviews).length);
    
    // 所有运营人员都显示统计面板
    if (currentOperator && currentOperator !== '全部') {
        statsPanel.style.display = 'block';
        
        try {
            // 获取全量统计
            const allStatsResponse = await fetch('/api/stats');
            const allStats = await allStatsResponse.json();
            console.log('📊 全量统计:', allStats);
            
            // 获取个人统计
            const personalStatsResponse = await fetch(`/api/stats?operator=${encodeURIComponent(currentOperator)}`);
            const personalStats = await personalStatsResponse.json();
            console.log('📊 个人统计:', personalStats);
            
            // 显示全量统计
            document.getElementById('allProgress').textContent = `${allStats.reviewed}/${allStats.total}`;
            document.getElementById('allPercent').textContent = `${allStats.percentage}%`;
            
            // 显示个人统计
            document.getElementById('personalProgress').textContent = `${personalStats.reviewed}/${personalStats.total}`;
            document.getElementById('personalPercent').textContent = `${personalStats.percentage}%`;
            
            // 显示运营人员名称
            document.getElementById('operatorName').textContent = currentOperator;
            
            console.log('✅ 统计面板更新完成');
            
        } catch (error) {
            console.error('❌ 获取统计信息失败:', error);
        }
    } else {
        statsPanel.style.display = 'none';
        console.log('📊 统计面板隐藏（全部运营人员）');
    }
}

/**
 * 更新管理员面板（仅窦显示）
 */
async function updateAdminPanel() {
    const adminPanel = document.getElementById('adminPanel');
    
    if (currentOperator === '窦') {
        adminPanel.style.display = 'block';
    } else {
        adminPanel.style.display = 'none';
    }
}

/**
 * 导出当前数据（不改变任何状态）
 */
async function exportCurrentData() {
    if (Object.keys(reviews).length === 0) {
        showToast('⚠️ 暂无审核结果可导出', 'error');
        return;
    }
    
    await exportReviews();
}

/**
 * 上传新Excel文件（开始新周期）
 */
async function uploadNewFile(event) {
    const file = event.target.files[0];
    
    if (!file) return;
    
    if (!file.name.endsWith('.xlsx')) {
        showToast('❌ 只支持.xlsx文件', 'error');
        return;
    }
    
    if (!confirm(`确认上传文件"${file.name}"并开始新周期吗？\n\n这将清空所有审核记录！`)) {
        event.target.value = '';
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('operator', currentOperator);
        
        showToast('正在上传文件...', 'success');
        
        const response = await fetch('/api/admin/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`✓ ${data.message}`, 'success');
            
            reviews = {};
            displayedStores.clear();
            completedStores = [];
            await loadItems();
            await loadReviews();
            updateAdminPanel();
        } else {
            showToast('❌ ' + (data.error || '上传失败'), 'error');
        }
        
        event.target.value = '';
        
    } catch (error) {
        console.error('上传失败:', error);
        showToast('❌ 上传失败，请重试', 'error');
        event.target.value = '';
    }
}


/**
 * HTML转义函数，防止XSS和引号冲突
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 打开图片查看器
 */
function openImageModal(imageSrc, caption) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    const modalCaption = document.getElementById('modalCaption');
    
    modal.classList.add('show');
    modalImg.src = imageSrc;
    modalCaption.textContent = caption;
    
    // 防止背景滚动
    document.body.style.overflow = 'hidden';
}

/**
 * 关闭图片查看器
 */
function closeImageModal() {
    const modal = document.getElementById('imageModal');
    modal.classList.remove('show');
    
    // 恢复背景滚动
    document.body.style.overflow = 'auto';
}

/**
 * 键盘ESC关闭模态框
 */
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeImageModal();
    }
});

/**
 * 事件委托：处理图片点击
 */
document.addEventListener('click', function(event) {
    // 查找最近的可点击图片容器
    const imageContainer = event.target.closest('.clickable-image');
    
    if (imageContainer) {
        console.log('🔍 [调试] 点击了图片容器');
        const imageUrl = imageContainer.dataset.imageUrl;
        const caption = imageContainer.dataset.caption;
        console.log('🔍 [调试] 图片URL:', imageUrl);
        console.log('🔍 [调试] 图片标题:', caption);
        
        if (imageUrl && imageUrl !== 'undefined' && imageUrl !== 'null') {
            console.log('✅ [调试] 打开图片查看器');
            openImageModal(imageUrl, caption);
        } else {
            console.warn('⚠️ [调试] 图片URL无效，无法打开查看器');
        }
    }
});
