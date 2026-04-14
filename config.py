#!/usr/bin/env python3
#Reads and parses OpenStack RC file and servers.conf
import os
import sys
from pathlib import Path


class ConfigParser:
    
    
    def __init__(self, rc_file, servers_conf):
       
        self.rc_file = rc_file
        self.servers_conf = servers_conf
        self.config = {}
        self.servers = {}
        
    def parse_rc_file(self):
        
        try:
            with open(self.rc_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse export statements
                    if line.startswith('export '):
                        parts = line.replace('export ', '').split('=', 1)
                        if len(parts) == 2:
                            key, value = parts
                            # Remove quotes
                            value = value.strip('\'"')
                            self.config[key] = value
            
            return self.config
        
        except FileNotFoundError:
            print(f"Error: RC file not found: {self.rc_file}")
            sys.exit(1)
        except Exception as e:
            print(f"Error parsing RC file: {e}")
            sys.exit(1)
    
    def parse_servers_conf(self):
        
        try:
            with open(self.servers_conf, 'r') as f:
                for line in f:
                    line = line.strip()
                    
                    
                    if not line or line.startswith('#'):
                        continue
                    
                   
                    if '=' in line:
                        key, value = line.split('=', 1)
                        try:
                            self.servers[key.strip()] = int(value.strip())
                        except ValueError:
                            print(f"Warning: Could not parse {key}={value}")
            
            return self.servers
        
        except FileNotFoundError:
            print(f"Error: servers.conf not found: {self.servers_conf}")
            sys.exit(1)
        except Exception as e:
            print(f"Error parsing servers.conf: {e}")
            sys.exit(1)
    
    def get_openstack_env(self):
        return self.config
    
    def get_server_counts(self):
        return self.servers
    
    def validate_config(self):
        required_rc = ['OS_AUTH_URL', 'OS_PROJECT_NAME', 'OS_USERNAME']
        required_servers = ['service_nodes', 'proxy_nodes', 'bastion_nodes']
        
        missing_rc = [key for key in required_rc if key not in self.config]
        missing_servers = [key for key in required_servers if key not in self.servers]
        
        if missing_rc:
            print(f"Error: Missing RC variables: {missing_rc}")
            return False
        
        if missing_servers:
            print(f"Error: Missing server configs: {missing_servers}")
            return False
        
        return True


if __name__ == "__main__":
    parser = ConfigParser(
        'HareeshSatyendra-project-openrc.sh',
        'servers.conf'
    )
    
    print("Parsing OpenStack RC file...")
    parser.parse_rc_file()
    
    print("Parsing servers.conf...")
    parser.parse_servers_conf()
    
    
    else:
        print("✗ Configuration is invalid!")