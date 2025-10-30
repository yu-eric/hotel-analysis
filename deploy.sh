#!/bin/bash
# Update this to your repository location
REPO_DIR="/home/almalinux/proj"

python generate_inventory.py > inventory.ini
HOST_IP=$(terraform output --json | jq -r '.host_vm_ips.value[0]')
WORKER_1=$(terraform output --json | jq -r '.worker_vm_ips.value[0]')
WORKER_2=$(terraform output --json | jq -r '.worker_vm_ips.value[1]')
WORKER_3=$(terraform output --json | jq -r '.worker_vm_ips.value[2]')
WORKER_4=$(terraform output --json | jq -r '.worker_vm_ips.value[3]')

rsync -ah $REPO_DIR $HOST_IP:/home/almalinux
rsync -ah $REPO_DIR $WORKER_1:/home/almalinux
rsync -ah $REPO_DIR $WORKER_2:/home/almalinux
rsync -ah $REPO_DIR $WORKER_3:/home/almalinux 
rsync -ah $REPO_DIR $WORKER_4:/home/almalinux

ssh -T $HOST_IP << EOF
    while [ ! -f /var/lib/cloud/instance/boot-finished ]; do
        echo "Waiting for cloud-init to finish..."
        sleep 10
    done
    cd proj
    mv id_rsa /home/almalinux/.ssh
    echo "Host *
        StrictHostKeyChecking no" > /home/almalinux/.ssh/config
    nohup ansible-playbook -i inventory.ini full.yaml &
EOF
