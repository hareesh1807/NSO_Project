#!/usr/bin/env python3


import paramiko
import time
from datetime import datetime


class NodeMonitor:
    
    
    def __init__(self, openstack_manager, bastion_ip, ssh_key):
        
        self.manager = openstack_manager
        self.bastion_ip = bastion_ip
        self.ssh_key = ssh_key
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    def connect_ssh(self, hostname, username='ubuntu'):
        
        try:
            self.ssh_client.connect(
                hostname,
                username=username,
                key_filename=self.ssh_key,
                timeout=10
            )
            return True
        except Exception as e:
            print(f"✗ Failed to connect to {hostname}: {e}")
            return False
    
    def disconnect_ssh(self):
        
        try:
            self.ssh_client.close()
        except:
            pass
    
    def get_cpu_load(self, hostname):
        
        try:
            if not self.connect_ssh(hostname):
                return None
            
            stdin, stdout, stderr = self.ssh_client.exec_command('uptime')
            output = stdout.read().decode('utf-8').strip()
            self.disconnect_ssh()
            
            return output
        except Exception as e:
            print(f"✗ Error getting CPU load from {hostname}: {e}")
            return None
    
    def get_memory_usage(self, hostname):
        
        try:
            if not self.connect_ssh(hostname):
                return None
            
            stdin, stdout, stderr = self.ssh_client.exec_command('free -h')
            output = stdout.read().decode('utf-8').strip()
            self.disconnect_ssh()
            
            return output
        except Exception as e:
            print(f"✗ Error getting memory from {hostname}: {e}")
            return None
    
    def get_disk_usage(self, hostname):
        
        try:
            if not self.connect_ssh(hostname):
                return None
            
            stdin, stdout, stderr = self.ssh_client.exec_command('df -h /')
            output = stdout.read().decode('utf-8').strip()
            self.disconnect_ssh()
            
            return output
        except Exception as e:
            print(f"✗ Error getting disk usage from {hostname}: {e}")
            return None
    
    def check_service_health(self, hostname, service_name='flask-service'):
        
        try:
            if not self.connect_ssh(hostname):
                return False
            
            stdin, stdout, stderr = self.ssh_client.exec_command(
                f'systemctl is-active {service_name}'
            )
            status = stdout.read().decode('utf-8').strip()
            self.disconnect_ssh()
            
            return status == 'active'
        except Exception as e:
            print(f"✗ Error checking service on {hostname}: {e}")
            return False
    
    def check_http_health(self, hostname, port=5000, endpoint='/health'):
        
        try:
            if not self.connect_ssh(hostname):
                return False
            
            stdin, stdout, stderr = self.ssh_client.exec_command(
                f'curl -s http://localhost:{port}{endpoint}'
            )
            output = stdout.read().decode('utf-8').strip()
            self.disconnect_ssh()
            
            return 'OK' in output or 'status' in output
        except Exception as e:
            print(f"✗ Error checking HTTP health on {hostname}: {e}")
            return False
    
    def monitor_node(self, node_name, node_ip):
       
        print(f"\n=== Monitoring {node_name} ({node_ip}) ===")
        
        # Check service
        service_ok = self.check_service_health(node_ip)
        print(f"Service status: {'✓ Running' if service_ok else '✗ Not running'}")
        
        # Check HTTP
        http_ok = self.check_http_health(node_ip)
        print(f"HTTP health: {'✓ Responding' if http_ok else '✗ Not responding'}")
        
        # Get metrics
        cpu = self.get_cpu_load(node_ip)
        if cpu:
            print(f"CPU Load: {cpu}")
        
        memory = self.get_memory_usage(node_ip)
        if memory:
            print(f"Memory:\n{memory}")
        
        disk = self.get_disk_usage(node_ip)
        if disk:
            print(f"Disk:\n{disk}")
        
        return service_ok and http_ok
    
    def monitor_all_nodes(self, nodes_info):
        """Monitor all nodes"""
        print(f"\n{'='*50}")
        print(f"Node Monitoring Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        
        results = {
            'service_nodes': [],
            'proxy_nodes': [],
            'bastion_nodes': []
        }
        
        # Monitor service nodes
        print("\n--- Service Nodes ---")
        for node in nodes_info.get('service_nodes', []):
            status = self.monitor_node(node['name'], node['ip'])
            results['service_nodes'].append({'name': node['name'], 'healthy': status})
        
        # Monitor proxy nodes
        print("\n--- Proxy Nodes ---")
        for node in nodes_info.get('proxy_nodes', []):
            status = self.monitor_node(node['name'], node['ip'])
            results['proxy_nodes'].append({'name': node['name'], 'healthy': status})
        
        # Monitor bastion nodes
        print("\n--- Bastion Nodes ---")
        for node in nodes_info.get('bastion_nodes', []):
            status = self.monitor_node(node['name'], node['ip'])
            results['bastion_nodes'].append({'name': node['name'], 'healthy': status})
        
       
        print(f"\n{'='*50}")
        print("Summary:")
        total = 0
        healthy = 0
        for node_type, nodes in results.items():
            for node in nodes:
                total += 1
                if node['healthy']:
                    healthy += 1
        
        print(f"Nodes: {healthy}/{total} healthy")
        if healthy == total:
            print("✓ All nodes are healthy!")
        else:
            print(f"⚠ {total - healthy} nodes need attention")
        print(f"{'='*50}\n")
        
        return results


if __name__ == "__main__":
    print("NodeMonitor module loaded")