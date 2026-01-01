#!/usr/bin/env python3
"""
Auto Risk Score Updater
========================

This script automatically:
1. Reads all available APs from mock data
2. Gets metrics for each AP (from wireless_channel_utilization, usage_history, etc.)
3. Calculates risk scores using the calculate_risk_score.py logic
4. Updates agent_data/risk_scores.json every 10 seconds

Run: python scripts/auto_risk_score_updater.py --continuous 10
"""

import json
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.calculate_risk_score import calculate_ap_risk_score, classify_risk, get_risk_indicator

# File paths
MOCK_DATA_FILE = PROJECT_ROOT / "mock_data" / "comprehensive_api_data.json"
RISK_SCORES_FILE = PROJECT_ROOT / "agent_data" / "risk_scores.json"


def load_mock_data() -> Dict[str, Any]:
    """Load the comprehensive mock data"""
    try:
        with open(MOCK_DATA_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading mock data: {e}")
        return {}


def load_existing_risk_scores() -> Dict[str, Any]:
    """Load existing risk scores to preserve history"""
    try:
        if RISK_SCORES_FILE.exists():
            with open(RISK_SCORES_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return json.load(f)
    except Exception as e:
        print(f"⚠️ Could not load existing risk scores: {e}")
    return {}


def get_all_aps(mock_data: Dict[str, Any]) -> list:
    """Extract all AP devices from mock data"""
    aps = []
    
    # Get from organization_devices
    org_devices = mock_data.get("organization_devices", {})
    for org_id, devices in org_devices.items():
        for device in devices:
            if device.get("model", "").startswith("MR"):  # Meraki wireless APs
                aps.append({
                    "serial": device.get("serial"),
                    "name": device.get("name"),
                    "model": device.get("model"),
                    "lat": device.get("lat"),
                    "lng": device.get("lng"),
                    "networkId": device.get("networkId")
                })
    
    return aps


def get_ap_metrics(ap_serial: str, mock_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract metrics for an AP from various mock data sources.
    
    Sources:
    - wireless_channel_utilization: retransmissions, SNR, client count
    - network_wireless_usage_history: latency-related data
    - device_wireless_status: radio SNR, client count
    """
    metrics = {
        "latency_ms": None,
        "jitter_ms": None,
        "retrans_per_min": None,
        "snr_db": None,
        "client_count": None,
        "auth_failures_per_hour": None,
        "ap_name": None
    }
    
    # 1. Get from wireless_channel_utilization (most comprehensive)
    channel_util = mock_data.get("wireless_channel_utilization", [])
    for ap_data in channel_util:
        if ap_data.get("serial") == ap_serial:
            metrics["ap_name"] = ap_data.get("name")
            metrics["client_count"] = ap_data.get("clientCount")
            metrics["retrans_per_min"] = ap_data.get("retransmissions", {}).get("perMinute")
            
            # Get SNR from signalToNoiseRatio section
            snr_data = ap_data.get("signalToNoiseRatio", {})
            if snr_data:
                # Average the SNR values if multiple
                snr_values = [v for v in snr_data.values() if isinstance(v, (int, float))]
                if snr_values:
                    metrics["snr_db"] = sum(snr_values) / len(snr_values)
            
            # Check status note for failure simulation
            note = ap_data.get("note", "")
            if "FAILURE" in note:
                # Simulate degraded metrics for failing APs
                metrics["retrans_per_min"] = max(metrics.get("retrans_per_min") or 0, 45)
                if metrics["snr_db"]:
                    metrics["snr_db"] = min(metrics["snr_db"], 18)
            break
    
    # 2. Get additional data from device_wireless_status
    wireless_status = mock_data.get("device_wireless_status", {}).get(ap_serial, {})
    if wireless_status:
        # Get best SNR from radios
        radio0 = wireless_status.get("radio0", {})
        radio1 = wireless_status.get("radio1", {})
        
        radio_snrs = []
        if radio0.get("snr"):
            radio_snrs.append(radio0["snr"])
        if radio1.get("snr"):
            radio_snrs.append(radio1["snr"])
        
        if radio_snrs and not metrics["snr_db"]:
            metrics["snr_db"] = sum(radio_snrs) / len(radio_snrs)
        
        # Sum client counts from both radios
        if not metrics["client_count"]:
            client_count = 0
            if radio0.get("clientCount"):
                client_count += radio0["clientCount"]
            if radio1.get("clientCount"):
                client_count += radio1["clientCount"]
            if client_count > 0:
                metrics["client_count"] = client_count
    
    # 3. Get latest data from usage history
    network_id = None
    for org_devices in mock_data.get("organization_devices", {}).values():
        for device in org_devices:
            if device.get("serial") == ap_serial:
                network_id = device.get("networkId")
                if not metrics["ap_name"]:
                    metrics["ap_name"] = device.get("name")
                break
    
    if network_id:
        usage_history = mock_data.get("network_wireless_usage_history", {}).get(network_id, [])
        # Get latest entries for this AP
        ap_usage = [u for u in usage_history if u.get("deviceSerial") == ap_serial]
        if ap_usage:
            latest = ap_usage[-1]  # Most recent
            if not metrics["retrans_per_min"]:
                metrics["retrans_per_min"] = latest.get("retransmissionsPerMinute")
            if not metrics["snr_db"]:
                metrics["snr_db"] = latest.get("avgSignalToNoise")
            if not metrics["client_count"]:
                metrics["client_count"] = latest.get("clientCount")
    
    # 4. Check for failed connections (auth failures)
    if network_id:
        failed_conns = mock_data.get("network_wireless_failed_connections", {}).get(network_id, [])
        # Find MAC address for this AP
        ap_mac = None
        device_details = mock_data.get("device_details", {}).get(ap_serial, {})
        if device_details:
            ap_mac = device_details.get("mac")
        
        if ap_mac:
            auth_failures = len([f for f in failed_conns if f.get("apMac") == ap_mac])
            if auth_failures > 0:
                # Estimate per hour (assuming data covers 1 hour)
                metrics["auth_failures_per_hour"] = auth_failures
    
    return metrics


def calculate_and_update_risk_scores(existing_scores: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate risk scores for all APs and update the data structure"""
    
    mock_data = load_mock_data()
    if not mock_data:
        print("❌ No mock data available")
        return existing_scores
    
    aps = get_all_aps(mock_data)
    if not aps:
        print("❌ No APs found in mock data")
        return existing_scores
    
    print(f"\n📊 Calculating risk scores for {len(aps)} APs...")
    
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    for ap in aps:
        ap_serial = ap["serial"]
        ap_name = ap["name"]
        
        # Get metrics from mock data
        metrics = get_ap_metrics(ap_serial, mock_data)
        
        # Calculate risk score
        result = calculate_ap_risk_score(
            ap_serial=ap_serial,
            ap_name=ap_name or metrics.get("ap_name"),
            latency_ms=metrics.get("latency_ms"),
            jitter_ms=metrics.get("jitter_ms"),
            retrans_per_min=metrics.get("retrans_per_min"),
            snr_db=metrics.get("snr_db"),
            client_count=metrics.get("client_count"),
            auth_failures_per_hour=metrics.get("auth_failures_per_hour"),
            timestamp=timestamp
        )
        
        # Prepare entry for this AP
        current_entry = {
            "timestamp": timestamp,
            "risk_score": result["risk_score"],
            "risk_classification": result["risk_classification"],
            "metrics": result["metrics"]
        }
        
        # Update or create AP entry
        if ap_serial in existing_scores:
            # Append to history (keep last 100 entries)
            history = existing_scores[ap_serial].get("history", [])
            history.append(current_entry)
            if len(history) > 100:
                history = history[-100:]
            
            existing_scores[ap_serial]["history"] = history
            existing_scores[ap_serial]["current"] = current_entry
            existing_scores[ap_serial]["last_updated"] = timestamp
        else:
            # New AP entry
            existing_scores[ap_serial] = {
                "ap_serial": ap_serial,
                "history": [current_entry],
                "current": current_entry,
                "last_updated": timestamp
            }
        
        # Print status
        indicator = result["risk_indicator"]
        print(f"   {indicator} {ap_name} ({ap_serial}): {result['risk_score']} - {result['risk_classification']}")
    
    return existing_scores


def save_risk_scores(data: Dict[str, Any]):
    """Save risk scores to JSON file atomically"""
    try:
        # Ensure directory exists
        RISK_SCORES_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temp file first, then rename (atomic on most systems)
        temp_file = RISK_SCORES_FILE.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Rename to actual file
        temp_file.replace(RISK_SCORES_FILE)
        
    except Exception as e:
        print(f"❌ Error saving risk scores: {e}")


def run_once():
    """Run a single calculation cycle"""
    print(f"\n{'='*60}")
    print(f"🔄 Auto Risk Score Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    existing_scores = load_existing_risk_scores()
    updated_scores = calculate_and_update_risk_scores(existing_scores)
    save_risk_scores(updated_scores)
    
    print(f"\n✅ Risk scores updated and saved to {RISK_SCORES_FILE}")


def run_continuous(interval: int = 10):
    """Run continuously with specified interval"""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║     AUTO RISK SCORE UPDATER - CONTINUOUS MODE                ║
╠══════════════════════════════════════════════════════════════╣
║  Reading from: mock_data/comprehensive_api_data.json         ║
║  Writing to:   agent_data/risk_scores.json                   ║
║  Interval:     {interval} seconds                                     ║
║  Press Ctrl+C to stop                                        ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    try:
        while True:
            run_once()
            print(f"\n⏳ Next update in {interval} seconds...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n🛑 Auto Risk Score Updater stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="Auto-update risk scores from mock data"
    )
    parser.add_argument(
        "--continuous", 
        type=int, 
        nargs="?", 
        const=10,
        metavar="SECONDS",
        help="Run continuously with specified interval (default: 10 seconds)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit"
    )
    
    args = parser.parse_args()
    
    if args.continuous:
        run_continuous(args.continuous)
    else:
        run_once()


if __name__ == "__main__":
    main()
