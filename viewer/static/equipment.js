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
let displayMode = 'card'; // 'card' 或 'list'
let listFilterStatus = 'all'; // 'all', 'pending', 'recovered', 'not_recovered' - 列表模式的筛选状态

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
        showFirstVisitNotice();
        console.log('✅ 设备异常监控页面初始化完成');
    } catch (error) {
        console.error('❌ 页面初始化失败:', error);
        showToast('页面初始化失败，请刷新重试', 'error');
    }
}

// 首次访问弹窗通知（每个IP/浏览器首次打开时弹出，强制阅读3秒）
function showFirstVisitNotice() {
    const today = new Date().toISOString().split('T')[0];
    const noticeKey = `equipment_notice_v2_${today}`;
    if (localStorage.getItem(noticeKey)) return;

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.style.zIndex = '9999';
    overlay.innerHTML = `
        <div class="modal-dialog" style="max-width:480px;">
            <div class="modal-header">
                <h3>📢 收银系统检查须知</h3>
            </div>
            <div class="modal-body" style="font-size:14px;line-height:1.8;">
                <p>请提醒门店注意以下事项：</p>
                <ul style="padding-left:20px;margin:10px 0;">
                    <li>收银系统（平板）要保持<b>常亮</b>且停留在收银页面</li>
                    <li><b>息屏会导致收银系统离线</b>，无法正常接单</li>
                    <li>如有平板损坏等特殊情况，请提醒门店尽快修理、更换</li>
                </ul>
                <p>处理说明：</p>
                <ul style="padding-left:20px;margin:10px 0;">
                    <li>请沟通门店重启机顶盒、打开平板确保收银系统在最前展示</li>
                    <li>特殊情况选择"未恢复"后须填写<b>预计恢复日期</b>（最长7天）</li>
                    <li>恢复期内该门店免查</li>
                </ul>
            </div>
            <div style="margin-top:12px;padding:10px 14px;background:#fff3cd;border-left:3px solid #ffc107;border-radius:4px;font-size:13px;color:#856404;">
                ⚠️ 下午还离线的话就发警告单了！
            </div>
            <div class="modal-footer">
                <button id="noticeCloseBtn" class="btn btn-primary" disabled style="min-width:120px;">
                    请阅读 (<span id="noticeCountdown">3</span>s)
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    let remaining = 3;
    const countdownEl = document.getElementById('noticeCountdown');
    const closeBtn = document.getElementById('noticeCloseBtn');

    const timer = setInterval(() => {
        remaining--;
        if (remaining > 0) {
            countdownEl.textContent = remaining;
        } else {
            clearInterval(timer);
            closeBtn.disabled = false;
            closeBtn.textContent = '我已知晓';
            closeBtn.style.cursor = 'pointer';
        }
    }, 1000);

    closeBtn.addEventListener('click', () => {
        if (closeBtn.disabled) return;
        overlay.remove();
        localStorage.setItem(noticeKey, Date.now().toString());
    });
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
            
            // 显示数据更新时间
            if (data.data_time) {
                const dataUpdateTimeDiv = document.getElementById('dataUpdateTime');
                const dataTimeText = document.getElementById('dataTimeText');
                dataTimeText.textContent = data.data_time;
                dataUpdateTimeDiv.style.display = 'block';
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
        const response = await fetch(`${API_BASE_PATH}/api/equipment/all-regional-managers`);
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
        
        const response = await fetch(`${API_BASE_PATH}/api/equipment/regional-managers?war_zone=${encodeURIComponent(warZone)}`);
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
    document.getElementById('promoTab').addEventListener('click', () => {
        window.location.href = '/promoratio';
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
        storeSearchInput.value = '';
        clearStoreSearchBtn.style.display = 'none';
        filters = {
            war_zone: '',
            regional_manager: '',
            store_search: ''
        };
        currentPage = 1;
        listFilterStatus = 'all'; // 重置列表筛选状态
        
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
        
        // 判断显示模式：如果没有选择区域经理，使用列表模式
        displayMode = filters.regional_manager ? 'card' : 'list';
        
        // 构建查询参数
        const params = new URLSearchParams({
            page: currentPage,
            per_page: 20,
            ...filters
        });
        
        // 如果是列表模式且有状态筛选，添加状态筛选参数
        if (displayMode === 'list' && listFilterStatus !== 'all') {
            params.append('status_filter', listFilterStatus);
        }
        
        const response = await fetch(`${API_BASE_PATH}/api/equipment/search?${params}`);
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            totalPages = data.total_pages;
            
            // 更新统计信息 - 显示筛选后的数量
            const displayCount = listFilterStatus !== 'all' && data.filtered_total !== undefined ? data.filtered_total : data.total_stores;
            document.getElementById('resultCount').textContent = `异常门店: ${displayCount}`;
            
            // 根据模式渲染
            if (displayMode === 'list') {
                renderEquipmentListMode(data.stores, data.total_stores, data.total_pending, data.total_processed, data.total_recovered, data.total_not_recovered, data.total_chronic, data.filtered_total);
            } else {
                renderEquipmentList(data.stores);
            }
            
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
        
        // 经常出问题标记（仅POS）
        const chronicBadge = store.is_chronic ? `<span class="chronic-badge" title="5天${store.abnormal_count_5days}次 / 10天${store.abnormal_count_10days}次">🔴 ${store.chronic_reason}</span>` : '';
        
        return `
            <div class="store-card-horizontal ${store.is_chronic ? 'chronic-store' : ''}" data-store-id="${store.store_id}">
                <!-- 左侧：门店信息 -->
                <div class="store-info-section">
                    <div class="store-name-compact">${store.store_name} <span class="store-id-tag">${store.store_id}</span> ${chronicBadge}</div>
                    <div class="store-meta-inline">
                        <span class="meta-item">${store.war_zone}</span>
                        <span class="meta-item">${store.regional_manager}</span>
                        <span class="meta-badge">${store.equipment.length}个异常</span>
                    </div>
                </div>
                
                <!-- 中间：设备信息 -->
                <div class="equipment-info-section">
                    ${posEquipment.length > 0 ? `
                        <div class="equipment-row">
                            <span class="equipment-type-label">🖥️ POS:</span>
                            <div class="equipment-items-inline">
                                ${posEquipment.map(eq => `<span class="equipment-chip">${eq.equipment_name || eq.equipment_id}</span>`).join('')}
                            </div>
                        </div>
                    ` : ''}
                    ${stbEquipment.length > 0 ? `
                        <div class="equipment-row">
                            <span class="equipment-type-label">📺 机顶盒:</span>
                            <div class="equipment-items-inline">
                                ${stbEquipment.map(eq => `<span class="equipment-chip">${eq.equipment_name || eq.equipment_id}</span>`).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
                
                <!-- 右侧：操作按钮 -->
                <div class="actions-section">
                    ${posEquipment.length > 0 ? renderCompactActions(store, 'POS', store.processing_pos) : ''}
                    ${stbEquipment.length > 0 ? renderCompactActions(store, '机顶盒', store.processing_stb) : ''}
                </div>
            </div>
        `;
    }).join('');
    
    // 绑定处理按钮事件
    bindProcessingEvents();
}

// 渲染紧凑型操作按钮
function renderCompactActions(store, equipmentType, processing) {
    if (processing) {
        const badgeClass = processing.action === '未恢复' ? 'status-warning' : 'status-success';
        return `
            <div class="action-group" data-equipment-type="${equipmentType}">
                <div class="status-compact ${badgeClass}">
                    ${processing.action === '已恢复' ? '✓' : '⚠'} ${processing.action}${processing.reason ? ': ' + processing.reason : ''}
                </div>
                <button class="btn-edit-compact" data-equipment-type="${equipmentType}">✏️</button>
            </div>
            <div class="action-buttons-compact" data-equipment-type="${equipmentType}" style="display:none;">
                <button class="btn-action-compact btn-success" data-action="已恢复">✓</button>
                <button class="btn-action-compact btn-warning">⚠</button>
            </div>
            <div class="reason-input-compact" data-equipment-type="${equipmentType}" style="display:none;">
                <input type="text" class="input-reason-compact" placeholder="原因..." value="${processing.reason || ''}" />
                <button class="btn-submit-compact">✓</button>
                <button class="btn-cancel-compact">✕</button>
            </div>
        `;
    }
    
    return `
        <div class="action-group" data-equipment-type="${equipmentType}">
            <div class="action-buttons-compact" data-equipment-type="${equipmentType}">
                <button class="btn-action-compact btn-success" data-action="已恢复">✓ 已恢复</button>
                <button class="btn-action-compact btn-warning">⚠ 未恢复</button>
            </div>
            <div class="reason-input-compact" data-equipment-type="${equipmentType}" style="display:none;">
                <input type="text" class="input-reason-compact" placeholder="原因..." />
                <button class="btn-submit-compact">✓</button>
                <button class="btn-cancel-compact">✕</button>
            </div>
        </div>
    `;
}

// 渲染列表模式（战区/领导查看）
function renderEquipmentListMode(stores, totalStoresCount, totalPending, totalProcessed, totalRecovered, totalNotRecovered, totalChronic, filteredTotal) {
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
    
    // 使用后端返回的准确统计数据
    const totalStores = totalStoresCount || stores.length;
    const pendingStores = totalPending !== undefined ? totalPending : stores.filter(s => !s.processing_pos && !s.processing_stb).length;
    const completedStores = totalProcessed !== undefined ? totalProcessed : (totalStores - pendingStores);
    const recoveredStores = totalRecovered !== undefined ? totalRecovered : 0;
    const notRecoveredStores = totalNotRecovered !== undefined ? totalNotRecovered : 0;
    const chronicStores = totalChronic !== undefined ? totalChronic : 0;
    
    let html = `
        <div class="list-mode-container">
            <div class="summary-section">
                <div class="summary-title">
                    📊 处理进度概览
                    ${listFilterStatus !== 'all' ? '<button class="clear-filter-btn" onclick="clearListFilter()">✕ 清除筛选</button>' : ''}
                </div>
                <div class="summary-stats">
                    <div class="stat-item clickable ${listFilterStatus === 'all' ? 'active' : ''}" onclick="filterListByStatus('all')">
                        <div class="stat-number">${totalStores}</div>
                        <div class="stat-label">异常门店总数</div>
                    </div>
                    <div class="stat-item pending clickable ${listFilterStatus === 'pending' ? 'active' : ''}" onclick="filterListByStatus('pending')">
                        <div class="stat-number">${pendingStores}</div>
                        <div class="stat-label">待处理门店</div>
                    </div>
                    <div class="stat-item completed clickable ${listFilterStatus === 'recovered' || listFilterStatus === 'not_recovered' ? 'active' : ''}">
                        <div class="stat-number">${completedStores}</div>
                        <div class="stat-label">已处理门店</div>
                        <div class="stat-detail">
                            <span class="detail-item recovered clickable ${listFilterStatus === 'recovered' ? 'active' : ''}" onclick="event.stopPropagation(); filterListByStatus('recovered')">✓ 已恢复: ${recoveredStores}</span>
                            <span class="detail-item not-recovered clickable ${listFilterStatus === 'not_recovered' ? 'active' : ''}" onclick="event.stopPropagation(); filterListByStatus('not_recovered')">⚠ 未恢复: ${notRecoveredStores}</span>
                        </div>
                    </div>
                    ${chronicStores > 0 ? `
                    <div class="stat-item chronic clickable ${listFilterStatus === 'chronic' ? 'active' : ''}" onclick="filterListByStatus('chronic')">
                        <div class="stat-number">${chronicStores}</div>
                        <div class="stat-label">经常出问题</div>
                    </div>
                    ` : ''}
                </div>
                ${listFilterStatus !== 'all' ? `<div class="filter-hint">📌 当前显示: ${getFilterStatusText()} (共 ${filteredTotal !== undefined ? filteredTotal : stores.length} 家门店，第 ${currentPage} / ${totalPages} 页)</div>` : ''}
            </div>
    `;
    
    // 渲染门店列表（后端已经过滤，直接显示）
    stores.forEach(store => {
        const posEquipment = store.equipment.filter(eq => eq.equipment_type === 'POS');
        const stbEquipment = store.equipment.filter(eq => eq.equipment_type === '机顶盒');
        const isPending = !store.processing_pos && !store.processing_stb;
        
        html += `
            <div class="store-list-item">
                <div class="store-list-header">
                    <div class="store-list-info">
                        <div class="store-list-name">${store.store_name} <span class="store-id-tag">${store.store_id}</span></div>
                        <div class="store-list-meta">${store.war_zone} · ${store.regional_manager} · ID: ${store.store_id}</div>
                    </div>
                    <div class="store-list-status">
                        <span class="status-badge ${isPending ? 'pending' : 'completed'}">
                            ${isPending ? '待处理' : '已处理'}
                        </span>
                    </div>
                </div>
                <div class="store-list-equipment">
                    ${posEquipment.length > 0 ? `
                        <div class="equipment-type-section">
                            <div class="equipment-type-header">
                                <span class="equipment-type-title">🖥️ 收银系统 (POS)</span>
                                <span class="equipment-count">${posEquipment.length}台离线</span>
                            </div>
                            <div class="equipment-compact-list">
                                ${posEquipment.map(eq => `
                                    <span class="equipment-compact-item">${eq.equipment_name || eq.equipment_id}</span>
                                `).join('')}
                            </div>
                            ${store.processing_pos ? `
                                <div style="margin-top: 6px; font-size: 11px; color: #28a745;">
                                    ✓ ${store.processing_pos.action}${store.processing_pos.reason ? ': ' + store.processing_pos.reason : ''}
                                </div>
                            ` : ''}
                        </div>
                    ` : ''}
                    ${stbEquipment.length > 0 ? `
                        <div class="equipment-type-section">
                            <div class="equipment-type-header">
                                <span class="equipment-type-title">📺 机顶盒</span>
                                <span class="equipment-count">${stbEquipment.length}台离线</span>
                            </div>
                            <div class="equipment-compact-list">
                                ${stbEquipment.map(eq => `
                                    <span class="equipment-compact-item">${eq.equipment_name || eq.equipment_id}</span>
                                `).join('')}
                            </div>
                            ${store.processing_stb ? `
                                <div style="margin-top: 6px; font-size: 11px; color: #28a745;">
                                    ✓ ${store.processing_stb.action}${store.processing_stb.reason ? ': ' + store.processing_stb.reason : ''}
                                </div>
                            ` : ''}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    });
    
    html += `</div>`;
    container.innerHTML = html;
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
                <button class="edit-processing-btn" data-equipment-type="${equipmentType}">✏️ 修改</button>
            </div>
            <div class="processing-time">处理时间: ${p.processed_at}</div>
            <div class="processing-actions" data-equipment-type="${equipmentType}" style="display:none;">
                <button class="action-btn btn-processed" data-action="已恢复">✓ 已恢复</button>
                <button class="action-btn btn-special">⚠ 未恢复原因</button>
            </div>
            <div class="reason-input-container" data-equipment-type="${equipmentType}" style="display:none;">
                <input type="text" class="reason-input" placeholder="请输入未恢复原因..." value="${p.reason || ''}" />
                <button class="reason-submit-btn">提交</button>
                <button class="reason-cancel-btn">取消</button>
            </div>
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
    // 修改按钮（已处理状态下显示）
    document.querySelectorAll('.btn-edit-compact').forEach(btn => {
        btn.addEventListener('click', function() {
            const equipmentType = this.dataset.equipmentType;
            const card = this.closest('.store-card-horizontal');
            const actionGroup = this.closest('.action-group');
            const actionsDiv = card.querySelector(`.action-buttons-compact[data-equipment-type="${equipmentType}"]`);
            
            actionGroup.style.display = 'none';
            actionsDiv.style.display = 'flex';
        });
    });
    
    // 已恢复按钮
    document.querySelectorAll('.btn-action-compact[data-action]').forEach(btn => {
        btn.addEventListener('click', async function() {
            const card = this.closest('.store-card-horizontal');
            const storeId = card.dataset.storeId;
            const action = this.dataset.action;
            const actionsDiv = this.closest('.action-buttons-compact');
            const equipmentType = actionsDiv.dataset.equipmentType;
            
            await processEquipment(storeId, equipmentType, action, '');
        });
    });
    
    // 未恢复原因按钮
    document.querySelectorAll('.btn-action-compact:not([data-action])').forEach(btn => {
        btn.addEventListener('click', function() {
            const actionsDiv = this.closest('.action-buttons-compact');
            const equipmentType = actionsDiv.dataset.equipmentType;
            const card = this.closest('.store-card-horizontal');
            const storeId = card.dataset.storeId;
            
            // 显示预计恢复日期弹窗
            showExpectedRecoveryDialog(storeId, equipmentType, '');
        });
    });
    
    // 提交理由按钮
    document.querySelectorAll('.btn-submit-compact').forEach(btn => {
        btn.addEventListener('click', async function() {
            const reasonContainer = this.closest('.reason-input-compact');
            const equipmentType = reasonContainer.dataset.equipmentType;
            const reasonInput = reasonContainer.querySelector('.input-reason-compact');
            const reason = reasonInput.value.trim();
            
            if (!reason) {
                showToast('请输入未恢复原因', 'error');
                return;
            }
            
            const card = this.closest('.store-card-horizontal');
            const storeId = card.dataset.storeId;
            
            // 显示预计恢复日期弹窗
            showExpectedRecoveryDialog(storeId, equipmentType, reason);
        });
    });
    
    // 取消按钮
    document.querySelectorAll('.btn-cancel-compact').forEach(btn => {
        btn.addEventListener('click', function() {
            const reasonContainer = this.closest('.reason-input-compact');
            const equipmentType = reasonContainer.dataset.equipmentType;
            const card = this.closest('.store-card-horizontal');
            const actionsDiv = card.querySelector(`.action-buttons-compact[data-equipment-type="${equipmentType}"]`);
            const actionGroup = card.querySelector(`.action-group[data-equipment-type="${equipmentType}"]`);
            
            reasonContainer.style.display = 'none';
            
            // 如果有已处理状态，显示状态；否则显示操作按钮
            if (actionGroup && actionGroup.querySelector('.status-compact')) {
                actionGroup.style.display = 'flex';
            } else {
                actionsDiv.style.display = 'flex';
            }
        });
    });
}

// 处理设备异常
async function processEquipment(storeId, equipmentType, action, reason, expectedRecoveryDate = null) {
    try {
        const requestBody = {
            store_id: storeId,
            equipment_type: equipmentType,
            action: action,
            reason: reason
        };
        
        // 如果有预计恢复日期，添加到请求体
        if (expectedRecoveryDate) {
            requestBody.expected_recovery_date = expectedRecoveryDate;
        }
        
        const response = await fetch(`${API_BASE_PATH}/api/equipment/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
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

// 列表模式筛选功能
function filterListByStatus(status) {
    listFilterStatus = status;
    currentPage = 1; // 重置到第一页
    // 重新搜索以刷新列表
    searchEquipment();
}

function clearListFilter() {
    listFilterStatus = 'all';
    currentPage = 1; // 重置到第一页
    searchEquipment();
}

function getFilterStatusText() {
    const statusMap = {
        'all': '全部门店',
        'pending': '待处理门店',
        'recovered': '已恢复门店',
        'not_recovered': '未恢复门店',
        'chronic': '经常出问题'
    };
    return statusMap[listFilterStatus] || '全部门店';
}

// 显示预计恢复日期弹窗
function showExpectedRecoveryDialog(storeId, equipmentType, currentReason = '') {
    const dialog = document.createElement('div');
    dialog.className = 'modal-overlay';
    dialog.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-header">
                <h3>⚠ 设备未恢复</h3>
                <button class="modal-close-btn" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>未恢复原因: <span class="required">*</span></label>
                    <textarea id="recoveryReason" class="form-control" rows="3" placeholder="请输入未恢复原因...">${currentReason}</textarea>
                </div>
                <div class="form-group">
                    <label>预计恢复日期: (可选)</label>
                    <input type="date" id="expectedRecoveryDate" class="form-control" 
                           min="${getToday()}" max="${getMaxRecoveryDate()}">
                    <small class="form-text">填写后，在此日期前不会再次提示异常</small>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeModal()">取消</button>
                <button class="btn btn-primary" onclick="submitRecovery('${storeId}', '${equipmentType}')">提交</button>
            </div>
        </div>
    `;
    document.body.appendChild(dialog);
}

// 关闭弹窗
function closeModal() {
    const modal = document.querySelector('.modal-overlay');
    if (modal) {
        modal.remove();
    }
}

// 获取今天的日期字符串
function getToday() {
    const today = new Date();
    return today.toISOString().split('T')[0];
}

// 获取最大恢复日期（今天+7天）
function getMaxRecoveryDate() {
    const maxDate = new Date();
    maxDate.setDate(maxDate.getDate() + 7);
    return maxDate.toISOString().split('T')[0];
}

// 提交恢复信息
async function submitRecovery(storeId, equipmentType) {
    const reason = document.getElementById('recoveryReason').value.trim();
    const expectedDate = document.getElementById('expectedRecoveryDate').value;
    
    if (!reason) {
        showToast('请输入未恢复原因', 'error');
        return;
    }
    
    await processEquipment(storeId, equipmentType, '未恢复', reason, expectedDate);
    closeModal();
}
