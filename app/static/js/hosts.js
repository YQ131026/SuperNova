document.addEventListener('DOMContentLoaded', function() {
    // 初始化加载主机列表
    loadHosts();

    // 加载主机列表
    async function loadHosts() {
        try {
            const response = await fetch('/api/hosts');
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to load hosts');
            }
            
            console.log('Loaded hosts:', data.data);
            updateHostsList(data.data.hosts || []);
            
        } catch (error) {
            console.error('Error loading hosts:', error);
            showError('Failed to load hosts: ' + error.message);
        }
    }

    // 更新主机列表显示
    function updateHostsList(hosts) {
        const hostsList = document.getElementById('hosts-list');
        hostsList.innerHTML = '';
        
        if (!hosts || hosts.length === 0) {
            hostsList.innerHTML = '<tr><td colspan="6" class="text-center">No hosts found</td></tr>';
            return;
        }
        
        hosts.forEach(host => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${host.name}</td>
                <td>${host.ip}</td>
                <td>${host.port}</td>
                <td>${host.username || '-'}</td>
                <td>
                    <span class="badge bg-${host.status === 'connected' ? 'success' : 'danger'}">
                        ${host.status}
                    </span>
                </td>
                <td>
                    <div class="btn-group">
                        <a href="/services?host_id=${host.id}" class="btn btn-sm btn-primary">
                            <i class="bi bi-list-task"></i> 服务管理
                        </a>
                        <button class="btn btn-sm btn-warning" onclick="editHost('${host.id}')">
                            <i class="bi bi-pencil"></i> 编辑
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteHost('${host.id}')">
                            <i class="bi bi-trash"></i> 删除
                        </button>
                    </div>
                </td>
            `;
            hostsList.appendChild(row);
        });
    }

    // 显示错误消息
    function showError(message) {
        const errorAlert = document.getElementById('error-alert');
        if (errorAlert) {
            errorAlert.textContent = message;
            errorAlert.classList.remove('d-none');
            setTimeout(() => {
                errorAlert.classList.add('d-none');
            }, 5000);
        }
    }

    // 显示成功消息
    function showSuccess(message) {
        const successAlert = document.getElementById('success-alert');
        if (successAlert) {
            successAlert.textContent = message;
            successAlert.classList.remove('d-none');
            setTimeout(() => {
                successAlert.classList.add('d-none');
            }, 3000);
        }
    }

    // 定义全局的主机编辑函数
    window.editHost = async function(hostId) {
        try {
            // 获取主机信息
            const response = await fetch(`/api/hosts/${hostId}`);
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to get host info');
            }
            
            const host = data.data.host;
            
            // 获取表单元素
            const form = document.getElementById('edit-host-form');
            if (!form) {
                throw new Error('Edit form not found');
            }

            // 填充编辑表单
            const formElements = {
                'host_id': hostId,
                'name': host.name,
                'ip': host.ip,
                'port': host.port,
                'username': host.username
            };

            // 遍历设置表单值
            Object.entries(formElements).forEach(([key, value]) => {
                const element = form.querySelector(`[name="${key}"]`);
                if (element) {
                    element.value = value;
                }
            });
            
            // 显示编辑模态框
            const modalElement = document.getElementById('edit-host-modal');
            if (!modalElement) {
                throw new Error('Edit modal not found');
            }
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            
        } catch (error) {
            console.error('Error editing host:', error);
            showError('Failed to edit host: ' + error.message);
        }
    };

    // 处理编辑表单提交
    document.getElementById('edit-host-form')?.addEventListener('submit', async function(event) {
        event.preventDefault();
        
        const formData = new FormData(this);
        const hostId = formData.get('host_id');
        
        const hostData = {
            name: formData.get('name'),
            ip: formData.get('ip'),
            port: formData.get('port'),
            username: formData.get('username'),
            password: formData.get('password') // 如果密码为空，后端应保持原密码
        };

        try {
            const response = await fetch(`/api/hosts/${hostId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(hostData)
            });

            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to update host');
            }

            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('edit-host-modal'));
            modal.hide();
            
            // 刷新主机列表
            loadHosts();
            showSuccess('主机更新成功');
            
        } catch (error) {
            console.error('Error updating host:', error);
            showError('Failed to update host: ' + error.message);
        }
    });

    // 定义全局的主机删除函数
    window.deleteHost = async function(hostId) {
        if (!confirm('确定要删除这个主机吗？')) {
            return;
        }

        try {
            const response = await fetch(`/api/hosts/${hostId}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to delete host');
            }

            // 刷新主机列表
            loadHosts();
            showSuccess('主机删除成功');
            
        } catch (error) {
            console.error('Error deleting host:', error);
            showError('Failed to delete host: ' + error.message);
        }
    };
});