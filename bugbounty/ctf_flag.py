#!/usr/bin/env python3
"""
ACK-ME CORP CTF FLAG FINDER
Specialized script to find flags in common CTF formats
"""

import requests
import re
import json
import os
import sys
from urllib.parse import urljoin, urlparse
import concurrent.futures
from datetime import datetime

class CTFFlagHunter:
    def __init__(self, domain="ackme-corp.net"):
        self.domain = domain
        self.found_flags = []
        
        # Exact flag patterns based on the description
        self.flag_patterns = [
            # Standard CTF formats
            r'FLAG\{[^}]+?\}',
            r'flag\{[^}]+?\}',
            r'FLAG{[^}]+?}',  # Some CTFs use FLAG{...} without backslash
            r'flag{[^}]+?}',
            
            # Ack-Me Corp specific formats
            r'ackme-flag-[a-z0-9]{6,12}',
            r'ACKME-FLAG-[A-Z0-9]{6,12}',
            r'ackme\{[^}]+?\}',
            r'ACKME\{[^}]+?\}',
            
            # Generic CTF patterns
            r'ctf\{[^}]+?\}',
            r'CTF\{[^}]+?\}',
            r'[a-f0-9]{32}',  # MD5-like hashes
            r'[A-F0-9]{32}',  # Uppercase hashes
            r'[a-zA-Z0-9]{16,64}',  # Generic tokens
            
            # Common bug bounty formats
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',  # UUID
            r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*',  # JWT tokens
        ]
        
        # High-priority endpoints for flag hunting
        self.high_priority_endpoints = [
            '/flag', '/flags', '/secret', '/admin', '/debug', 
            '/api/flag', '/api/secret', '/internal/flag',
            '/chat/api', '/bot/flag', '/knowledgebase/secret',
            '/dev/flag', '/test/flag', '/staging/flag',
            '/.env', '/config.json', '/backup.zip', '/dump.sql',
            '/readme.md', '/TODO.txt', '/notes.txt'
        ]
        
        # Developer project specific paths
        self.dev_project_paths = [
            '/weekend/', '/sideproject/', '/vibe/', '/vibing/',
            '/knowledge-base/', '/chatbot/', '/internal-chat/',
            '/customer-records/', '/sensitive-data/'
        ]

    def log_message(self, message):
        """Helper function for logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def load_targets_from_file(self, filename="http_services.txt"):
        """Load previously discovered HTTP services"""
        if not os.path.exists(filename):
            self.log_message(f"❌ File not found: {filename}")
            return []
        
        with open(filename, 'r') as f:
            targets = [line.strip() for line in f if line.strip()]
        
        self.log_message(f"✅ Loaded {len(targets)} targets from {filename}")
        return targets

    def search_for_flags_in_text(self, text, source_url):
        """Search for flag patterns in text content"""
        flags_found = []
        
        for pattern in self.flag_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Validate it's not a false positive
                if self.validate_flag(match):
                    flags_found.append({
                        'flag': match,
                        'pattern': pattern,
                        'source_url': source_url,
                        'context': self.get_flag_context(text, match)
                    })
        
        return flags_found

    def validate_flag(self, potential_flag):
        """Validate if a string is likely a real flag"""
        # Exclude common false positives
        false_positives = [
            'flag_', 'flag-', 'flag.png', 'flag.jpg', 
            'stylesheet', 'javascript', 'function',
            '0000000000000000', '1234567890abcdef'
        ]
        
        # Check length constraints
        if len(potential_flag) < 8 or len(potential_flag) > 100:
            return False
        
        # Check for false positives
        if any(fp in potential_flag.lower() for fp in false_positives):
            return False
        
        # Specific validation for different flag types
        if re.match(r'FLAG\{[^}]+\}', potential_flag, re.IGNORECASE):
            return len(potential_flag) > 10  # FLAG{...} should have content
        
        if re.match(r'ackme-flag-[a-z0-9]{6,12}', potential_flag, re.IGNORECASE):
            return True
        
        if re.match(r'[a-f0-9]{32}', potential_flag) and not all(c == '0' for c in potential_flag):
            return True  # MD5-like hash that's not all zeros
        
        return True  # Default to true for other patterns

    def get_flag_context(self, text, flag, context_chars=100):
        """Extract context around the found flag"""
        flag_index = text.find(flag)
        if flag_index == -1:
            return "Context not available"
        
        start = max(0, flag_index - context_chars)
        end = min(len(text), flag_index + len(flag) + context_chars)
        
        context = text[start:end]
        # Clean up the context
        context = re.sub(r'\s+', ' ', context)
        return context.strip()

    def check_endpoint(self, base_url, endpoint):
        """Check a specific endpoint for flags"""
        url = urljoin(base_url, endpoint)
        
        try:
            response = requests.get(url, timeout=10, verify=False, allow_redirects=True)
            
            # Check response content for flags
            flags_in_content = self.search_for_flags_in_text(response.text, url)
            
            # Check headers for flags
            headers_text = str(response.headers)
            flags_in_headers = self.search_for_flags_in_text(headers_text, f"{url} (headers)")
            
            # Check JSON responses specifically
            flags_in_json = []
            if 'application/json' in response.headers.get('content-type', ''):
                try:
                    json_data = response.json()
                    json_text = json.dumps(json_data)
                    flags_in_json = self.search_for_flags_in_text(json_text, f"{url} (json)")
                except:
                    pass
            
            all_flags = flags_in_content + flags_in_headers + flags_in_json
            
            if all_flags:
                self.log_message(f"🎯 FOUND FLAGS at {url} (Status: {response.status_code})")
                for flag_info in all_flags:
                    self.log_message(f"   🔥 FLAG: {flag_info['flag']}")
            
            return {
                'url': url,
                'status': response.status_code,
                'flags_found': all_flags,
                'content_length': len(response.text)
            }
            
        except requests.RequestException as e:
            return {'url': url, 'error': str(e), 'flags_found': []}

    def deep_scan_url(self, url):
        """Perform deep scanning on a single URL"""
        self.log_message(f"🔍 Deep scanning: {url}")
        
        all_findings = []
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            test_urls = [f'https://{url}', f'http://{url}']
        else:
            test_urls = [url]
        
        for test_url in test_urls:
            # Check high-priority endpoints
            for endpoint in self.high_priority_endpoints:
                finding = self.check_endpoint(test_url, endpoint)
                if finding['flags_found']:
                    all_findings.extend(finding['flags_found'])
            
            # Check developer project paths
            for endpoint in self.dev_project_paths:
                finding = self.check_endpoint(test_url, endpoint)
                if finding['flags_found']:
                    all_findings.extend(finding['flags_found'])
            
            # Check root path and common variations
            common_paths = ['/', '/index.html', '/index.php', '/app', '/web']
            for endpoint in common_paths:
                finding = self.check_endpoint(test_url, endpoint)
                if finding['flags_found']:
                    all_findings.extend(finding['flags_found'])
        
        return all_findings

    def scan_response_for_sensitive_data(self, url):
        """Scan for sensitive data patterns that might lead to flags"""
        try:
            response = requests.get(url, timeout=10, verify=False)
            text = response.text.lower()
            
            sensitive_indicators = [
                'customer', 'record', 'database', 'password', 'secret',
                'key', 'token', 'api_key', 'admin', 'debug', 'internal',
                'knowledgebase', 'chatbot', 'weekend', 'sideproject'
            ]
            
            indicators_found = [ind for ind in sensitive_indicators if ind in text]
            
            if indicators_found:
                self.log_message(f"⚠️  Sensitive indicators at {url}: {', '.join(indicators_found)}")
                
                # Do a more thorough flag search on sensitive pages
                return self.search_for_flags_in_text(response.text, url)
            
            return []
            
        except requests.RequestException:
            return []

    def brute_force_api_endpoints(self, base_url):
        """Brute force common API endpoints that might contain flags"""
        api_endpoints = [
            '/api/flag', '/api/secret', '/api/admin', '/api/debug',
            '/chat/api', '/bot/flag', '/knowledgebase/api',
            '/internal/flag', '/dev/flag', '/test/secret',
            '/v1/flag', '/v2/secret', '/v1/admin', '/v2/debug'
        ]
        
        flags_found = []
        
        for endpoint in api_endpoints:
            result = self.check_endpoint(base_url, endpoint)
            flags_found.extend(result['flags_found'])
        
        return flags_found

    def generate_flag_report(self):
        """Generate a comprehensive flag report"""
        if not self.found_flags:
            return "No flags found during the investigation."
        
        report = f"""
=== ACK-ME CORP CTF FLAG REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Domain: {self.domain}
Total Flags Found: {len(self.found_flags)}

FLAGS FOUND:
{'=' * 60}
"""
        
        for i, flag_info in enumerate(self.found_flags, 1):
            report += f"""
FLAG #{i}:
• Flag: {flag_info['flag']}
• Source: {flag_info['source_url']}
• Pattern: {flag_info['pattern']}
• Context: {flag_info['context']}

"""
        
        report += f"""
VALIDATION INSTRUCTIONS:
• Submit the exact flag string to the CTF platform
• Do not share or publish the flag
• Follow the program's disclosure rules
• Flags prove access to sensitive resources

CRITICAL: These flags often prove exploitation and access to sensitive data.
Handle with care and follow responsible disclosure practices.
"""
        return report

    def run_flag_hunt(self, targets_file="http_services.txt"):
        """Main flag hunting function"""
        self.log_message("🚀 Starting CTF Flag Hunt")
        
        # Load targets
        targets = self.load_targets_from_file(targets_file)
        if not targets:
            self.log_message("❌ No targets to investigate")
            return
        
        self.log_message(f"🎯 Hunting flags across {len(targets)} targets")
        
        # Use threading for faster scanning (limited to 3 concurrent requests)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_url = {executor.submit(self.deep_scan_url, target): target for target in targets}
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    flags = future.result()
                    if flags:
                        self.found_flags.extend(flags)
                        self.log_message(f"✅ Found {len(flags)} flags at {url}")
                except Exception as e:
                    self.log_message(f"❌ Error scanning {url}: {e}")
        
        # Additional sensitive data scanning
        self.log_message("🔍 Performing sensitive data scan...")
        for target in targets:
            try:
                sensitive_flags = self.scan_response_for_sensitive_data(target)
                if sensitive_flags:
                    self.found_flags.extend(sensitive_flags)
            except Exception as e:
                self.log_message(f"❌ Error in sensitive scan for {target}: {e}")
        
        # Remove duplicate flags
        unique_flags = []
        seen_flags = set()
        for flag_info in self.found_flags:
            if flag_info['flag'] not in seen_flags:
                unique_flags.append(flag_info)
                seen_flags.add(flag_info['flag'])
        
        self.found_flags = unique_flags
        
        # Generate report
        report = self.generate_flag_report()
        
        with open('ctf_flags_report.txt', 'w') as f:
            f.write(report)
        
        self.log_message("✅ Flag hunt complete!")
        
        # Print summary
        print("\n" + "="*60)
        if self.found_flags:
            print(f"🎉 FOUND {len(self.found_flags)} UNIQUE FLAGS!")
            print("="*60)
            for flag_info in self.found_flags:
                print(f"🔥 {flag_info['flag']}")
                print(f"   Source: {flag_info['source_url']}")
                print(f"   Context: {flag_info['context'][:100]}...")
                print()
        else:
            print("❌ No flags found. Try expanding the search parameters.")
        
        print(f"📄 Detailed report saved to: ctf_flags_report.txt")

def main():
    """Main execution function"""
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    hunter = CTFFlagHunter()
    
    try:
        hunter.run_flag_hunt()
    except KeyboardInterrupt:
        print("\n⚠️  Flag hunt interrupted by user")
    except Exception as e:
        print(f"❌ Flag hunt failed: {e}")

if __name__ == "__main__":
    main()
