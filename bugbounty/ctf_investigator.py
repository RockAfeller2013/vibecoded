#!/usr/bin/env python3
"""
ACK-ME CORP CTF - PRIORITY INVESTIGATION SCRIPT
Focused on finding the developer's weekend knowledge-base chatbot
"""

import requests
import json
import subprocess
import re
import os
import sys
from urllib.parse import urljoin, urlparse
import concurrent.futures
from datetime import datetime

class CTFInvestigator:
    def __init__(self, domain="ackme-corp.net"):
        self.domain = domain
        self.results = {
            'unusual_subdomains': [],
            'suspicious_headers': [],
            'api_endpoints': [],
            'documentation_endpoints': [],
            'error_messages': [],
            'exposed_files': [],
            'technology_stack': [],
            'potential_flags': []
        }
        
        # Keywords for prioritization
        self.unusual_prefixes = ['dev', 'staging', 'test', 'internal', 'admin', 'secure', 'private', 'backup', 'temp']
        self.api_patterns = ['/api/', '/v1/', '/v2/', '/chat/', '/bot/', '/knowledge/', '/database/']
        self.doc_patterns = ['/docs/', '/swagger/', '/redoc/', '/api-docs/', '/documentation/']
        self.sensitive_files = ['.env', 'config.json', 'backup.zip', 'dump.sql', 'readme.md', 'TODO.txt']
        self.dev_frameworks = ['flask', 'express', 'django', 'rails', 'spring', 'laravel', 'node.js', 'react', 'vue']

    def log_message(self, message):
        """Helper function for logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    def load_subdomains_from_file(self, filename="live_subdomains.txt"):
        """Load previously discovered subdomains"""
        if not os.path.exists(filename):
            self.log_message(f"❌ File not found: {filename}")
            return []
        
        with open(filename, 'r') as f:
            subdomains = [line.strip() for line in f if line.strip()]
        
        self.log_message(f"✅ Loaded {len(subdomains)} subdomains from {filename}")
        return subdomains

    def prioritize_unusual_subdomains(self, subdomains):
        """Priority 1: Find unusual subdomains with suspicious prefixes"""
        self.log_message("🔍 Prioritizing unusual subdomains...")
        
        unusual_subs = []
        for subdomain in subdomains:
            # Check for unusual prefixes
            for prefix in self.unusual_prefixes:
                if subdomain.startswith(f"{prefix}-") or f".{prefix}." in subdomain:
                    unusual_subs.append(subdomain)
                    self.results['unusual_subdomains'].append({
                        'subdomain': subdomain,
                        'reason': f'Contains suspicious prefix: {prefix}',
                        'priority': 'HIGH'
                    })
                    break
            
            # Check for developer-related keywords
            dev_keywords = ['dev', 'test', 'stage', 'internal', 'admin', 'chat', 'bot', 'kb', 'knowledge']
            for keyword in dev_keywords:
                if keyword in subdomain.lower():
                    unusual_subs.append(subdomain)
                    self.results['unusual_subdomains'].append({
                        'subdomain': subdomain,
                        'reason': f'Contains developer keyword: {keyword}',
                        'priority': 'MEDIUM'
                    })
                    break
        
        self.log_message(f"✅ Found {len(unusual_subs)} unusual subdomains")
        return unusual_subs

    def analyze_response_headers(self, url):
        """Priority 2: Analyze HTTP headers for technology stack clues"""
        try:
            self.log_message(f"🔍 Analyzing headers for {url}")
            
            response = requests.get(url, timeout=10, verify=False)
            headers = dict(response.headers)
            
            findings = []
            tech_clues = []
            
            # Check for framework indicators in headers
            server_header = headers.get('Server', '').lower()
            x_powered_by = headers.get('X-Powered-By', '').lower()
            
            for framework in self.dev_frameworks:
                if framework in server_header or framework in x_powered_by:
                    tech_clues.append(framework)
                    findings.append({
                        'url': url,
                        'header': 'Server/X-Powered-By',
                        'value': f"{server_header} {x_powered_by}",
                        'technology': framework,
                        'priority': 'HIGH'
                    })
            
            # Check for development mode indicators
            if 'debug' in str(headers).lower() or 'development' in str(headers).lower():
                findings.append({
                    'url': url,
                    'header': 'Various',
                    'value': 'Debug/Development mode detected',
                    'technology': 'Development Environment',
                    'priority': 'CRITICAL'
                })
            
            # Check for API-related headers
            api_headers = ['api-key', 'authorization', 'bearer', 'token']
            for header in headers:
                if any(api_hdr in header.lower() for api_hdr in api_headers):
                    findings.append({
                        'url': url,
                        'header': header,
                        'value': headers[header][:100] + '...' if len(headers[header]) > 100 else headers[header],
                        'technology': 'API Authentication',
                        'priority': 'HIGH'
                    })
            
            if findings:
                self.results['suspicious_headers'].extend(findings)
                self.results['technology_stack'].extend(tech_clues)
            
            return headers, response.text
            
        except Exception as e:
            self.log_message(f"❌ Error analyzing {url}: {e}")
            return {}, ""

    def examine_error_messages(self, url, response_text):
        """Priority 3: Extract technology stack from error messages"""
        if not response_text:
            return
        
        # Common error patterns that reveal technology
        error_patterns = {
            'flask': [r'jinja2', r'werkzeug', r'flask.app'],
            'django': [r'django', r'csrf', r'settings.DEBUG'],
            'express': [r'express', r'node.js', r'errorhandler'],
            'rails': [r'rails', r'ruby', r'actioncontroller'],
            'php': [r'php', r'warning', r'fatal error'],
            'python': [r'python', r'traceback', r'file.*line']
        }
        
        for tech, patterns in error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, response_text, re.IGNORECASE):
                    self.results['error_messages'].append({
                        'url': url,
                        'technology': tech,
                        'pattern': pattern,
                        'priority': 'MEDIUM'
                    })
                    break

    def discover_api_endpoints(self, base_url):
        """Priority 4: Discover API endpoints and chatbot-related paths"""
        self.log_message(f"🔍 Discovering API endpoints for {base_url}")
        
        api_endpoints_to_check = [
            '/api/', '/api/v1/', '/api/v2/', '/chat/', '/bot/', '/knowledge/', 
            '/database/', '/customers/', '/records/', '/internal/', '/dev/',
            '/weekend/', '/sideproject/', '/vibe/', '/knowledgebase/'
        ]
        
        discovered_endpoints = []
        
        for endpoint in api_endpoints_to_check:
            test_url = urljoin(base_url, endpoint)
            try:
                response = requests.get(test_url, timeout=8, verify=False)
                
                if response.status_code in [200, 301, 302, 403]:
                    discovered_endpoints.append({
                        'url': test_url,
                        'status': response.status_code,
                        'endpoint': endpoint,
                        'priority': 'HIGH' if '/api/' in endpoint or '/chat/' in endpoint else 'MEDIUM'
                    })
                    
                    # Check if response contains API-like content
                    if any(keyword in response.text.lower() for keyword in ['json', 'api', 'endpoint', 'database']):
                        discovered_endpoints[-1]['content_type'] = 'API-like'
            
            except requests.RequestException:
                continue
        
        if discovered_endpoints:
            self.results['api_endpoints'].extend(discovered_endpoints)
        
        return discovered_endpoints

    def check_documentation_endpoints(self, base_url):
        """Priority 5: Check for API documentation endpoints"""
        self.log_message(f"🔍 Checking documentation endpoints for {base_url}")
        
        doc_endpoints = [
            '/docs/', '/swagger/', '/redoc/', '/api-docs/', '/documentation/',
            '/swagger-ui/', '/api/swagger', '/api/docs', '/explorer/'
        ]
        
        discovered_docs = []
        
        for endpoint in doc_endpoints:
            test_url = urljoin(base_url, endpoint)
            try:
                response = requests.get(test_url, timeout=8, verify=False)
                
                if response.status_code in [200, 301, 302]:
                    discovered_docs.append({
                        'url': test_url,
                        'status': response.status_code,
                        'type': endpoint,
                        'priority': 'HIGH'
                    })
            
            except requests.RequestException:
                continue
        
        if discovered_docs:
            self.results['documentation_endpoints'].extend(discovered_docs)
        
        return discovered_docs

    def check_exposed_files(self, base_url):
        """Priority 6: Check for exposed sensitive files"""
        self.log_message(f"🔍 Checking for exposed files on {base_url}")
        
        exposed_files_found = []
        
        for filename in self.sensitive_files:
            test_url = urljoin(base_url, filename)
            try:
                response = requests.get(test_url, timeout=8, verify=False)
                
                if response.status_code == 200:
                    file_info = {
                        'url': test_url,
                        'status': response.status_code,
                        'filename': filename,
                        'priority': 'CRITICAL',
                        'size': len(response.content)
                    }
                    
                    # Check file content for interesting data
                    content_preview = response.text[:200].lower()
                    if any(keyword in content_preview for keyword in ['password', 'secret', 'key', 'flag', 'database']):
                        file_info['sensitive_content'] = True
                    
                    exposed_files_found.append(file_info)
            
            except requests.RequestException:
                continue
        
        if exposed_files_found:
            self.results['exposed_files'].extend(exposed_files_found)
        
        return exposed_files_found

    def search_for_flags(self, url, content):
        """Search for potential flag patterns in content"""
        # Common CTF flag patterns
        flag_patterns = [
            r'flag\{[^}]+\}',
            r'FLAG\{[^}]+\}',
            r'ackme\{[^}]+\}',
            r'ACKME\{[^}]+\}',
            r'ctf\{[^}]+\}',
            r'CTF\{[^}]+\}',
            r'[a-f0-9]{32}',  # MD5-like
            r'[A-Z0-9]{32}',  # Uppercase hash
        ]
        
        for pattern in flag_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                self.results['potential_flags'].append({
                    'url': url,
                    'flag_pattern': match,
                    'pattern': pattern,
                    'priority': 'CRITICAL'
                })

    def investigate_url(self, url):
        """Comprehensive investigation of a single URL"""
        self.log_message(f"🚀 Investigating: {url}")
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        findings = {
            'url': url,
            'headers_analysis': [],
            'api_endpoints': [],
            'documentation': [],
            'exposed_files': [],
            'technologies': []
        }
        
        try:
            # Analyze headers and get response
            headers, content = self.analyze_response_headers(url)
            
            # Examine error messages for technology stack
            self.examine_error_messages(url, content)
            
            # Search for flags in content
            self.search_for_flags(url, content)
            
            # Discover API endpoints
            api_findings = self.discover_api_endpoints(url)
            findings['api_endpoints'] = api_findings
            
            # Check documentation endpoints
            doc_findings = self.check_documentation_endpoints(url)
            findings['documentation'] = doc_findings
            
            # Check for exposed files
            file_findings = self.check_exposed_files(url)
            findings['exposed_files'] = file_findings
            
        except Exception as e:
            self.log_message(f"❌ Error investigating {url}: {e}")
        
        return findings

    def generate_report(self):
        """Generate a comprehensive investigation report"""
        report = f"""
=== ACK-ME CORP CTF INVESTIGATION REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Domain: {self.domain}

CRITICAL FINDINGS:
==================

UNUSUAL SUBDOMAINS ({len(self.results['unusual_subdomains'])}):
{'-' * 50}
"""
        for subdomain in self.results['unusual_subdomains']:
            report += f"• {subdomain['subdomain']} - {subdomain['reason']} [{subdomain['priority']}]\n"

        report += f"""
SUSPICIOUS HEADERS ({len(self.results['suspicious_headers'])}):
{'-' * 50}
"""
        for header in self.results['suspicious_headers']:
            report += f"• {header['url']} - {header['technology']} [{header['priority']}]\n"

        report += f"""
API ENDPOINTS ({len(self.results['api_endpoints'])}):
{'-' * 50}
"""
        for endpoint in self.results['api_endpoints']:
            report += f"• {endpoint['url']} - Status: {endpoint['status']} [{endpoint['priority']}]\n"

        report += f"""
DOCUMENTATION ENDPOINTS ({len(self.results['documentation_endpoints'])}):
{'-' * 50}
"""
        for doc in self.results['documentation_endpoints']:
            report += f"• {doc['url']} - Status: {doc['status']} [{doc['priority']}]\n"

        report += f"""
EXPOSED FILES ({len(self.results['exposed_files'])}):
{'-' * 50}
"""
        for file in self.results['exposed_files']:
            report += f"• {file['url']} - Size: {file['size']} bytes [{file['priority']}]\n"

        report += f"""
TECHNOLOGY STACK CLUES:
{'-' * 50}
"""
        tech_stack = list(set(self.results['technology_stack']))
        for tech in tech_stack:
            report += f"• {tech}\n"

        report += f"""
POTENTIAL FLAGS ({len(self.results['potential_flags'])}):
{'-' * 50}
"""
        for flag in self.results['potential_flags']:
            report += f"• {flag['url']} - Pattern: {flag['flag_pattern']} [{flag['priority']}]\n"

        report += f"""
NEXT STEPS RECOMMENDED:
1. Investigate CRITICAL priority findings first
2. Check authentication on API endpoints
3. Examine exposed files for credentials
4. Test documentation endpoints for API access
5. Look for developer comments in source code

TOTAL FINDINGS: {sum(len(v) for v in self.results.values())}
"""
        return report

    def run_investigation(self, subdomains_file="live_subdomains.txt"):
        """Main investigation runner"""
        self.log_message("🚀 Starting CTF Investigation")
        
        # Load subdomains
        all_subdomains = self.load_subdomains_from_file(subdomains_file)
        if not all_subdomains:
            self.log_message("❌ No subdomains to investigate")
            return
        
        # Prioritize unusual subdomains
        unusual_subdomains = self.prioritize_unusual_subdomains(all_subdomains)
        
        # Investigate all subdomains (with focus on unusual ones)
        targets_to_investigate = unusual_subdomains + all_subdomains
        targets_to_investigate = list(dict.fromkeys(targets_to_investigate))  # Remove duplicates
        
        self.log_message(f"🎯 Investigating {len(targets_to_investigate)} targets")
        
        # Use threading for faster investigation (limited to 5 concurrent requests)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.investigate_url, target) for target in targets_to_investigate]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.log_message(f"❌ Thread error: {e}")
        
        # Generate and save report
        report = self.generate_report()
        
        with open('ctf_investigation_report.txt', 'w') as f:
            f.write(report)
        
        self.log_message("✅ Investigation complete! Report saved to: ctf_investigation_report.txt")
        
        # Print critical findings immediately
        print("\n" + "="*60)
        print("🚨 CRITICAL FINDINGS SUMMARY:")
        print("="*60)
        
        critical_items = []
        for category, items in self.results.items():
            for item in items:
                if item.get('priority') in ['CRITICAL', 'HIGH']:
                    critical_items.append(item)
        
        for item in sorted(critical_items, key=lambda x: x.get('priority', ''), reverse=True):
            print(f"• {item.get('url', 'N/A')} - {item.get('reason', item.get('technology', 'Finding'))} [{item.get('priority')}]")
        
        if not critical_items:
            print("No critical findings detected. Check the full report for details.")

def main():
    """Main execution function"""
    # Disable SSL warnings for cleaner output
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    investigator = CTFInvestigator()
    
    try:
        investigator.run_investigation()
    except KeyboardInterrupt:
        print("\n⚠️  Investigation interrupted by user")
    except Exception as e:
        print(f"❌ Investigation failed: {e}")

if __name__ == "__main__":
    main()
