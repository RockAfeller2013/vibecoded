# Proxmox Internet-Only VM/LXC Firewall Guide

```mermaid
architecture-beta
    group datacenter(cloud)[Proxmox]
    group node(server)[Node] in datacenter
    group isolated(server)[Isolated VM] in node
    group normal(server)[Other VMs] in node
    group blocked(cloud)[Blocked Nets]

    service fw(shield)[Firewall] in isolated
    service internet(internet)[Internet]
    service nfs(database)[NFS 192.168.1.146]
    service net10(server)[10.0.0.0/8] in blocked
    service net172(server)[172.16.0.0/12] in blocked
    service net192(server)[192.168.0.0/16] in blocked

    fw -- internet
    fw -- nfs
    fw -- net10
    fw -- net172
    fw -- net192
```
