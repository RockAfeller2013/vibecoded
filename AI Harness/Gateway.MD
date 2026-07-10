# UniFi Cloud Gateway: Allow VLAN 100 → Single IP on VLAN 300 Only
 
Goal: Devices on VLAN 100 can reach **one specific IP** on VLAN 300, and nothing else on VLAN 300.
 
> Note: The per-network **"Network Isolation"** toggle (Settings > Networks) is all-or-nothing and does
> not support single-IP exceptions. This guide uses the Zone-Based Firewall (ZBF) instead, which does.
 
---
 
## Step 1: Turn off Network Isolation
1. Go to **Settings > Networks**.
2. Select **VLAN 100** > toggle **Network Isolation** OFF (if enabled).
3. Select **VLAN 300** > toggle **Network Isolation** OFF (if enabled).
4. Save.
---
 
## Step 2: Create an IP Group for the destination
1. Go to **Settings > Firewall & Security > IP Groups** (or under "Groups").
2. Click **Create New Group**.
3. Name: `VLAN300-SingleIP`
4. Type: **IPv4 Address Group**
5. Add the single destination IP, e.g. `192.168.30.50`
6. Save.
---
 
## Step 3: Create the Block rule (VLAN100 → all of VLAN300)
1. Go to **Settings > Firewall & Security > Zones**.
2. Since both VLANs are in the default **Internal** zone, go to:
   **Internal / Internal > View Policies**
3. Click **Create New Policy**.
4. Configure:
   - Name: `Block VLAN100 to VLAN300`
   - Action: **Block**
   - Source Network: `VLAN 100`
   - Destination Network: `VLAN 300`
   - Destination: `Any`
5. Save.
---
 
## Step 4: Create the Allow rule (VLAN100 → single IP) — must be ABOVE the block rule
1. Same policy list (**Internal / Internal > View Policies**).
2. Click **Create New Policy**.
3. Configure:
   - Name: `Allow VLAN100 to VLAN300 Single IP`
   - Action: **Allow**
   - Source Network: `VLAN 100`
   - Destination: select the `VLAN300-SingleIP` IP Group
   - Protocol: Any (or restrict to a specific port/service if desired)
4. Save.
5. **Drag this rule above** `Block VLAN100 to VLAN300` in the list.
   - Rules are evaluated top-to-bottom; first match wins.
---
 
## Step 5: Verify
- From a VLAN 100 device:
  - Connect to the single allowed IP on VLAN 300 → should **succeed**.
  - Connect to any other IP on VLAN 300 → should **fail**.
- Optional: enable logging on both rules and check **Insights > Firewall/Traffic Logs**
  to confirm which rule is being matched.
---
 
## Rule order summary
 
```
1. Allow: VLAN100 -> VLAN300-SingleIP   (Allow)
2. Block: VLAN100 -> VLAN300 (Any)      (Block)
```
