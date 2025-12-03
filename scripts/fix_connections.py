#!/usr/bin/env python3
"""
Fix Connections Script
----------------------
This script automatically sets up port-forwarding for Prometheus and Alertmanager
running in the Kubernetes cluster so the local agent can access them.
"""

import subprocess
import time
import sys
import os
import signal

def run_command(command):
    """Run a shell command."""
    try:
        subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def start_port_forward(service, namespace, local_port, remote_port):
    """Start a port-forward process in the background."""
    print(f"🔄 Setting up port-forward for {service} ({local_port}:{remote_port})...")
    
    # Kill any existing process on this port
    os.system(f"lsof -ti:{local_port} | xargs kill -9 2>/dev/null")
    
    cmd = f"kubectl port-forward -n {namespace} svc/{service} {local_port}:{remote_port}"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait a bit to ensure it started
    time.sleep(2)
    
    if process.poll() is None:
        print(f"✅ Connected to {service} on localhost:{local_port}")
        return process
    else:
        print(f"❌ Failed to connect to {service}")
        return None

def main():
    print("==========================================")
    print("🛠️  Fixing K8s Observability Connections")
    print("==========================================")
    print("")
    
    processes = []
    
    # 1. Prometheus
    # Service name usually follows kube-prometheus-stack naming convention
    # We'll try common names
    prom_services = [
        "prometheus-kube-prometheus-prometheus", 
        "prometheus-operated",
        "prometheus"
    ]
    
    prom_connected = False
    for svc in prom_services:
        p = start_port_forward(svc, "monitoring", 9090, 9090)
        if p:
            processes.append(p)
            prom_connected = True
            break
            
    if not prom_connected:
        print("⚠️  Could not find Prometheus service. Trying pod directly...")
        p = start_port_forward("prometheus-prometheus-kube-prometheus-prometheus-0", "monitoring", 9090, 9090)
        if p:
            processes.append(p)
            prom_connected = True

    # 2. Alertmanager
    alert_services = [
        "alertmanager-operated",
        "prometheus-kube-prometheus-alertmanager",
        "alertmanager"
    ]
    
    alert_connected = False
    for svc in alert_services:
        p = start_port_forward(svc, "monitoring", 9093, 9093)
        if p:
            processes.append(p)
            alert_connected = True
            break
            
    if not alert_connected:
        print("⚠️  Could not find Alertmanager service. Trying pod directly...")
        p = start_port_forward("alertmanager-prometheus-kube-prometheus-alertmanager-0", "monitoring", 9093, 9093)
        if p:
            processes.append(p)
            alert_connected = True

    print("")
    if prom_connected and alert_connected:
        print("✅ All connections fixed!")
        print("   Keep this script running while using the agent.")
        print("   Press Ctrl+C to stop.")
        
        # Keep alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping port-forwards...")
            for p in processes:
                p.terminate()
            print("Done.")
    else:
        print("❌ Failed to establish all connections.")
        for p in processes:
            p.terminate()
        sys.exit(1)

if __name__ == "__main__":
    main()
