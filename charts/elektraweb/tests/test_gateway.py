import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml


CHART = Path(__file__).resolve().parents[1]
HELM = os.environ.get("HELM_BIN") or shutil.which("helm")


def render(values=None, namespace="hotel", kube_version="1.35.0"):
    if not HELM:
        raise RuntimeError("Install Helm or set HELM_BIN to the Helm executable")
    with tempfile.TemporaryDirectory() as directory:
        overrides = Path(directory) / "values.yaml"
        overrides.write_text(yaml.safe_dump(values or {}), encoding="utf-8")
        result = subprocess.run(
            [
                HELM, "template", "elektraweb", str(CHART),
                "--namespace", namespace, "--kube-version", kube_version,
                "--values", str(overrides),
            ],
            check=True, capture_output=True, text=True, encoding="utf-8",
        )
    return [doc for doc in yaml.safe_load_all(result.stdout) if doc]


def resources(documents, kind):
    return [doc for doc in documents if doc["kind"] == kind]


def named(documents, kind, name):
    return next(
        doc for doc in resources(documents, kind)
        if doc["metadata"]["name"] == name
    )


def all_features():
    return {
        "fileUploader": {"install": True},
        "onlineBooking": {"install": True},
        "callcenterintegration": {"install": True},
        "dashboardAccess": {"gateway": {"enabled": True}},
    }


class GatewayTests(unittest.TestCase):
    def assert_routing_contract(self, documents, namespace="hotel"):
        gateways = resources(documents, "Gateway")
        self.assertEqual(len(gateways), 1)
        gateway = gateways[0]
        self.assertEqual(gateway["apiVersion"], "gateway.networking.k8s.io/v1")
        self.assertEqual(gateway["metadata"]["namespace"], namespace)
        listeners = {item["name"]: item for item in gateway["spec"]["listeners"]}
        services = {
            (doc["metadata"].get("namespace", namespace), doc["metadata"]["name"]): doc
            for doc in resources(documents, "Service")
        }
        for route in resources(documents, "HTTPRoute"):
            self.assertEqual(route["apiVersion"], "gateway.networking.k8s.io/v1")
            self.assertEqual(route["metadata"]["namespace"], namespace)
            for parent in route["spec"]["parentRefs"]:
                self.assertEqual(parent["name"], gateway["metadata"]["name"])
                listener = listeners[parent["sectionName"]]
                self.assertEqual(
                    listener["allowedRoutes"]["namespaces"]["from"], "Same"
                )
                if listener["protocol"] == "HTTPS":
                    self.assertIn(listener["hostname"], route["spec"]["hostnames"])
            for rule in route["spec"]["rules"]:
                for backend in rule.get("backendRefs", []):
                    if backend["name"] == "kubernetes-dashboard":
                        continue  # Optional backend supplied by the cluster.
                    service = services[
                        (backend.get("namespace", namespace), backend["name"])
                    ]
                    self.assertIn(
                        backend["port"],
                        [port["port"] for port in service["spec"]["ports"]],
                    )
        self.assertFalse(resources(documents, "Ingress"))
        self.assertFalse(resources(documents, "VirtualService"))

    def test_default_local_gateway(self):
        documents = render()
        self.assert_routing_contract(documents)
        self.assertEqual(len(resources(documents, "HTTPRoute")), 5)
        self.assertFalse(resources(documents, "Certificate"))
        gateway = named(documents, "Gateway", "elektraweb-gateway")
        self.assertEqual(
            gateway["metadata"]["annotations"]["networking.istio.io/service-type"],
            "ClusterIP",
        )
        options = named(documents, "ConfigMap", "elektraweb-gateway-options")["data"]
        deployment = yaml.safe_load(options["deployment"])["spec"]
        self.assertEqual(deployment["replicas"], 1)
        self.assertEqual(deployment["strategy"], {
            "type": "Recreate", "rollingUpdate": None,
        })
        pod = deployment["template"]["spec"]
        self.assertIs(pod["hostNetwork"], True)
        self.assertEqual(pod["dnsPolicy"], "ClusterFirstWithHostNet")
        self.assertEqual(pod["securityContext"]["sysctls"], [])
        security = pod["containers"][0]["securityContext"]
        self.assertEqual(security["runAsUser"], 0)
        self.assertIs(security["runAsNonRoot"], False)
        self.assertIs(security["privileged"], False)
        self.assertIs(security["allowPrivilegeEscalation"], False)
        self.assertEqual(security["capabilities"], {
            "drop": ["ALL"], "add": ["NET_BIND_SERVICE"],
        })
        self.assertNotIn("horizontalPodAutoscaler", options)

    def test_all_features_share_one_gateway(self):
        documents = render(all_features())
        self.assert_routing_contract(documents)
        self.assertEqual(len(resources(documents, "HTTPRoute")), 8)
        gateway = resources(documents, "Gateway")[0]
        self.assertEqual(len(gateway["spec"]["listeners"]), 8)
        callcenter = named(documents, "HTTPRoute", "call-center-integration")
        rule = callcenter["spec"]["rules"][0]
        self.assertEqual(rule["timeouts"]["request"], "3600s")
        self.assertEqual(rule["filters"][0]["type"], "CORS")
        self.assertEqual(rule["filters"][0]["cors"]["maxAge"], 600)

    def test_files_route_is_optional_and_more_specific(self):
        route = named(render(), "HTTPRoute", "nodejs-http")
        self.assertEqual(len(route["spec"]["rules"]), 1)
        documents = render({"fileUploader": {"install": True}})
        route = named(documents, "HTTPRoute", "nodejs-http")
        files, catch_all = route["spec"]["rules"]
        self.assertEqual(files["matches"][0]["path"], {
            "type": "PathPrefix", "value": "/files",
        })
        self.assertEqual(files["backendRefs"], [{"name": "file-uploader", "port": 80}])
        self.assertEqual(files["timeouts"]["request"], "600s")
        cors = files["filters"][0]["cors"]
        self.assertEqual(cors["maxAge"], 86400)
        self.assertIn("Authorization", cors["allowHeaders"])
        self.assertIn("PUT", cors["allowMethods"])
        self.assertEqual(catch_all["backendRefs"], [{"name": "nodejs-http", "port": 8080}])
        self.assertEqual(catch_all["timeouts"]["request"], "600s")

    def test_http_redirect_and_plain_http_mode(self):
        documents = render()
        redirect = named(documents, "HTTPRoute", "elektraweb-gateway-https-redirect")
        self.assertEqual(redirect["spec"]["parentRefs"][0]["sectionName"], "http")
        self.assertEqual(redirect["spec"]["rules"][0]["filters"][0], {
            "type": "RequestRedirect",
            "requestRedirect": {"scheme": "https", "port": 443, "statusCode": 301},
        })
        documents = render({"istio": {"httpsRedirect": False}})
        self.assert_routing_contract(documents)
        self.assertEqual(len(resources(documents, "HTTPRoute")), 4)
        for route in resources(documents, "HTTPRoute"):
            self.assertEqual(
                [parent["sectionName"] for parent in route["spec"]["parentRefs"]],
                ["https-" + {
                    "nodejs-http": "worker", "angus": "angus",
                    "pos-ng11": "pos", "reportingcore": "reporting",
                }[route["metadata"]["name"]], "http"],
            )

    def test_cloud_preserves_unprivileged_defaults(self):
        annotations = {"service.beta.kubernetes.io/port_443_health-probe_port": "15021"}
        documents = render({"istio": {"gateway": {
            "hostNetwork": False, "replicas": 2,
            "serviceAnnotations": annotations,
        }}})
        self.assert_routing_contract(documents)
        gateway = resources(documents, "Gateway")[0]
        self.assertEqual(
            gateway["metadata"]["annotations"]["networking.istio.io/service-type"],
            "LoadBalancer",
        )
        self.assertEqual(gateway["spec"]["infrastructure"]["annotations"], annotations)
        options = named(documents, "ConfigMap", "elektraweb-gateway-options")["data"]
        deployment = yaml.safe_load(options["deployment"])["spec"]
        self.assertEqual(deployment["replicas"], 2)
        self.assertNotIn("strategy", deployment)
        self.assertEqual(deployment["template"]["spec"], {"hostNetwork": False})
        self.assertNotIn("horizontalPodAutoscaler", options)

    def test_custom_name_namespace_and_node(self):
        documents = render({"istio": {"gateway": {
            "name": "hotel-edge", "nodeSelector": {"kubernetes.io/hostname": "hotel-01"},
        }}}, namespace="custom")
        self.assert_routing_contract(documents, namespace="custom")
        gateway = named(documents, "Gateway", "hotel-edge")
        self.assertEqual(
            gateway["spec"]["infrastructure"]["parametersRef"]["name"],
            "hotel-edge-options",
        )
        options = named(documents, "ConfigMap", "hotel-edge-options")["data"]
        pod = yaml.safe_load(options["deployment"])["spec"]["template"]["spec"]
        self.assertEqual(pod["nodeSelector"], {"kubernetes.io/hostname": "hotel-01"})

    def test_certificates_match_every_tls_listener(self):
        values = all_features()
        for key in ("worker", "angus", "pos", "reporting", "onlineBooking",
                    "callcenterintegration"):
            values.setdefault(key, {})["sslClusterIssuer"] = "letsencrypt-prod"
        values["dashboardAccess"]["gateway"]["sslIssuer"] = "internal-ca"
        documents = render(values)
        self.assert_routing_contract(documents)
        certificates = resources(documents, "Certificate")
        self.assertEqual(len(certificates), 7)
        by_secret = {cert["spec"]["secretName"]: cert for cert in certificates}
        gateway = resources(documents, "Gateway")[0]
        for listener in gateway["spec"]["listeners"]:
            if listener["protocol"] != "HTTPS":
                continue
            cert = by_secret[listener["tls"]["certificateRefs"][0]["name"]]
            self.assertIn(listener["hostname"], cert["spec"]["dnsNames"])
            self.assertEqual(cert["metadata"]["namespace"], "hotel")
        dashboard = named(documents, "Certificate", "dashboard-cert")
        self.assertEqual(dashboard["spec"]["issuerRef"], {
            "name": "internal-ca", "kind": "Issuer",
        })

    def test_shared_certificate_combines_hostnames(self):
        values = {
            "worker": {"tlsSecretName": "shared", "sslClusterIssuer": "prod"},
            "angus": {"tlsSecretName": "shared", "sslClusterIssuer": "prod"},
        }
        certificates = resources(render(values), "Certificate")
        self.assertEqual(len(certificates), 1)
        self.assertEqual(certificates[0]["spec"]["dnsNames"], ["nodejs4001", "elektraweb"])

    def test_dashboard_cross_namespace_permissions_and_backend_tls(self):
        documents = render({"dashboardAccess": {"gateway": {"enabled": True}}})
        grant = named(documents, "ReferenceGrant", "kubernetes-dashboard")
        self.assertEqual(grant["metadata"]["namespace"], "kube-system")
        self.assertEqual(grant["spec"]["from"], [{
            "group": "gateway.networking.k8s.io", "kind": "HTTPRoute",
            "namespace": "hotel",
        }])
        self.assertEqual(grant["spec"]["to"], [{
            "group": "", "kind": "Service", "name": "kubernetes-dashboard",
        }])
        route = named(documents, "HTTPRoute", "kubernetes-dashboard")
        self.assertEqual(route["spec"]["rules"][0]["backendRefs"], [{
            "name": "kubernetes-dashboard", "namespace": "kube-system", "port": 443,
        }])
        tls = named(documents, "DestinationRule", "kubernetes-dashboard")
        self.assertEqual(tls["metadata"]["namespace"], "hotel")
        self.assertEqual(tls["spec"]["host"],
                         "kubernetes-dashboard.kube-system.svc.cluster.local")
        self.assertEqual(tls["spec"]["trafficPolicy"]["tls"]["mode"], "SIMPLE")

    def test_dashboard_same_namespace_needs_no_grant(self):
        documents = render({
            "dashboard": {"namespace": "hotel"},
            "dashboardAccess": {"gateway": {"enabled": True}},
        })
        self.assertFalse(resources(documents, "ReferenceGrant"))
        self.assert_routing_contract(documents)

    def test_disabled_gateway_emits_no_edge_resources(self):
        values = all_features()
        values["istio"] = {"enabled": False}
        documents = render(values)
        for kind in ("Gateway", "HTTPRoute", "Certificate", "ReferenceGrant",
                     "DestinationRule", "VirtualService", "Ingress"):
            self.assertFalse(resources(documents, kind))
        self.assertTrue(resources(documents, "Deployment"))

    def test_disabled_optional_services_have_no_routes_or_listeners(self):
        documents = render({
            "angus": {"install": False}, "pos": {"install": False},
            "reporting": {"install": False},
        })
        self.assertEqual(len(resources(documents, "HTTPRoute")), 2)
        gateway = resources(documents, "Gateway")[0]
        self.assertEqual(
            [item["name"] for item in gateway["spec"]["listeners"]],
            ["http", "https-worker"],
        )

    def test_invalid_settings_fail_with_explanation(self):
        cases = [
            ({"istio": {"gateway": {"replicas": 2}}}, "must be 1 with hostNetwork"),
            ({"istio": {"gateway": {"replicas": 0}}}, "must be 1 with hostNetwork"),
            ({"istio": {"gateway": {"hostNetwork": False, "replicas": 0}}},
             "must be at least 1"),
            ({"istio": {"gateway": {"serviceType": "ExternalName"}}},
             "serviceType must be"),
            ({"angus": {"host": "nodejs4001"}}, "configured more than once"),
            ({"worker": {"host": ""}}, "worker.host is required"),
            ({
                "worker": {"tlsSecretName": "shared", "sslIssuer": "one"},
                "angus": {"tlsSecretName": "shared", "sslIssuer": "two"},
            }, "cannot use different certificate issuers"),
        ]
        for values, message in cases:
            with self.subTest(values=values):
                with self.assertRaises(subprocess.CalledProcessError) as error:
                    render(values)
                self.assertIn(message, error.exception.stderr)

    def test_unsupported_kubernetes_fails_before_install(self):
        with self.assertRaises(subprocess.CalledProcessError) as error:
            render(kube_version="1.27.0")
        self.assertIn("kubeVersion", error.exception.stderr)


if __name__ == "__main__":
    unittest.main()
