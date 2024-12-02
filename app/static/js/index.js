// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
    // 每30秒刷新一次数据
    setInterval(loadDashboard, 30000);
});

// 加载仪表盘数据
function loadDashboard() {
    fetch('/api/dashboard')
        .then(response => response.json())
        .then(data => {
            updateStatistics(data.statistics);
            updateHostList(data.hosts);
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('加载数据失败', 'danger');
        });
}

// 更新统计数据
function updateStatistics(stats) {
    document.getElementById('totalHosts').textContent = stats.total_hosts;
    document.getElementById('onlineHosts').textContent = stats.online_hosts;
    document.getElementById('runningServices').textContent = stats.running_services;
    document.getElementById('errorServices').textContent = stats.error_services;
}

// 更新主机列表
function updateHostList(hosts) {
    const hostList = document.getElementById('hostStatusList');
    hostList.innerHTML = '';

    hosts.forEach(host => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${host.name}</td>
            <td>${host.ip}:${host.port}</td>
            <td>${getStatusBadge(host.status)}</td>
            <td>${host.running_services}</td>
            <td>${host.error_services}</td>
            <td>
                <a href="/services/${host.id}" class="btn btn-sm btn-primary">
                    <i class="bi bi-list-task"></i> 服务
                </a>
            </td>
        `;
        hostList.appendChild(row);
    });
}

// 获取状态徽章
function getStatusBadge(status) {
    return status ? 
        '<span class="badge bg-success">在线</span>' : 
        '<span class="badge bg-danger">离线</span>';
}