#!/bin/bash

# ==================================================
# ACK-ME CORP CTF INVESTIGATION SCRIPT
# Mission: Find the developer's weekend knowledge-base chatbot
# ==================================================

echo "=== Starting Ack-Me Corp Investigation ==="
echo "Target: ackme-corp.net"
echo "Mission: Find internal knowledge-base chatbot with sensitive data"
echo ""

# ==================================================
# PHASE 1: DNS ENUMRATION - FIND ALL SUBDOMAINS
# ==================================================

echo "=== PHASE 1: DNS Enumeration ==="

# Step 1: Use subfinder to find known subdomains from various sources
echo "[+] Running subfinder to discover known subdomains..."
subfinder -d ackme-corp.net -silent > subdomains.txt
echo "Subfinder found $(wc -l < subdomains.txt) subdomains"

# Step 2: Bruteforce additional subdomains using shuffledns
echo "[+] Bruteforcing subdomains with shuffledns..."
shuffledns -d ackme-corp.net -w /opt/wordlists/subdomain-wordlist.txt -r /opt/massdns/resolvers.txt -o bruteforced.txt
echo "ShuffleDNS found $(wc -l < bruteforced.txt) additional subdomains"

# Step 3: Combine all discovered subdomains and remove duplicates
echo "[+] Combining and deduplicating subdomain lists..."
cat subdomains.txt bruteforced.txt | sort -u > all_subdomains.txt
echo "Total unique subdomains: $(wc -l < all_subdomains.txt)"

# Step 4: Resolve all subdomains to IP addresses using massdns
echo "[+] Resolving subdomains to IP addresses..."
massdns -r /opt/massdns/resolvers.txt -t A -o S -w resolved.txt all_subdomains.txt

# Step 5: Extract only live subdomains that resolved successfully
echo "[+] Extracting live subdomains..."
grep -E " A " resolved.txt | awk '{print $1}' | sed 's/\.$//' > live_subdomains.txt
echo "Live subdomains: $(wc -l < live_subdomains.txt)"

# Display discovered subdomains for review
echo "[+] Discovered subdomains:"
cat live_subdomains.txt
echo ""

# ==================================================
# PHASE 2: HTTP SERVICE DISCOVERY
# ==================================================

echo "=== PHASE 2: HTTP Service Discovery ==="

# Step 6: Probe which subdomains have active HTTP/HTTPS services
echo "[+] Probing HTTP/HTTPS services with httpx..."
cat live_subdomains.txt | httpx -silent > http_services.txt
echo "Active HTTP services: $(wc -l < http_services.txt)"

# Display active HTTP services
echo "[+] Active web services found:"
cat http_services.txt
echo ""

# ==================================================
# PHASE 3: WEB CONTENT DISCOVERY
# ==================================================

echo "=== PHASE 3: Web Content Discovery ==="

# Step 7: Directory and file bruteforcing on each discovered web service
echo "[+] Starting directory/file discovery with ffuf (5 threads max)..."
mkdir -p ffuf_results  # Create directory for results

for domain in $(cat http_services.txt); do
    echo "[+] Scanning: $domain"
    
    # Clean domain name for filename
    clean_domain=$(echo $domain | sed 's|https\?://||' | tr '/' '_')
    
    # Run ffuf with limited threads for directory discovery
    ffuf -u $domain/FUZZ \
         -w /opt/wordlists/api-objects.txt \
         -t 5 \
         -mc 200,301,302,403 \
         -o ffuf_results/${clean_domain}.json \
         -of json \
         -s
    
    echo "    -> Results saved to ffuf_results/${clean_domain}.json"
done

# ==================================================
# PHASE 4: TARGETED SEARCH FOR DEVELOPER PROJECT
# ==================================================

echo "=== PHASE 4: Targeted Search for Developer Project ==="

# Step 8: Look specifically for knowledge-base and chatbot related endpoints
echo "[+] Searching for knowledge-base/chatbot specific paths..."

# Create custom wordlist for developer project keywords
cat > /tmp/dev_keywords.txt << 'EOF'
chat
chatbot
bot
knowledge
knowledgebase
kb
internal
dev
developer
weekend
sideproject
vibe
vibing
api
admin
console
debug
test
staging
database
records
customer
data
EOF

# Search main domain with developer keywords
echo "[+] Scanning main domain for developer project indicators..."
ffuf -u https://ackme-corp.net/FUZZ \
     -w /tmp/dev_keywords.txt \
     -t 5 \
     -mc 200,301,302,403 \
     -o ffuf_results/main_domain_dev.json \
     -of json

# Step 9: Check for common developer framework paths
echo "[+] Checking for common developer framework paths..."

# Common paths for web apps and APIs
cat > /tmp/framework_paths.txt << 'EOF'
api/v1
api/v2
v1/api
v2/api
graphql
admin
console
debug
test
docs
swagger
redoc
api-docs
api/docs
_chat
_bot
_internal
_private
EOF

for domain in $(cat http_services.txt); do
    clean_domain=$(echo $domain | sed 's|https\?://||' | tr '/' '_')
    echo "[+] Checking framework paths on: $domain"
    
    ffuf -u $domain/FUZZ \
         -w /tmp/framework_paths.txt \
         -t 5 \
         -mc 200,301,302,403 \
         -o ffuf_results/${clean_domain}_framework.json \
         -of json \
         -s
done

# ==================================================
# PHASE 5: NETWORK SCANNING & SERVICE DISCOVERY
# ==================================================

echo "=== PHASE 5: Network Scanning ==="

# Step 10: Extract unique IP addresses from DNS results
echo "[+] Extracting unique IP addresses..."
grep -E " A " resolved.txt | awk '{print $3}' | sort -u > unique_ips.txt
echo "Unique IPs found: $(wc -l < unique_ips.txt)"

# Step 11: Quick port scanning on discovered IPs
echo "[+] Performing quick port scans..."
mkdir -p nmap_results

for ip in $(cat unique_ips.txt); do
    echo "[+] Scanning IP: $ip"
    
    # Quick scan for common web and developer ports
    nmap -sS -T4 -p 80,443,3000,5000,8000,8080,8443,9000 $ip \
         -oN nmap_results/quick_$ip.txt
    
    # Check if any unusual ports are open
    open_ports=$(grep "open" nmap_results/quick_$ip.txt | wc -l)
    echo "    -> Open ports: $open_ports"
done

# ==================================================
# PHASE 6: DETAILED HTTP ANALYSIS
# ==================================================

echo "=== PHASE 6: Detailed HTTP Analysis ==="

# Step 12: Examine HTTP headers and responses for clues
echo "[+] Analyzing HTTP headers and responses..."
mkdir -p curl_results

for url in $(cat http_services.txt); do
    clean_url=$(echo $url | sed 's|https\?://||' | tr '/' '_' | tr '.' '_')
    echo "[+] Analyzing: $url"
    
    # Get detailed header information
    curl -I -L -k "$url" > "curl_results/${clean_url}_headers.txt" 2>/dev/null
    
    # Get full page response
    curl -L -k "$url" > "curl_results/${clean_url}_content.txt" 2>/dev/null
    
    # Check for interesting headers
    echo "=== Headers for $url ===" >> analysis_summary.txt
    grep -i "server\|x-powered-by\|api\|token\|auth" "curl_results/${clean_url}_headers.txt" >> analysis_summary.txt
    echo "" >> analysis_summary.txt
done

# ==================================================
# PHASE 7: DATA ANALYSIS & FLAG IDENTIFICATION
# ==================================================

echo "=== PHASE 7: Data Analysis ==="

# Step 13: Parse and analyze all results
echo "[+] Analyzing collected data..."

# Parse FFUF results to find interesting endpoints
echo "[+] Interesting endpoints discovered:" > findings.txt
for result_file in ffuf_results/*.json; do
    if [ -s "$result_file" ]; then
        echo "=== $(basename $result_file) ===" >> findings.txt
        jq -r '.results[] | select(.status == 200 or .status == 301 or .status == 302) | "\(.url) [Status: \(.status)]"' "$result_file" >> findings.txt 2>/dev/null
        echo "" >> findings.txt
    fi
done

# Step 14: Look for API endpoints and unusual services
echo "[+] Searching for API endpoints and unusual services..."

# Check for JSON responses and API-like content
for content_file in curl_results/*_content.txt; do
    if grep -q "api\|json\|token\|auth\|customer\|record" "$content_file" 2>/dev/null; then
        echo "Potential API/service found in: $(basename $content_file)" >> findings.txt
    fi
done

# Step 15: Check for exposed files and backup files
echo "[+] Checking for exposed files..."

# Common sensitive files to check
cat > /tmp/sensitive_files.txt << 'EOF
.env
config.json
config.php
backup.zip
dump.sql
database.sql
readme.md
TODO.txt
notes.txt
password.txt
credentials.json
EOF

for domain in $(cat http_services.txt); do
    clean_domain=$(echo $domain | sed 's|https\?://||' | tr '/' '_')
    echo "[+] Checking for sensitive files on: $domain"
    
    ffuf -u $domain/FUZZ \
         -w /tmp/sensitive_files.txt \
         -t 5 \
         -mc 200,301,302,403 \
         -o ffuf_results/${clean_domain}_files.json \
         -of json \
         -s
done

# ==================================================
# PHASE 8: SUMMARY AND REPORTING
# ==================================================

echo "=== PHASE 8: Generating Summary ==="

# Step 16: Generate final summary report
echo "[+] Generating investigation summary..."

cat > investigation_report.txt << 'EOF'
=== ACK-ME CORP INVESTIGATION REPORT ===
Target: ackme-corp.net
Mission: Find internal knowledge-base chatbot
Investigation Date: $(date)

SUMMARY:
- Subdomains discovered: $(wc -l < all_subdomains.txt)
- Live subdomains: $(wc -l < live_subdomains.txt)
- HTTP services: $(wc -l < http_services.txt)
- Unique IP addresses: $(wc -l < unique_ips.txt)

LIVE SUBDOMAINS:
$(cat live_subdomains.txt)

HTTP SERVICES:
$(cat http_services.txt)

KEY FINDINGS:
$(cat findings.txt | head -50)  # First 50 lines of findings

NEXT STEPS:
1. Examine discovered endpoints for the knowledge-base chatbot
2. Check for authentication bypass vulnerabilities
3. Look for exposed API endpoints with customer data
4. Search for developer comments and metadata

FLAG LOCATION HINTS:
- Check unusual subdomains (dev-, test-, internal- prefixes)
- Look for /chat, /api, /knowledge endpoints
- Examine response headers for framework information
- Check for exposed configuration files
EOF

# Display quick summary
echo ""
echo "=== INVESTIGATION COMPLETE ==="
echo "Report saved to: investigation_report.txt"
echo "FFUF results in: ffuf_results/"
echo "Nmap results in: nmap_results/"
echo "Curl results in: curl_results/"
echo ""
echo "Next: Examine the findings for the knowledge-base chatbot flag!"

# Cleanup temporary files
rm -f /tmp/dev_keywords.txt /tmp/framework_paths.txt /tmp/sensitive_files.txt

echo "=== Script finished ==="
