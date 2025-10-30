#!/usr/bin/env python3

import json
import subprocess
import sys

def run(command):
    return subprocess.run(command, capture_output=True, encoding='UTF-8')

def get_ips():
    command = "terraform output --json".split()
    ip_data = json.loads(run(command).stdout)
    host_ips = ip_data.get('host_vm_ips', {}).get('value', [])
    worker_ips = ip_data.get('worker_vm_ips', {}).get('value', [])
    return host_ips, worker_ips

def generate_inventory_ini(host_ips, worker_ips):
    inventory_lines = []

    if host_ips:
        inventory_lines.append("[host]")
        for ip in host_ips:
            inventory_lines.append(ip)
        inventory_lines.append("")

    if worker_ips:
        inventory_lines.append("[workers]")
        for ip in worker_ips:
            inventory_lines.append(ip)

    return "\n".join(inventory_lines)

if __name__ == "__main__":
    host_ips, worker_ips = get_ips()

    if '--first-worker-ip' in sys.argv:
         if worker_ips:
             print(worker_ips[0])
             sys.exit(0)
         else:
             print("Error: No worker IPs found.", file=sys.stderr)
             sys.exit(1)

    else:
        print(generate_inventory_ini(host_ips, worker_ips))