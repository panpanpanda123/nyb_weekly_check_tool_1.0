// 设备异常监控 JavaScript

const API_BASE_PATH = '';

// 全局状态
let currentPage = 1;
let totalPages = 1;
let filters = {
    war_zone: '',
    regional_manager: '',
    store_search: ''
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 设备异常监控页面加载开始...');
    initEquipmentPage();
});

// 初始化页面
async function initEquipmentPage() {
    try {
        await loadFilterOptions();
        setupEventListeners();
        console.log('✅ 设备异常监控页面初始化完成');
    } catch (error) {
        console.error('❌ 页面初始化失败:', error);
        showToast('页面初始化失败，请刷新重试', 'error');
    }
}

// 加载筛选选项
async function loadFilterOptions() {
    try {
        const response = await fetch(`${API_BASE_PATH}/api/equipment/filters`);
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            
            // 填充战区选项
            const warZoneSelect = document.getElementById('warZoneFilter');
            warZoneSelect.innerHTML = '<option value="">全部</option>';
            data.war_zones.forEach(wz => {
                warZoneSelect.innerHTML += `<option value="${wz}">${wz}</option>`;
            });
            
            console.log('✅ 筛选选项加载完成');
        } else {
            throw new Error(result.error || '加载筛选选项失败');
        }
    } catch (error) {
        console.error('加载筛选选项失败:', error);
        throw error;
    }
}

// 根据战区加载区域经理
async function loadRegionalManagers(warZone) {
    try {
        const regionalManagerSelect = document.getElementById('regionalManagerFilter');
        
        if (!warZone) {
            regionalManagerSelect.innerHTML = '<option value="">全部</option>';
            regionalManagerSelect.disabled = true;
            return;
        }
        
        const response = await fetch(`${API_BASE_PATH}/api/equipment/regional-managers?war_zone=${encodeURIComponent(warZone)}`);
        const result = await response.json();
        
        if (result.success) {
            regionalManagerSelect.innerHTML = '<option value="">全部</option>';
            result.data.regional_managers.forEach(rm => {
                regionalManagerSelect.innerHTML += `<option value="${rm}">${rm}</option>`;
            });
            regionalManagerSelect.disabled = false;
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
    
    // 战区变化 - 级联加载区域经理
    document.getElementById('warZoneFilter').addEventListener('change', async (e) => {
        const warZone = e.target.value;
        filters.war_zone = warZone;
        filters.regional_manager = '';
        document.getElementById('regionalManagerFilter').value = '';
        await loadRegionalManagers(warZone);
    });
    
    // 区域经理变化
    document.getElementById('regionalManagerFilter').addEventListener('change', (e) => {
        filters.regional_manager = e.target.value;
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
        searchEquipment();
    });
    
    clearStoreSearchBtn.addEventListener('click', () => {
        storeSearchInput.value = '';
        filters.store_search = '';
        clearStoreSearchBtn.style.display = 'none';
        currentPage = 1;
        searchEquipment();
    });
    
    storeSearchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            storeSearchBtn.click();
        }
    });
    
    // 搜索按钮
    document.getElementById('searchBtn').addEventListener('click', () => {
        currentPage = 1;
        searchEquipment();
    });
    
    // 清除筛选按钮
    document.getElementById('clearBtn').addEventListener('click', () => {
        document.getElementById('warZoneFilter').value = '';
        document.getElementById('regionalManagerFilter').value = '';
        document.getElementById('regionalManagerFilter').disabled = true;
        storeSearchInput.value = '';
        clearStoreSearchBtn.style.display = 'none';
        filters = {
            war_zone: '',
            regional_manager: '',
            store_search: ''
        };
        currentPage = 1;
        
        // 清空结果显示欢迎消息
        const container = document.getElementById('resultsContainer');
        container.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">🔧</div>
                <h2>欢迎使用设备异常监控系统</h2>
                <p>请选择筛选条件并点击"搜索"按钮查看设备异常</p>
            </div>
        `;
        document.getElementById('paginationContainer').style.display = 'none';
        document.getElementById('resultCount').textContent = '异常门店: 0';
    });
    
    // 导出按钮
    document.getElementById('exportBtn').addEventListener('click', exportEquipment);
    
    // 上一页
    document.getElementById('prevPage').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            searchEquipment();
        }
    });
    
    // 下一页
    document.getElementById('nextPage').addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            searchEquipment();
        }
    });
}

// 搜索设备异常
async function searchEquipment() {
    try {
        showLoading();
        
        // 构建查询参数
        const params = new URLSearchParams({
            page: currentPage,
            per_page: 20,
            ...filters
        });
        
        const response = await fetch(`${API_BASE_PATH}/api/equipment/search?${params}`);
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            totalPages = data.total_pages;
            
            // 更新统计信息
            document.getElementById('resultCount').textContent = `异常门店: ${data.total_stores}`;
            
            // 渲染门店列表
            renderEquipmentList(data.stores);
            
            // 更新分页
            if (data.total_stores > 0) {
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

// 渲染设备列表
function renderEquipmentList(stores) {
    const container = document.getElementById('resultsContainer');
    
    if (!stores || stores.length === 0) {
        container.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">📭</div>
                <h2>暂无设备异常数据</h2>
                <p>当前筛选条件下没有找到设备异常</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = stores.map(store => {
        // 按设备类型分组
        const posEquipment = store.equipment.filter(eq => eq.equipment_type === 'POS');
        const stbEquipment = store.equipment.filter(eq => eq.equipment_type === '机顶盒');
        
        return `
            <div class="store-card" data-store-id="${store.store_id}">
                <div class="store-header">
                    <div class="store-info">
                        <span class="store-name">${store.store_name}</span>
                        <span class="store-id">ID: ${store.store_id}</span>
                    </div>
                    <div class="store-meta">
                        <span class="badge badge-war-zone">${store.war_zone}</span>
                        <span class="badge badge-manager">${store.regional_manager}</span>
                        <span class="badge badge-count">${store.equipment.length}个设备异常</span>
                    </div>
                </div>
                <div class="store-body">
                    ${posEquipment.length > 0 ? `
                        <div class="equipment-group">
                            <div class="equipment-group-title">收银系统 (POS)</div>
                            <div class="equipment-list-items">
                                ${posEquipment.map(eq => `
                                    <div class="equipment-item-inline">
                                        <span class="equipment-status-badge">离线</span>
                                        <span class="equipment-name-text">${eq.equipment_name || eq.equipment_id}</span>
                                    </div>
                                `).join('')}
                            </div>
                            ${renderProcessingSection(store, 'POS', store.processing_pos)}
                        </div>
                    ` : ''}
                    ${stbEquipment.length > 0 ? `
                        <div class="equipment-group">
                            <div class="equipment-group-title">机顶盒</div>
                            <div class="equipment-list-items">
                                ${stbEquipment.map(eq => `
                                    <div class="equipment-item-inline">
                                        <span class="equipment-status-badge">离线</span>
                                        <span class="equipment-name-text">${eq.equipment_name || eq.equipment_id}</span>
                                    </div>
                                `).join('')}
                            </div>
                            ${renderProcessingSection(store, '机顶盒', store.processing_stb)}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
    
    // 绑定处理按钮事件
    bindProcessingEvents();
}

// 渲染处理区域
function renderProcessingSection(store, equipmentType, processing) {
    if (processing) {
        const p = processing;
        let badgeClass = 'status-processed';
        if (p.action === '未恢复') badgeClass = 'status-special';
        
        return `
            <div class="processing-status ${badgeClass}">
                <span class="status-label">${p.action}</span>
                ${p.reason ? `<span class="status-reason">: ${p.reason}</span>` : ''}
            </div>
            <div class="processing-time">处理时间: ${p.processed_at}</div>
        `;
    }
    
    return `
        <div class="processing-actions" data-equipment-type="${equipmentType}">
            <button class="action-btn btn-processed" data-action="已恢复">✓ 已恢复</button>
            <button class="action-btn btn-special">⚠ 未恢复原因</button>
        </div>
        <div class="reason-input-container" data-equipment-type="${equipmentType}" style="display:none;">
            <input type="text" class="reason-input" placeholder="请输入未恢复原因..." />
            <button class="reason-submit-btn">提交</button>
            <button class="reason-cancel-btn">取消</button>
        </div>
    `;
}

// 绑定处理按钮事件
function bindProcessingEvents() {
    // 已恢复按钮
    document.querySelectorAll('.action-btn[data-action]').forEach(btn => {
        btn.addEventListener('click', async function() {
            const card = this.closest('.store-card');
            const storeId = card.dataset.storeId;
            const action = this.dataset.action;
            const actionsDiv = this.closest('.processing-actions');
            const equipmentType = actionsDiv.dataset.equipmentType;
            
            await processEquipment(storeId, equipmentType, action, '');
        });
    });
    
    // 未恢复按钮
    document.querySelectorAll('.btn-special').forEach(btn => {
        btn.addEventListener('click', function() {
            const actionsDiv = this.closest('.processing-actions');
            const equipmentType = actionsDiv.dataset.equipmentType;
            const card = this.closest('.store-card');
            const reasonContainer = card.querySelector(`.reason-input-container[data-equipment-type="${equipmentType}"]`);
            
            actionsDiv.style.display = 'none';
            reasonContainer.style.display = 'flex';
            reasonContainer.querySelector('.reason-input').focus();
        });
    });
    
    // 提交理由按钮
    document.querySelectorAll('.reason-submit-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            const reasonContainer = this.closest('.reason-input-container');
            const equipmentType = reasonContainer.dataset.equipmentType;
            const reasonInput = reasonContainer.querySelector('.reason-input');
            const reason = reasonInput.value.trim();
            
            if (!reason) {
                showToast('请输入未恢复原因', 'error');
                return;
            }
            
            const card = this.closest('.store-card');
            const storeId = card.dataset.storeId;
            await processEquipment(storeId, equipmentType, '未恢复', reason);
        });
    });
    
    // 取消按钮
    document.querySelectorAll('.reason-cancel-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const reasonContainer = this.closest('.reason-input-container');
            const equipmentType = reasonContainer.dataset.equipmentType;
            const card = this.closest('.store-card');
            const actionsDiv = card.querySelector(`.processing-actions[data-equipment-type="${equipmentType}"]`);
            
            reasonContainer.style.display = 'none';
            actionsDiv.style.display = 'flex';
            reasonContainer.querySelector('.reason-input').value = '';
        });
    });
}

// 处理设备异常
async function processEquipment(storeId, equipmentType, action, reason) {
    try {
        const response = await fetch(`${API_BASE_PATH}/api/equipment/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                store_id: storeId,
                equipment_type: equipmentType,
                action: action,
                reason: reason
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('处理成功', 'success');
            // 重新加载当前页
            await searchEquipment();
        } else {
            throw new Error(result.error || '处理失败');
        }
    } catch (error) {
        console.error('处理失败:', error);
        showToast('处理失败，请重试', 'error');
    }
}

// 导出设备异常数据
function exportEquipment() {
    window.location.href = `${API_BASE_PATH}/api/equipment/export`;
}

// 显示加载中
function showLoading() {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">⏳</div>
            <h2>加载中...</h2>
            <p>正在获取设备异常数据</p>
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
            <p>${message}</p>
        </div>
    `;
}

// Toast提示
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast toast-${type} show`;
    
    setTimeout(() => {
        toast.className = 'toast';
    }, 3000);
}
