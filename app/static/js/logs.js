document.addEventListener('DOMContentLoaded', function() {
    const hostSelect = document.getElementById('host-select');
    const processSelect = document.getElementById('process-select');
    const logTypeSelect = document.getElementById('log-type');
    const logContent = document.getElementById('log-content');
    const refreshBtn = document.getElementById('refresh-btn');
    const tailCheckbox = document.getElementById('tail-checkbox');
    const errorAlert = document.getElementById('error-alert');
    const successAlert = document.getElementById('success-alert');
    
    let currentLogData = '';
    let autoRefreshInterval;

    // 检查必要的DOM元素
    if (!hostSelect || !processSelect || !logTypeSelect || !logContent || 
        !refreshBtn || !tailCheckbox || !errorAlert || !successAlert) {
        console.error('Required DOM elements not found');
        return;
    }

    // 主机选择变更时加载进程列表
    hostSelect.addEventListener('change', function() {
        if (this.value) {
            loadProcesses(this.value);
            processSelect.disabled = false;
        } else {
            processSelect.innerHTML = '<option value="">请选择进程...</option>';
            processSelect.disabled = true;
            logTypeSelect.disabled = true;
            refreshBtn.disabled = true;
            tailCheckbox.disabled = true;
            clearLog();
        }
    });

    // 进程选择变更时加载日志
    processSelect.addEventListener('change', function() {
        if (this.value) {
            logTypeSelect.disabled = false;
            refreshBtn.disabled = false;
            tailCheckbox.disabled = false;
            fetchLogs();
        } else {
            logTypeSelect.disabled = true;
            refreshBtn.disabled = true;
            tailCheckbox.disabled = true;
            clearLog();
        }
    });

    // 日志类型变更时重新加载日志
    logTypeSelect.addEventListener('change', fetchLogs);

    // 刷新按钮点击事件
    refreshBtn.addEventListener('click', fetchLogs);

    // 自动刷新切换
    tailCheckbox.addEventListener('change', function() {
        if (this.checked) {
            autoRefreshInterval = setInterval(fetchLogs, 5000);
        } else {
            clearInterval(autoRefreshInterval);
        }
    });

    // 加载进程列表
    async function loadProcesses(hostId) {
        if (!hostId) {
            processSelect.innerHTML = '<option value="">请选择进程...</option>';
            return;
        }

        try {
            const response = await fetch(`/api/processes?host_id=${hostId}`);
            const data = await response.json();
            console.log('Processes response:', data);

            if (data.success) {
                processSelect.innerHTML = '<option value="">请选择进程...</option>';
                const processes = data.data?.processes;
                
                if (!processes) {
                    throw new Error('No processes data received');
                }

                processes.forEach(process => {
                    const option = document.createElement('option');
                    option.value = process.name;
                    option.textContent = `${process.name} (${process.statename})`;
                    processSelect.appendChild(option);
                });
            } else {
                throw new Error(data.error || 'Failed to load processes');
            }
        } catch (error) {
            console.error('Error loading processes:', error);
            showError('Failed to load processes: ' + error.message);
            processSelect.innerHTML = '<option value="">加载失败</option>';
        }
    }

    // 获取日志内容
    async function fetchLogs() {
        const hostId = hostSelect.value;
        const processName = processSelect.value;
        const logType = logTypeSelect.value;

        if (!hostId || !processName) {
            return;
        }

        try {
            const response = await fetch(`/api/logs/${processName}?host_id=${hostId}&type=${logType}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Log response:', data);  // 添加调试日志

            if (data.success) {
                currentLogData = data.data.content;
                logContent.textContent = currentLogData || 'No logs available';
                logContent.scrollTop = logContent.scrollHeight;
            } else {
                throw new Error(data.error || 'Failed to fetch logs');
            }
        } catch (error) {
            console.error('Error fetching logs:', error);
            showError(`Failed to fetch logs: ${error.message}`);
            logContent.textContent = 'Failed to load logs';
        }
    }

    // 清空日志显示
    function clearLog() {
        currentLogData = '';
        logContent.textContent = '';
    }

    // 下载日志文件
    function downloadLog() {
        if (!currentLogData) {
            return;
        }

        const hostId = hostSelect.value;
        const processName = processSelect.value;
        const logType = logTypeSelect.value;
        const filename = `${processName}_${logType}.log`;

        const blob = new Blob([currentLogData], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    // 显示错误信息
    function showError(message) {
        console.error('Error:', message);
        errorAlert.textContent = message;
        errorAlert.classList.remove('d-none');
        setTimeout(() => {
            errorAlert.classList.add('d-none');
        }, 5000);
    }
});