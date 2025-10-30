data "harvester_image" "img" {
  display_name = var.img_display_name
  namespace    = "harvester-public"
}

data "harvester_ssh_key" "mysshkey" {
  name      = var.keyname
  namespace = var.namespace
}

resource "random_id" "secret" {
  byte_length = 5
}

# Generate a separate SSH key for inter-VM communication
resource "tls_private_key" "internal_ssh_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "local_file" "internal_private_key" {
  content         = tls_private_key.internal_ssh_key.private_key_pem
  filename        = "${path.module}/id_rsa"
  file_permission = "0600"
}

resource "harvester_cloudinit_secret" "cloud-config" {
  name      = "cloud-config-${random_id.secret.hex}"
  namespace = var.namespace

  user_data = templatefile("cloud-init.tmpl.yaml", {
    public_key_openssh = data.harvester_ssh_key.mysshkey.public_key,
    internal_public_key = tls_private_key.internal_ssh_key.public_key_openssh,
    internal_private_key = tls_private_key.internal_ssh_key.private_key_pem
  })
}

resource "harvester_virtualmachine" "hostvm" {
  
  count = 1

  name                 = "${var.username}-host-${format("%02d", count.index + 1)}-${random_id.secret.hex}"
  namespace            = var.namespace
  restart_after_update = true

  description = "Cluster Host Node"

  cpu    = 2 
  memory = "4Gi"

  efi         = true
  secure_boot = false

  run_strategy    = "RerunOnFailure"
  hostname        = "${var.username}-host-${format("%02d", count.index + 1)}-${random_id.secret.hex}"
  reserved_memory = "100Mi"
  machine_type    = "q35"

  network_interface {
    name           = "nic-1"
    wait_for_lease = true
    type           = "bridge"
    network_name   = var.network_name
  }

  disk {
    name       = "rootdisk"
    type       = "disk"
    size       = "10Gi"
    bus        = "virtio"
    boot_order = 1

    image       = data.harvester_image.img.id
    auto_delete = true
  }


  cloudinit {
    user_data_secret_name = harvester_cloudinit_secret.cloud-config.name
  }
}

resource "harvester_virtualmachine" "workervm" {
  
  count = var.vm_count

  name                 = "${var.username}-worker-${format("%02d", count.index + 1)}-${random_id.secret.hex}"
  namespace            = var.namespace
  restart_after_update = true

  description = "Cluster Compute Node"

  cpu    = 4
  memory = "32Gi"

  efi         = true
  secure_boot = false

  run_strategy    = "RerunOnFailure"
  hostname        = "${var.username}-worker-${format("%02d", count.index + 1)}-${random_id.secret.hex}"
  reserved_memory = "100Mi"
  machine_type    = "q35"

  network_interface {
    name           = "nic-1"
    wait_for_lease = true
    type           = "bridge"
    network_name   = var.network_name
  }

  disk {
    name       = "rootdisk"
    type       = "disk"
    size       = "50Gi"
    bus        = "virtio"
    boot_order = 1

    image       = data.harvester_image.img.id
    auto_delete = true
  }

  # Note: The following tags are specific to the Condenser ingress system
  # If you're using a different ingress/load balancer solution, modify accordingly
  # Uncomment and update these tags to match your ingress controller configuration
  #
  # tags = count.index == 0 ? {
  #   condenser_ingress_isEnabled = true
  #   condenser_ingress_dagster_hostname = "${var.username}-dagster"
  #   condenser_ingress_dagster_port=3000
  #   condenser_ingress_dagster_protocol = "http"
  #   condenser_ingress_dagster_nginx_proxy-body-size = "100000m"
  #   
  #   condenser_ingress_dask_hostname = "${var.username}-dask"
  #   condenser_ingress_dask_port=8787
  #   condenser_ingress_dask_protocol = "http"
  #   condenser_ingress_dask_nginx_proxy-body-size = "100000m"
  #
  #   condenser_ingress_s3_hostname = "${var.username}-s3"
  #   condenser_ingress_s3_port = 9000
  #   condenser_ingress_s3_protocol = "https"
  #   condenser_ingress_s3_nginx_proxy-body-size = "100000m"
  #
  #   condenser_ingress_minio_hostname = "${var.username}-cons"
  #   condenser_ingress_minio_port = 9001
  #   condenser_ingress_minio_protocol = "https"
  #   condenser_ingress_minio_nginx_proxy-body-size = "100000m"
  #
  # } : {}

  cloudinit {
    user_data_secret_name = harvester_cloudinit_secret.cloud-config.name
  }
}
