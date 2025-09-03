import os
from locust import HttpUser, task, constant_pacing

# Inline configuration overrides (set these to force specific IDs/host)
# Example: ORG_ID = "12345"  NETWORK_ID = "N_67890"
ORG_ID="999781"
NETWORK_ID="L_3947405073390239794"
HOST = "http://127.0.0.1:5000"

#locust -f locustfile.py --host http://127.0.0.1:5000 --headless -u 3 -r 1   how to run this

class APIUser(HttpUser):
    host = HOST
    wait_time = constant_pacing(1.0)

    def on_start(self):
        # Prefer inline constants, then environment variables; fallback to discovery
        self.organization_id = ORG_ID or os.getenv("ORG_ID") or None
        self.network_id = NETWORK_ID or os.getenv("NETWORK_ID") or None

        if not self.organization_id:
            orgs = self._get_json("/organizations") or []
            if isinstance(orgs, dict):
                orgs = orgs.get("items") or orgs.get("organizations") or []
            if orgs:
                first_org = orgs[0]
                self.organization_id = first_org.get("id") if isinstance(first_org, dict) else first_org

        if not self.network_id and self.organization_id:
            nets = self._get_json(f"/organizations/{self.organization_id}/networks") or []
            if isinstance(nets, dict):
                nets = nets.get("items") or nets.get("networks") or []
            if nets:
                first_net = nets[0]
                self.network_id = first_net.get("id") if isinstance(first_net, dict) else first_net

        if not self.network_id:
            nets = self._get_json("/networks") or []
            if isinstance(nets, dict):
                # handle dict keyed by networkId
                if nets.get("items") or nets.get("networks"):
                    nets = nets.get("items") or nets.get("networks") or []
                else:
                    first_key = next(iter(nets.keys()), None)
                    if first_key:
                        self.network_id = first_key
            if not self.network_id and isinstance(nets, list) and nets:
                first_net = nets[0]
                self.network_id = first_net.get("id") if isinstance(first_net, dict) else first_net

        # One-time visibility for troubleshooting
        print(f"[Locust] Using ORG_ID={self.organization_id} NETWORK_ID={self.network_id}")

    def _get_json(self, path):
        with self.client.get(path, name=path, catch_response=True) as r:
            try:
                return r.json()
            except Exception:
                return None

    @task
    def sweep_all_endpoints(self):
        # Always hit general endpoints
        self.client.get("/")
        self.client.get("/organizations")
        self.client.get("/networks")

        # Resolve effective IDs from runtime state, inline constants, or env
        effective_org_id = self.organization_id or ORG_ID or os.getenv("ORG_ID")
        effective_net_id = self.network_id or NETWORK_ID or os.getenv("NETWORK_ID")
        if not effective_net_id:
            # last-resort attempt every cycle if missing
            nets = self._get_json("/networks") or {}
            if isinstance(nets, dict) and nets:
                effective_net_id = next(iter(nets.keys()), None)

        # Network-scoped endpoints when a network is known
        if effective_net_id:
            self.client.get(f"/networks/{effective_net_id}/clients")
            self.client.get(f"/networks/{effective_net_id}/traffic")
            self.client.get(f"/networks/{effective_net_id}/events")
            self.client.get(f"/networks/{effective_net_id}/settings")
            self.client.get(f"/networks/{effective_net_id}/groupPolicies")
            self.client.get(
                f"/networks/{effective_net_id}/appliance/connectivityMonitoringDestinations"
            )
            self.client.get(
                f"/networks/{effective_net_id}/appliance/security/intrusion"
            )

        # Organization-scoped endpoints when an organization is known
        if effective_org_id:
            self.client.get(
                f"/organizations/{effective_org_id}/uplinks/statuses"
            )
            self.client.get(
                f"/organizations/{effective_org_id}/appliance/vpn/stats"
            )