import os
import shutil
import yaml
from datetime import datetime
import logging

class ConfigBackup:
    def __init__(self, app):
        self.app = app
        self.config_dir = os.path.join(app.root_path, '..', 'config')
        self.backup_dir = os.path.join(app.root_path, '..', 'config_backups')
        self.ensure_backup_directory()

    def ensure_backup_directory(self):
        """确保备份目录存在"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def create_backup(self):
        """创建配置文件备份"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(self.backup_dir, f'hosts_{timestamp}.yaml')
            
            # 复制配置文件
            shutil.copy2(
                os.path.join(self.config_dir, 'hosts.yaml'),
                backup_path
            )
            
            # 记录备份信息
            self.app.logger.info(f"Configuration backup created: {backup_path}")
            return True
        except Exception as e:
            self.app.logger.error(f"Backup creation failed: {e}")
            return False

    def list_backups(self):
        """列出所有备份"""
        backups = []
        for file in os.listdir(self.backup_dir):
            if file.startswith('hosts_') and file.endswith('.yaml'):
                path = os.path.join(self.backup_dir, file)
                backups.append({
                    'filename': file,
                    'timestamp': datetime.fromtimestamp(os.path.getctime(path)),
                    'size': os.path.getsize(path)
                })
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)

    def restore_backup(self, backup_filename):
        """从备份恢复配置"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            if not os.path.exists(backup_path):
                raise FileNotFoundError("Backup file not found")

            # 创建当前配置的备份
            self.create_backup()

            # 恢复选定的备份
            shutil.copy2(
                backup_path,
                os.path.join(self.config_dir, 'hosts.yaml')
            )

            self.app.logger.info(f"Configuration restored from: {backup_filename}")
            return True
        except Exception as e:
            self.app.logger.error(f"Restore failed: {e}")
            return False

    def cleanup_old_backups(self, keep_days=30):
        """清理旧备份"""
        try:
            cutoff = datetime.now().timestamp() - (keep_days * 24 * 3600)
            for file in os.listdir(self.backup_dir):
                path = os.path.join(self.backup_dir, file)
                if os.path.getctime(path) < cutoff:
                    os.remove(path)
                    self.app.logger.info(f"Removed old backup: {file}")
        except Exception as e:
            self.app.logger.error(f"Backup cleanup failed: {e}")