# Proxmox Internet-Only VM/LXC Firewall Guide

```architecture-beta
group datacenter(cloud)[Proxmox Datacenter]

group node(server)[Proxmox Node] in datacenter

group isolated_vm(server)[Protected VM/LXC] in node
group normal_vm(server)[Other VM/LXC] in node

service firewall(shield)[VM Firewall] in isolated_vm

service internet(internet)[Internet]
service nfs(database)[NFS Server\n192.168.1.146]

group blocked(cloud)[Blocked Local Networks]

service lan192(server)[192.168.0.0/16] in blocked
service lan10(server)[10.0.0.0/8] in blocked
service lan172(server)[172.16.0.0/12] in blocked

junction fw

firewall:R -- L:fw
fw:R -- L:internet
fw:B -- T:nfs

firewall:L -- R:lan192
firewall:L -- R:lan10
firewall:L -- R:lan172

%% Allowed Paths
internet:R --> L:firewall
nfs:T --> B:firewall

%% Notes
%% Protected VM/LXC:
%% - Policy In = DROP
%% - Policy Out = DROP
%% - Allow DNS (53)
%% - Allow HTTP (80)
%% - Allow HTTPS (443)
%% - Allow NTP (123)
%% - Allow NFS TCP 2049 to 192.168.1.146
%%
%% Other VMs/LXCs:
%% - No special firewall rules
%%
%% Blocked Networks:
%% - 10.0.0.0/8
%% - 172.16.0.0/12
%% - 192.168.0.0/16
```

## Objective

Create a firewall policy for selected VMs/LXCs that:

- Allows Internet access
- Allows NFS access to `192.168.1.146`
- Blocks access to all other local networks
- Does not affect any other VM/LXC

---

# Step 1 - Enable Proxmox Firewall Globally

Navigate to:

```text
Datacenter
└── Firewall
    └── Options
```

Set:

```text
Firewall = Yes
```

---

# Step 2 - Enable Firewall on the VM/LXC

Navigate to:

```text
VM/LXC
└── Firewall
    └── Options
```

Set:

```text
Firewall = Yes
Policy In  = DROP
Policy Out = DROP
```

---

# Step 3 - Enable Firewall on Network Interface

Navigate to:

```text
VM/LXC
└── Hardware
    └── Network Device
```

Edit the network adapter.

Ensure:

```text
Firewall = Yes
```

---

# Step 4 - Create Alias for NFS Server

Navigate to:

```text
VM/LXC
└── Firewall
    └── Aliases
```

Create:

```text
Name: NFS_SERVER
CIDR: 192.168.1.146
```

---

# Step 5 - Add Firewall Rules

Navigate to:

```text
VM/LXC
└── Firewall
    └── Rules
```

Add the following rules in the exact order shown.

---

## Rule 1 - Allow NFS

```text
Direction: OUT
Action: ACCEPT
Protocol: TCP
Destination: 192.168.1.146
Destination Port: 2049
Comment: Allow NFS
```

---

## Rule 2 - Block 10.x.x.x Networks

```text
Direction: OUT
Action: DROP
Destination: 10.0.0.0/8
Comment: Block RFC1918
```

---

## Rule 3 - Block 172.16.x.x Networks

```text
Direction: OUT
Action: DROP
Destination: 172.16.0.0/12
Comment: Block RFC1918
```

---

## Rule 4 - Block 192.168.x.x Networks

```text
Direction: OUT
Action: DROP
Destination: 192.168.0.0/16
Comment: Block RFC1918
```

---

## Rule 5 - Allow DNS UDP

```text
Direction: OUT
Action: ACCEPT
Protocol: UDP
Destination Port: 53
Comment: DNS UDP
```

---

## Rule 6 - Allow DNS TCP

```text
Direction: OUT
Action: ACCEPT
Protocol: TCP
Destination Port: 53
Comment: DNS TCP
```

---

## Rule 7 - Allow HTTP

```text
Direction: OUT
Action: ACCEPT
Protocol: TCP
Destination Port: 80
Comment: HTTP
```

---

## Rule 8 - Allow HTTPS

```text
Direction: OUT
Action: ACCEPT
Protocol: TCP
Destination Port: 443
Comment: HTTPS
```

---

## Rule 9 - Allow NTP

```text
Direction: OUT
Action: ACCEPT
Protocol: UDP
Destination Port: 123
Comment: NTP
```

---

# Step 6 - Verify Rule Order

Your rules should appear as:

```text
1  ACCEPT  OUT  TCP  192.168.1.146  PORT 2049
2  DROP    OUT       10.0.0.0/8
3  DROP    OUT       172.16.0.0/12
4  DROP    OUT       192.168.0.0/16
5  ACCEPT  OUT  UDP  PORT 53
6  ACCEPT  OUT  TCP  PORT 53
7  ACCEPT  OUT  TCP  PORT 80
8  ACCEPT  OUT  TCP  PORT 443
9  ACCEPT  OUT  UDP  PORT 123
```

---

# Step 7 - Test

From the VM/LXC:

## Should Work

```bash
ping 8.8.8.8

curl https://google.com

nslookup google.com

showmount -e 192.168.1.146
```

## Should Fail

```bash
ping 192.168.1.1

ping 192.168.1.100

ssh 192.168.1.1

curl http://192.168.1.1
```

---

# Optional: Create a Security Group

If multiple VMs/LXCs require the same policy:

```text
Datacenter
└── Firewall
    └── Security Groups
```

Create:

```text
Name: INTERNET_ONLY_NFS
```

Add all rules to the security group.

Then attach the security group only to the VMs/LXCs that should be isolated.

This avoids maintaining duplicate firewall rules across multiple guests.
