#!/usr/bin/env python3
"""
Devin Automation Observability Dashboard

Generates and displays statistics about Devin automation performance,
including success/failure rates, PR creation rates, and session statistics.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import glob


class DevinObservability:
    """Track and analyze Devin automation performance"""
    
    def __init__(self, logs_dir: str = ".devin/logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.stats_file = self.logs_dir / "observability_stats.json"
        
    def parse_log_file(self, log_file: Path) -> Dict[str, Any]:
        """Parse a single log file and extract session information"""
        try:
            with open(log_file, 'r') as f:
                content = f.read()
            
            session_info = {
                "file": log_file.name,
                "timestamp": datetime.fromtimestamp(log_file.stat().st_mtime),
                "success": False,
                "session_id": None,
                "pr_url": None,
                "issue_number": None,
                "error": None,
                "changes": 0
            }
            
            # Extract session ID
            if "Session created:" in content:
                for line in content.split('\n'):
                    if "Session created:" in line:
                        session_info["session_id"] = line.split("Session created:")[-1].strip()
                        break
            
            # Extract success/failure
            if "Success: True" in content:
                session_info["success"] = True
            elif "Success: False" in content:
                session_info["success"] = False
            
            # Extract PR URL
            if "PR URL:" in content:
                for line in content.split('\n'):
                    if "PR URL:" in line and "None" not in line:
                        session_info["pr_url"] = line.split("PR URL:")[-1].strip()
                        break
            
            # Extract issue number from filename
            if "devin-api-result-" in log_file.name:
                parts = log_file.name.replace("devin-api-result-", "").replace(".json", "").split("-")
                if parts:
                    session_info["issue_number"] = parts[0]
            
            # Extract error
            if "Error:" in content:
                for line in content.split('\n'):
                    if "Error:" in line and "session_id" not in line.lower():
                        session_info["error"] = line.split("Error:")[-1].strip()
                        break
            
            # Extract changes count
            if "Changes:" in content:
                for line in content.split('\n'):
                    if "Changes:" in line:
                        changes_str = line.split("Changes:")[-1].strip()
                        try:
                            session_info["changes"] = int(changes_str)
                        except ValueError:
                            pass
                        break
            
            return session_info
            
        except Exception as e:
            print(f"Error parsing {log_file}: {e}")
            return None
    
    def collect_stats(self) -> Dict[str, Any]:
        """Collect statistics from all log files"""
        log_files = list(self.logs_dir.glob("devin-api-result-*.json"))
        
        sessions = []
        for log_file in log_files:
            session_info = self.parse_log_file(log_file)
            if session_info:
                sessions.append(session_info)
        
        # Calculate statistics
        total_sessions = len(sessions)
        successful_sessions = sum(1 for s in sessions if s["success"])
        failed_sessions = total_sessions - successful_sessions
        pr_created = sum(1 for s in sessions if s["pr_url"])
        
        # Time-based statistics
        now = datetime.now()
        last_24h = [s for s in sessions if now - s["timestamp"] <= timedelta(hours=24)]
        last_7d = [s for s in sessions if now - s["timestamp"] <= timedelta(days=7)]
        last_30d = [s for s in sessions if now - s["timestamp"] <= timedelta(days=30)]
        
        stats = {
            "total_sessions": total_sessions,
            "successful_sessions": successful_sessions,
            "failed_sessions": failed_sessions,
            "pr_created": pr_created,
            "success_rate": (successful_sessions / total_sessions * 100) if total_sessions > 0 else 0,
            "pr_creation_rate": (pr_created / total_sessions * 100) if total_sessions > 0 else 0,
            "last_24h": {
                "total": len(last_24h),
                "successful": sum(1 for s in last_24h if s["success"]),
                "pr_created": sum(1 for s in last_24h if s["pr_url"])
            },
            "last_7d": {
                "total": len(last_7d),
                "successful": sum(1 for s in last_7d if s["success"]),
                "pr_created": sum(1 for s in last_7d if s["pr_url"])
            },
            "last_30d": {
                "total": len(last_30d),
                "successful": sum(1 for s in last_30d if s["success"]),
                "pr_created": sum(1 for s in last_30d if s["pr_url"])
            },
            "recent_sessions": sorted(sessions, key=lambda x: x["timestamp"], reverse=True)[:10]
        }
        
        return stats
    
    def generate_html_dashboard(self, stats: Dict[str, Any]) -> str:
        """Generate an HTML dashboard"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Devin Automation Observability Dashboard</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .dashboard {{
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}
        .stat-card.success {{
            border-left-color: #28a745;
        }}
        .stat-card.warning {{
            border-left-color: #ffc107;
        }}
        .stat-card.danger {{
            border-left-color: #dc3545;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .session-list {{
            margin-top: 30px;
        }}
        .session-item {{
            background: #f8f9fa;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 4px solid #ddd;
        }}
        .session-item.success {{
            border-left-color: #28a745;
        }}
        .session-item.failure {{
            border-left-color: #dc3545;
        }}
        .session-time {{
            color: #666;
            font-size: 0.85em;
        }}
        .session-pr {{
            color: #007bff;
            margin-top: 5px;
        }}
        .session-error {{
            color: #dc3545;
            margin-top: 5px;
            font-size: 0.9em;
        }}
        .time-period {{
            margin: 10px 0;
            padding: 10px;
            background: #e9ecef;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>Devin Automation Observability Dashboard</h1>
        <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['total_sessions']}</div>
                <div class="stat-label">Total Sessions</div>
            </div>
            <div class="stat-card success">
                <div class="stat-value">{stats['successful_sessions']}</div>
                <div class="stat-label">Successful Sessions</div>
            </div>
            <div class="stat-card danger">
                <div class="stat-value">{stats['failed_sessions']}</div>
                <div class="stat-label">Failed Sessions</div>
            </div>
            <div class="stat-card success">
                <div class="stat-value">{stats['pr_created']}</div>
                <div class="stat-label">PRs Created</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['success_rate']:.1f}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['pr_creation_rate']:.1f}%</div>
                <div class="stat-label">PR Creation Rate</div>
            </div>
        </div>
        
        <h2>Time Period Analysis</h2>
        <div class="time-period">
            <strong>Last 24 Hours:</strong> {stats['last_24h']['total']} sessions, 
            {stats['last_24h']['successful']} successful, {stats['last_24h']['pr_created']} PRs created
        </div>
        <div class="time-period">
            <strong>Last 7 Days:</strong> {stats['last_7d']['total']} sessions, 
            {stats['last_7d']['successful']} successful, {stats['last_7d']['pr_created']} PRs created
        </div>
        <div class="time-period">
            <strong>Last 30 Days:</strong> {stats['last_30d']['total']} sessions, 
            {stats['last_30d']['successful']} successful, {stats['last_30d']['pr_created']} PRs created
        </div>
        
        <h2>Recent Sessions</h2>
        <div class="session-list">
"""
        
        for session in stats['recent_sessions']:
            status_class = "success" if session['success'] else "failure"
            status_text = "Success" if session['success'] else "Failed"
            
            html += f"""
            <div class="session-item {status_class}">
                <strong>{status_text}</strong> - Issue #{session.get('issue_number', 'Unknown')}
                <div class="session-time">{session['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</div>
"""
            
            if session.get('pr_url'):
                html += f"""
                <div class="session-pr">PR: <a href="{session['pr_url']}" target="_blank">{session['pr_url']}</a></div>
"""
            
            if session.get('error'):
                html += f"""
                <div class="session-error">Error: {session['error']}</div>
"""
            
            html += """
            </div>
"""
        
        html += """
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def generate_dashboard(self) -> str:
        """Generate and save the observability dashboard"""
        stats = self.collect_stats()
        html = self.generate_html_dashboard(stats)
        
        # Save HTML dashboard
        dashboard_file = self.logs_dir / "observability_dashboard.html"
        with open(dashboard_file, 'w') as f:
            f.write(html)
        
        # Save JSON stats
        with open(self.stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        print(f"Dashboard generated: {dashboard_file}")
        print(f"Stats saved: {self.stats_file}")
        
        return str(dashboard_file)
    
    def print_summary(self):
        """Print a text summary of the statistics"""
        stats = self.collect_stats()
        
        print("\n" + "="*50)
        print("DEVIN AUTOMATION OBSERVABILITY SUMMARY")
        print("="*50)
        print(f"Total Sessions: {stats['total_sessions']}")
        print(f"Successful: {stats['successful_sessions']} ({stats['success_rate']:.1f}%)")
        print(f"Failed: {stats['failed_sessions']}")
        print(f"PRs Created: {stats['pr_created']} ({stats['pr_creation_rate']:.1f}%)")
        print("\nTime Period Analysis:")
        print(f"   Last 24h: {stats['last_24h']['total']} sessions, {stats['last_24h']['successful']} success, {stats['last_24h']['pr_created']} PRs")
        print(f"   Last 7d:  {stats['last_7d']['total']} sessions, {stats['last_7d']['successful']} success, {stats['last_7d']['pr_created']} PRs")
        print(f"   Last 30d: {stats['last_30d']['total']} sessions, {stats['last_30d']['successful']} success, {stats['last_30d']['pr_created']} PRs")
        print("="*50 + "\n")


def main():
    """Main entry point"""
    import sys
    
    logs_dir = sys.argv[1] if len(sys.argv) > 1 else ".devin/logs"
    
    observability = DevinObservability(logs_dir)
    
    print("Collecting Devin automation statistics...")
    observability.print_summary()
    
    print("Generating HTML dashboard...")
    dashboard_path = observability.generate_dashboard()
    
    print(f"Dashboard ready! Open it in your browser: {dashboard_path}")


if __name__ == "__main__":
    main()