document.addEventListener('DOMContentLoaded', function() {
    const hostSelect = document.getElementById('host-select');
    const refreshBtn = document.getElementById('refresh-btn');
    const processTableBody = document.getElementById('services-list');
    const errorAlert = document.getElementById('error-alert');
    const successAlert = document.getElementById('success-alert');

    // 检查DOM元素
    console.log('DOM Elements Check:', {
        hostSelect: !!hostSelect,
        refreshBtn: !!refreshBtn,
        processTableBody: !!processTableBody,
        errorAlert: !!errorAlert,
        successAlert: !!successAlert
    });

    if (!hostSelect || !refreshBtn || !processTableBody || !errorAlert || !successAlert) {
        console.error('Required DOM elements not found');
        return;
    }

    // 主机选择变更事件
    hostSelect.addEventListener('change', function() {
        console.log('Host selected:', this.value);
        if (this.value) {
            loadProcessList(this.value);
            refreshBtn.disabled = false;
        } else {
            clearProcessTable();
            refreshBtn.disabled = true;
        }
    });

    // 刷新按钮点击事件
    refreshBtn.addEventListener('click', function() {
        console.log('Refresh button clicked');
        const selectedHostId = hostSelect.value;
        console.log('Selected host ID:', selectedHostId);
        
        if (selectedHostId) {
            loadProcessList(selectedHostId);
            showSuccess('正在刷新服务列表...');
        } else {
            console.warn('No host selected when refresh clicked');
            showError('请先选择主机');
        }
    });

    // 加载进程列表
    async function loadProcessList(hostId) {
        try {
            console.log('Loading process list for host:', hostId);
            processTableBody.innerHTML = '<tr><td colspan="6" class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></td></tr>';
            
            const url = `/api/processes?host_id=${hostId}`;
            console.log('Fetching from URL:', url);
            
            const response = await fetch(url);
            console.log('Response status:', response.status);
            
            const data = await response.json();
            console.log('Raw API response:', data);
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to load processes');
            }

            // 从 data.data.processes 获取进程列表
            const processes = data.data?.processes;
            
            if (!processes) {
                console.error('Missing processes field in response:', data);
                throw new Error('Invalid response format: missing processes field');
            }

            if (!Array.isArray(processes)) {
                console.error('Processes is not an array:', typeof processes, processes);
                throw new Error('Invalid response format: processes is not an array');
            }

            console.log('Found processes:', processes);
            updateProcessTable(processes);
            
        } catch (error) {
            console.error('Error loading processes:', error);
            showError('Failed to load processes: ' + error.message);
            processTableBody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Failed to load processes</td></tr>';
        }
    }

    // 定义全局的进程控制函数
    window.controlProcess = async function(hostId, processName, action) {
        console.log(`Controlling process: ${processName}, action: ${action}, host: ${hostId}`);
        try {
            const response = await fetch('/api/processes/' + processName + '/' + action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ host_id: hostId })
            });

            const data = await response.json();
            console.log('Control process response:', data);

            if (!data.success) {
                throw new Error(data.error || `Failed to ${action} process`);
            }

            showSuccess(`Successfully ${action}ed ${processName}`);
            
            // 延迟刷新列表，让进程有时间改变状态
            setTimeout(() => {
                loadProcessList(hostId);
            }, 1000);

        } catch (error) {
            console.error(`Error ${action}ing process:`, error);
            showError(`Failed to ${action} process: ${error.message}`);
        }
    };

    // 更新进程表格
    function updateProcessTable(processes) {
        console.log('Updating process table with processes:', processes);
        processTableBody.innerHTML = '';
        
        if (!processes || processes.length === 0) {
            processTableBody.innerHTML = '<tr><td colspan="6" class="text-center">No processes found</td></tr>';
            return;
        }

        processes.forEach(process => {
            console.log('Processing process:', process);
            const row = document.createElement('tr');
            
            // 状态样式
            let statusBadge = '';
            switch (process.statename) {
                case 'RUNNING':
                    statusBadge = 'bg-success';
                    break;
                case 'STOPPED':
                    statusBadge = 'bg-danger';
                    break;
                default:
                    statusBadge = 'bg-secondary';
            }

            row.innerHTML = `
                <td>
                    <div class="form-check">
                        <input type="checkbox" class="form-check-input service-checkbox" value="${process.name}">
                    </div>
                </td>
                <td>${process.name}</td>
                <td><span class="badge ${statusBadge}">${process.statename}</span></td>
                <td>${process.description || '-'}</td>
                <td>${process.pid || '-'}</td>
                <td class="text-end">
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-sm btn-success" 
                                onclick="controlProcess('${hostSelect.value}', '${process.name}', 'start')" 
                                ${process.statename === 'RUNNING' ? 'disabled' : ''}>
                            <i class="bi bi-play-fill"></i> 启动
                        </button>
                        <button type="button" class="btn btn-sm btn-danger" 
                                onclick="controlProcess('${hostSelect.value}', '${process.name}', 'stop')" 
                                ${process.statename === 'STOPPED' ? 'disabled' : ''}>
                            <i class="bi bi-stop-fill"></i> 停止
                        </button>
                        <button type="button" class="btn btn-sm btn-warning" 
                                onclick="controlProcess('${hostSelect.value}', '${process.name}', 'restart')">
                            <i class="bi bi-arrow-clockwise"></i> 重启
                        </button>
                    </div>
                </td>
            `;
            processTableBody.appendChild(row);
        });
    }

    // 清空进程表格
    function clearProcessTable() {
        console.log('Clearing process table');
        processTableBody.innerHTML = '<tr><td colspan="6" class="text-center">请选择主机...</td></tr>';
    }

    // 显示错误消息
    function showError(message) {
        console.error('Error:', message);
        errorAlert.textContent = message;
        errorAlert.classList.remove('d-none');
        setTimeout(() => {
            errorAlert.classList.add('d-none');
        }, 5000);
    }

    // 显示成功消息
    function showSuccess(message) {
        console.log('Success:', message);
        successAlert.textContent = message;
        successAlert.classList.remove('d-none');
        setTimeout(() => {
            successAlert.classList.add('d-none');
        }, 3000);
    }

    // 初始化页面 - 如果有选中的主机，立即加载其服务列表
    console.log('Initializing services page');
    if (hostSelect.value) {
        console.log('Initial host selected:', hostSelect.value);
        loadProcessList(hostSelect.value);
        refreshBtn.disabled = false;
    } else {
        console.log('No initial host selected');
        clearProcessTable();
        refreshBtn.disabled = true;
    }
});