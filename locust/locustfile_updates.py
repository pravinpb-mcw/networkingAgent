import os
import random
from locust import HttpUser, task, between



#locust -f locustfile_updates.py

# Inline configuration overrides
ORG_ID = os.getenv("ORG_ID", "999781")
NETWORK_ID = os.getenv("NETWORK_ID", "L_3947405073390239794")
HOST = os.getenv("HOST", "http://127.0.0.1:5000")


def make_problem_like_payload(seed: int) -> dict:
    random.seed(seed)
    # Simulate real-time networking problems fields; server is flexible (pydantic extra=allow)
    return {
        "latencyMs": random.randint(50, 400),
        "packetLossPct": round(random.uniform(0.0, 8.0), 2),
        "jitterMs": random.randint(1, 50),
        "degradedLinks": [
            {"uplink": "wan1", "status": random.choice(["ok", "degraded", "down"])},
            {"uplink": "wan2", "status": random.choice(["ok", "degraded", "down"])},
        ],
        "note": "auto-load-test-update",
    }


class UpdateAPIUser(HttpUser):
    host = HOST
    # Base wait is small; we'll add dynamic backoff on successful updates
    wait_time = between(0.2, 0.8)

    def on_start(self):
        self.organization_id = ORG_ID
        self.network_id = NETWORK_ID
        self.dynamic_sleep_bonus = 0.0

    def _apply_dynamic_sleep(self, response_ok: bool):
        # Increase delay after successful update to simulate slower system
        if response_ok:
            self.dynamic_sleep_bonus = min(self.dynamic_sleep_bonus + 0.2, 5.0)
        else:
            # decay quickly when failures occur
            self.dynamic_sleep_bonus = max(self.dynamic_sleep_bonus - 0.5, 0.0)

    def _sleep_hook(self):
        # Locust's wait_time is applied automatically; we add extra delay dynamically
        if self.dynamic_sleep_bonus > 0:
            self.environment.events.request.fire(
                request_type="SLEEP",
                name="dynamic_backoff",
                response_time=int(self.dynamic_sleep_bonus * 1000),
                response_length=0,
                exception=None,
            )
            self.sleep(self.dynamic_sleep_bonus)

    def _post(self, path: str, json_body: dict):
        with self.client.post(path, name=path, json=json_body, catch_response=True) as r:
            ok = 200 <= r.status_code < 300
            if not ok:
                r.failure(f"HTTP {r.status_code}: {r.text}")
            self._apply_dynamic_sleep(ok)
        self._sleep_hook()

    def _put(self, path: str, json_body: dict):
        with self.client.put(path, name=path, json=json_body, catch_response=True) as r:
            ok = 200 <= r.status_code < 300
            if not ok:
                r.failure(f"HTTP {r.status_code}: {r.text}")
            self._apply_dynamic_sleep(ok)
        self._sleep_hook()

    # --- Tasks targeting PUT/POST endpoints ---

    @task(2)
    def post_appliance_settings(self):
        payload = make_problem_like_payload(seed=random.randint(0, 10_000))
        self._post(f"/networks/{self.network_id}/appliance/settings", payload)

    @task(2)
    def put_appliance_settings(self):
        payload = make_problem_like_payload(seed=random.randint(0, 10_000))
        self._put(f"/networks/{self.network_id}/appliance/settings", payload)

    @task(1)
    def post_wireless_settings(self):
        # Wireless settings accepts extra fields as well
        payload = make_problem_like_payload(seed=random.randint(0, 10_000))
        payload.update({"ssidHealth": {"poorClients": random.randint(0, 20)}})
        self._post(f"/networks/{self.network_id}/wireless/settings", payload)

    @task(1)
    def put_network_settings(self):
        payload = make_problem_like_payload(seed=random.randint(0, 10_000))
        payload.update({"trafficShaping": {"enabled": True}})
        self._put(f"/networks/{self.network_id}/settings", payload)

    @task(1)
    def put_group_policies(self):
        payload = {
            "name": "dynamic-policy",
            "firewallAndTrafficShaping": {
                "settings": "custom",
                "l7Rules": [
                    {"type": "deny", "value": "peer-to-peer"},
                ],
            },
        }
        self._put(f"/networks/{self.network_id}/groupPolicies", payload)

    @task(1)
    def put_connectivity_monitoring(self):
        payload = {
            "destinations": [
                {"description": "dns", "ip": "8.8.8.8"},
                {"description": "gateway", "ip": "192.168.1.1"},
            ]
        }
        self._put(
            f"/networks/{self.network_id}/appliance/connectivityMonitoringDestinations",
            payload,
        )

    @task(1)
    def put_acl(self):
        payload = {
            "rules": [
                {
                    "comment": "block-bad-hosts",
                    "policy": "deny",
                    "protocol": "any",
                    "srcCidr": "0.0.0.0/0",
                    "destCidr": "10.10.10.10/32",
                }
            ]
        }
        self._put(f"/networks/{self.network_id}/switch/accessControlLists", payload)

    @task(1)
    def put_login_security(self):
        payload = {
            "enforceTwoFactorAuth": True,
            "apiAccess": {"restricted": True},
        }
        self._put(f"/organizations/{self.organization_id}/loginSecurity", payload)

    @task(1)
    def put_security_intrusion(self):
        payload = {
            "mode": random.choice(["disabled", "detection", "prevention"]),
            "rulesets": {"balanced": True},
        }
        self._put(f"/networks/{self.network_id}/appliance/security/intrusion", payload)


