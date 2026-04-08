#!/usr/bin/env python3
"""
OpenStack Utility Library
Provides functions to interact with OpenStack API (Nova, Neutron, Glance)
"""

import os
import subprocess
import json
import sys
from pathlib import Path

class OpenStackUtils:
    """Utility class for OpenStack operations"""
    
    def __init__(self, rc_file=None):
        """
        Initialize OpenStack utils with RC file
        
        Args:
            rc_file: Path to OpenStack RC file (e.g., HareeshSatyendra-project-openrc.sh)
        """
        self.rc_file = rc_file or "HareeshSatyendra-project-openrc.sh"
        self.project_root = Path(__file__).parent
        self.rc_path = self.project_root / self.rc_file
        
        if not self.rc_path.exists():
            raise FileNotFoundError(f"RC file not found: {self.rc_path}")
    
    def _source_rc(self):
        """Source the RC file and get environment variables"""
        # Note: On Windows, we need to parse the RC file differently
        # This is a simplified version for testing
        env = os.environ.copy()
        
        # Read RC file and extract export statements
        try:
            with open(self.rc_path, 'r') as f:
                for line in f:
                    if line.startswith('export '):
                        # Parse: export VAR=value
                        parts = line.replace('export ', '').strip().split('=', 1)
                        if len(parts) == 2:
                            key, value = parts
                            # Remove quotes if present
                            value = value.strip('\'"')
                            env[key] = value
        except Exception as e:
            print(f"Error sourcing RC file: {e}")
        
        return env
    
    def run_command(self, cmd, use_rc=True):
        """
        Run OpenStack CLI command
        
        Args:
            cmd: Command to run (e.g., 'nova list', 'openstack server list')
            use_rc: Whether to use RC file environment
            
        Returns:
            Command output as string
        """
        env = self._source_rc() if use_rc else os.environ.copy()
        
        try:
            # For Windows, use shell=True
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode != 0:
                print(f"Error: {result.stderr}", file=sys.stderr)
                return None
            
            return result.stdout
        
        except Exception as e:
            print(f"Failed to run command '{cmd}': {e}", file=sys.stderr)
            return None
    
    def list_instances(self):
        """List all running instances in the project"""
        output = self.run_command("openstack server list")
        return output
    
    def list_networks(self):
        """List all networks in the project"""
        output = self.run_command("openstack network list")
        return output
    
    def list_images(self):
        """List all available images"""
        output = self.run_command("openstack image list")
        return output
    
    def create_instance(self, name, image, flavor, network=None):
        """
        Create a new instance
        
        Args:
            name: Instance name
            image: Image ID or name
            flavor: Flavor ID or name (e.g., m1.small)
            network: Network ID or name (optional)
            
        Returns:
            Command output
        """
        cmd = f"openstack server create --image {image} --flavor {flavor}"
        
        if network:
            cmd += f" --nic net-id={network}"
        
        cmd += f" {name}"
        
        return self.run_command(cmd)
    
    def delete_instance(self, instance_id):
        """Delete an instance"""
        cmd = f"openstack server delete {instance_id}"
        return self.run_command(cmd)
    
    def get_instance_status(self, instance_id):
        """Get status of a specific instance"""
        cmd = f"openstack server show {instance_id}"
        return self.run_command(cmd)
    
    def test_connection(self):
        """Test connection to OpenStack"""
        print("Testing OpenStack connection...")
        output = self.run_command("openstack project list")
        
        if output:
            print("✅ Connection successful!")
            return True
        else:
            print("❌ Connection failed!")
            return False


if __name__ == "__main__":
    try:
        utils = OpenStackUtils()
        
        # Test connection
        utils.test_connection()
        
        # List instances
        print("\n--- Instances ---")
        instances = utils.list_instances()
        print(instances if instances else "No instances found")
        
        # List networks
        print("\n--- Networks ---")
        networks = utils.list_networks()
        print(networks if networks else "No networks found")
        
        # List images
        print("\n--- Images ---")
        images = utils.list_images()
        print(images if images else "No images found")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)