variable img_display_name {
  type = string
  default = "almalinux-9.4-20240805"
}

variable namespace {
  type = string
  default = "your-namespace"
  description = "Kubernetes namespace for your deployment"
}

variable network_name {
  type = string
  default = "your-namespace/your-network"
  description = "Network name in format namespace/network"
}

variable username {
  type = string
  default = "your-username"
  description = "Username prefix for VM naming"
}

variable keyname {
  type = string
  default = "your-ssh-key-name"
  description = "Name of the SSH key to use for VM access"
}

variable vm_count {
  type    = number
  default = 4
}
