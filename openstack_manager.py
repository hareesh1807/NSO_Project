#!/usr/bin/env python3

#Handles all OpenStack API interactions for VM creation, deletion, and management


import sys
import time
from openstack import connection
from config import ConfigParser


class OpenStackManager:
    
    
    def __init__(self, rc_file, tag):
        
        self.rc_file = rc_file
        self.tag = tag
        self.config_parser = ConfigParser(rc_file, 'servers.conf')
        self.conn = None
        self.project_id = None
        
    def connect(self):
        
        try:
           
            self.config_parser.parse_rc_file()
            os_config = self.config_parser.get_openstack_env()
            
           
            self.conn = connection.Connection(
                auth_url=os_config.get('OS_AUTH_URL'),
                project_name=os_config.get('OS_PROJECT_NAME'),
                username=os_config.get('OS_USERNAME'),
                password=os_config.get('OS_PASSWORD'),
                user_domain_name=os_config.get('OS_USER_DOMAIN_NAME', 'Default'),
                project_domain_name=os_config.get('OS_PROJECT_DOMAIN_NAME', 'Default'),
                region_name=os_config.get('OS_REGION_NAME', 'RegionOne'),
                verify=False
            )
            
            print(f"✓ Connected to OpenStack")
            return True
        
        except Exception as e:
            print(f"✗ Failed to connect to OpenStack: {e}")
            return False
    
    def create_network(self, network_name):
        
        try:
            
            network = self.conn.network.find_network(network_name, ignore_missing=True)
            if network:
                print(f"✓ Network '{network_name}' already exists")
                return network
            
            
            network = self.conn.network.create_network(name=network_name)
            print(f"✓ Created network: {network_name}")
            return network
        
        except Exception as e:
            print(f"✗ Failed to create network: {e}")
            return None
    
    def create_subnet(self, subnet_name, network_id, cidr='192.168.1.0/24'):
        
        try:
            
            subnet = self.conn.network.find_subnet(subnet_name, ignore_missing=True)
            if subnet:
                print(f"✓ Subnet '{subnet_name}' already exists")
                return subnet
            
            
            subnet = self.conn.network.create_subnet(
                name=subnet_name,
                network_id=network_id,
                cidr=cidr,
                ip_version=4
            )
            print(f"✓ Created subnet: {subnet_name} ({cidr})")
            return subnet
        
        except Exception as e:
            print(f"✗ Failed to create subnet: {e}")
            return None
    
    def create_router(self, router_name, subnet_id, external_network_name='public'):
       
        try:
            
            router = self.conn.network.find_router(router_name, ignore_missing=True)
            if router:
                print(f"✓ Router '{router_name}' already exists")
                return router
            
           
            external_network = self.conn.network.find_network(
                external_network_name,
                ignore_missing=True
            )
            
            if not external_network:
                print(f"✗ External network '{external_network_name}' not found")
                return None
            
            
            router = self.conn.network.create_router(
                name=router_name,
                external_gateway_info={
                    'network_id': external_network.id
                }
            )
            
            
            self.conn.network.add_router_interface(
                router,
                subnet_id=subnet_id
            )
            
            print(f"✓ Created router: {router_name}")
            return router
        
        except Exception as e:
            print(f"✗ Failed to create router: {e}")
            return None
    
    def create_security_group(self, sg_name):
        
        try:
           
            sg = self.conn.network.find_security_group(sg_name, ignore_missing=True)
            if sg:
                print(f"✓ Security group '{sg_name}' already exists")
                return sg
            
            
            sg = self.conn.network.create_security_group(
                name=sg_name,
                description=f"Security group for {self.tag}"
            )
            
            
            rules = [
                {
                    'direction': 'ingress',
                    'ethertype': 'IPv4',
                    'protocol': 'tcp',
                    'port_range_min': 22,
                    'port_range_max': 22,
                    'remote_ip_prefix': '0.0.0.0/0'
                },
                {
                    'direction': 'ingress',
                    'ethertype': 'IPv4',
                    'protocol': 'tcp',
                    'port_range_min': 80,
                    'port_range_max': 80,
                    'remote_ip_prefix': '0.0.0.0/0'
                },
                {
                    'direction': 'ingress',
                    'ethertype': 'IPv4',
                    'protocol': 'icmp',
                    'remote_ip_prefix': '0.0.0.0/0'
                }
            ]
            
            for rule in rules:
                self.conn.network.create_security_group_rule(
                    security_group_id=sg.id,
                    **rule
                )
            
            print(f"✓ Created security group: {sg_name}")
            return sg
        
        except Exception as e:
            print(f"✗ Failed to create security group: {e}")
            return None
    
    def create_instance(self, name, image_name, flavor_name, network_id, sg_id, key_name):
        
        try:
            
            instance = self.conn.compute.find_server(name, ignore_missing=True)
            if instance:
                print(f"✓ Instance '{name}' already exists")
                return instance
            
            
            image = self.conn.compute.find_image(image_name, ignore_missing=True)
            if not image:
                print(f"✗ Image '{image_name}' not found")
                return None
            
            
            flavor = self.conn.compute.find_flavor(flavor_name, ignore_missing=True)
            if not flavor:
                print(f"✗ Flavor '{flavor_name}' not found")
                return None
            
            
            instance = self.conn.compute.create_server(
                name=name,
                image_id=image.id,
                flavor_id=flavor.id,
                networks=[{'uuid': network_id}],
                key_name=key_name,
                security_groups=[{'name': sg_id}]
            )
            
            print(f"✓ Created instance: {name} (waiting for boot...)")
            
           
            self.conn.compute.wait_for_server(instance, wait=120)
            print(f"✓ Instance {name} is running")
            
            return instance
        
        except Exception as e:
            print(f"✗ Failed to create instance: {e}")
            return None
    
    def delete_instance(self, instance_id):
        
        try:
            self.conn.compute.delete_server(instance_id, ignore_missing=True)
            print(f"✓ Deleted instance: {instance_id}")
            return True
        
        except Exception as e:
            print(f"✗ Failed to delete instance: {e}")
            return False
    
    def get_instance_by_tag(self, tag_prefix):
        
        try:
            instances = []
            for server in self.conn.compute.servers():
                if server.name.startswith(tag_prefix):
                    instances.append(server)
            
            return instances
        
        except Exception as e:
            print(f"✗ Failed to get instances: {e}")
            return []
    
    def allocate_floating_ip(self, instance_id, external_network_name='public'):
        
        try:
           
            external_network = self.conn.network.find_network(
                external_network_name,
                ignore_missing=True
            )
            
            if not external_network:
                print(f"✗ External network not found")
                return None
            
            
            floating_ip = self.conn.network.create_ip(
                floating_network_id=external_network.id
            )
            
            
            instance = self.conn.compute.get_server(instance_id)
            
           
            ports = list(self.conn.network.ports(device_id=instance_id))
            if not ports:
                print(f"✗ No ports found for instance")
                return None
            
            
            self.conn.network.update_ip(
                floating_ip,
                port_id=ports[0].id
            )
            
            print(f"✓ Assigned floating IP {floating_ip.floating_ip_address} to {instance.name}")
            return floating_ip
        
        except Exception as e:
            print(f"✗ Failed to allocate floating IP: {e}")
            return None
    
    def get_instance_ip(self, instance_id):
        
        try:
            instance = self.conn.compute.get_server(instance_id)
            
            
            for addr_group in instance.addresses.values():
                for addr in addr_group:
                    if addr['OS-EXT-IPS:type'] == 'floating':
                        return addr['addr']
            
            return None
        
        except Exception as e:
            print(f"✗ Failed to get instance IP: {e}")
            return None
    
    def delete_network_resources(self, router_id, subnet_id, network_id):
        
        try:
           
            self.conn.network.remove_router_interface(
                router_id,
                subnet_id=subnet_id
            )
            
           
            self.conn.network.delete_router(router_id)
            
            
            self.conn.network.delete_subnet(subnet_id)
            
            
            self.conn.network.delete_network(network_id)
            
            print(f"✓ Deleted network resources")
            return True
        
        except Exception as e:
            print(f"✗ Failed to delete network resources: {e}")
            return False
    
    def disconnect(self):
        
        if self.conn:
            self.conn.close()
            print(f"✓ Disconnected from OpenStack")


if __name__ == "__main__":

    manager = OpenStackManager(
        'HareeshSatyendra-project-openrc.sh',
        'nso-test'
    )
    
    if manager.connect():
        print("✓ OpenStack Manager initialized successfully")
    else:
        print("✗ Failed to initialize OpenStack Manager")