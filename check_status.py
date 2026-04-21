import sys
sys.path.insert(0, '.')
from openstack_manager import OpenStackManager

manager = OpenStackManager('HareeshSatyendra-project-openrc.sh', 'nso')
if manager.connect():
    instances = manager.get_instance_by_tag('nso')
    for inst in instances:
        print(f"{inst.name}: {inst.status}")
    manager.disconnect()