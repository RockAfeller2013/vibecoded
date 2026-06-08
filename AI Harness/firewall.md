# Proxmox Internet-Only VM/LXC Firewall Guide




```mermaid
architecture-beta
    group datacenter(cloud)[Proxmox]
    group node(server)[Node] in datacenter
    group isolated(server)[Isolated_VM] in node
    group normal(server)[Other_VMs] in node
    group blocked(cloud)[Blocked_Nets]

    service fw(shield)[Firewall] in isolated
    service internet(internet)[Internet]
    service nfs(database)[NFS_192-168-1-146]
    service net10(server)[10-0-0-0_8] in blocked
    service net172(server)[172-16-0-0_12] in blocked
    service net192(server)[192-168-0-0_16] in blocked

    fw:R -- L:internet
    fw:B -- T:nfs
    fw:L -- R:net10
    fw:L -- R:net172
    fw:L -- R:net192
```
