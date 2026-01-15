// 审核结果展示系统前端逻辑

// 全局状态
let filterOptions = {
    war_zones: [],
    provinces: [],
    cities: [],
    store_tags: [],
    review_results: []
};

let currentFilters = {
    war_zone: '',
    province: '',
    city: '',
    store_tag: '',
    review_result: ''
};

let searchResults = [];

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🚀 页面加载开始...');
    
    // 加载筛选选项
    await loadFilterOptions();
    
    // 绑定事件
    bindEvents();
    
    console.log('✅ 页面初始化完成');
});

/**
 * 加载筛选选项
 */
async function loadFilterOptions() {
    try {
        showToast('正在加载筛选选项...', 'info');
        
        const response = await fetch('/api/filters');
        const data = await response.json();
        
        if (data.success) {
            filterOptions = data.data;
            
            // 填充战区下拉菜单
            populateSelect('warZoneFilter', filterOptions.war_zones);
            
            // 填充门店标签下拉菜单
            populateSelect('storeTagFilter', filterOptions.store_tags);
            
            // 填充是否合格下拉菜单
            populateSelect('reviewResultFilter', filterOptions.review_results);
            
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
    
    // 门店标签选择变化
    document.getElementById('storeTagFilter').addEventListener('change', function(e) {
        currentFilters.store_tag = e.target.value;
    });
    
    // 是否合格选择变化
    document.getElementById('reviewResultFilter').addEventListener('change', function(e) {
        currentFilters.review_result = e.target.value;
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
}

/**
 * 根据战区加载省份列表
 */
async function loadProvinces(warZone) {
    try {
        const response = await fetch(`/api/filters/provinces?war_zone=${encodeURIComponent(warZone)}`);
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
        const response = await fetch(`/api/filters/cities?province=${encodeURIComponent(province)}`);
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
 * 执行搜索
 */
async function performSearch() {
    try {
        // 显示加载状态
        showLoading();
        
        // 构建查询参数
        const params = new URLSearchParams();
        if (currentFilters.war_zone) params.append('war_zone', currentFilters.war_zone);
        if (currentFilters.province) params.append('province', currentFilters.province);
        if (currentFilters.city) params.append('city', currentFilters.city);
        if (currentFilters.store_tag) params.append('store_tag', currentFilters.store_tag);
        if (currentFilters.review_result) params.append('review_result', currentFilters.review_result);
        
        const response = await fetch(`/api/search?${params.toString()}`);
        const data = await response.json();
        
        if (data.success) {
            searchResults = data.data.results;
            renderResults(searchResults);
            updateResultCount(data.data.count);
            
            if (data.data.count === 0) {
                showToast('未找到符合条件的审核结果', 'info');
            } else {
                showToast(`找到 ${data.data.count} 条审核结果`, 'success');
            }
        } else {
            showToast('搜索失败: ' + data.error, 'error');
            showEmptyResults();
        }
        
    } catch (error) {
        console.error('搜索失败:', error);
        showToast('搜索失败，请重试', 'error');
        showEmptyResults();
    }
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
        store_tag: '',
        review_result: ''
    };
    
    // 重置下拉菜单
    document.getElementById('warZoneFilter').value = '';
    document.getElementById('provinceFilter').value = '';
    document.getElementById('cityFilter').value = '';
    document.getElementById('storeTagFilter').value = '';
    document.getElementById('reviewResultFilter').value = '';
    
    // 禁用省份和城市下拉菜单
    document.getElementById('provinceFilter').disabled = true;
    document.getElementById('cityFilter').disabled = true;
    
    // 清空省份和城市选项
    populateSelect('provinceFilter', []);
    populateSelect('cityFilter', []);
    
    // 显示欢迎消息
    showWelcomeMessage();
    updateResultCount(0);
    
    showToast('已清除所有筛选条件', 'info');
}

/**
 * 渲染搜索结果
 */
function renderResults(results) {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = '';
    
    if (results.length === 0) {
        showEmptyResults();
        return;
    }
    
    results.forEach(result => {
        const card = createResultCard(result);
        container.appendChild(card);
    });
}

/**
 * 创建结果卡片
 */
function createResultCard(result) {
    const card = document.createElement('div');
    card.className = 'result-card';
    
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
            <div class="image-container" onclick="openImageModal('${escapeHtml(imageUrl)}', '${escapeHtml(result.store_name + ' - ' + result.item_name)}')">
                ${imageUrl ? 
                    `<img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(result.item_name)}" loading="lazy" onerror="handleImageError(this)">` :
                    '<div class="image-placeholder">📷 暂无图片</div>'
                }
            </div>
            <div class="review-status ${reviewResult === '合格' ? 'pass' : 'fail'}">
                <span class="status-icon">${reviewResult === '合格' ? '✓' : '✗'}</span>
                <span class="status-text">${reviewResult === '合格' ? '合格' : '不合格'}</span>
            </div>
            ${reviewResult === '不合格' && problemNote ? `
                <div class="problem-note">
                    <div class="problem-label">❗ 问题描述:</div>
                    <div class="problem-text">${escapeHtml(problemNote)}</div>
                </div>
            ` : ''}
        </div>
    `;
    
    return card;
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
function updateResultCount(count) {
    document.getElementById('resultCount').textContent = `结果: ${count}`;
}

/**
 * 处理图片加载错误
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
}

/**
 * 关闭图片模态框
 */
function closeImageModal() {
    const modal = document.getElementById('imageModal');
    modal.classList.remove('show');
    
    // 恢复背景滚动
    document.body.style.overflow = 'auto';
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
