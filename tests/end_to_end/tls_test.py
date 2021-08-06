import os

from tests.util.test_util import getClientTlsCertificates, get_tsl_certificate
from xrdsst.controllers.tls import TlsController
from xrdsst.controllers.client import ClientController
from xrdsst.core.definitions import ROOT_DIR
from xrdsst.main import XRDSSTTest


class TlsTest:

    def __init__(self, end_to_end_tests):
        self.test = end_to_end_tests

    def step_cert_download_internal_tls(self):
        with XRDSSTTest() as app:
            tls_controller = TlsController()
            tls_controller.app = app
            for security_server in self.test.config["security_server"]:
                ss_configuration = tls_controller.create_api_config(security_server, self.test.config)
                result = tls_controller.remote_download_internal_tls(ss_configuration, security_server)
                assert len(result) == 1

    def step_import_tls_certificate(self):
        tls_certificate = "tests/resources/cert.pem"
        for security_server in self.test.config["security_server"]:
            security_server["tls_certificates"] = [os.path.join(ROOT_DIR, tls_certificate)]
            for client in security_server["clients"]:
                if "tls_certificates" in client:
                    client["tls_certificates"] = [os.path.join(ROOT_DIR, tls_certificate)]
        with XRDSSTTest() as app:
            client_controller = ClientController()
            client_controller.app = app
            ssn = 0
            for security_server in self.test.config["security_server"]:
                configuration = client_controller.create_api_config(security_server, self.test.config)
                client_conf = {
                    "member_name": security_server["owner_dn_org"],
                    "member_code": security_server["owner_member_code"],
                    "member_class": security_server["owner_member_class"]
                }
                client_controller.remote_import_tls_certificate(configuration, security_server["tls_certificates"], client_conf)

                if "clients" in security_server:
                    for client in security_server["clients"]:
                        if "tls_certificates" in client:
                            client_controller.remote_import_tls_certificate(configuration, client["tls_certificates"], client)
                            tls_certs = getClientTlsCertificates(self.test.config, client, ssn)
                            assert len(tls_certs) == 1
                ssn = ssn + 1

    def step_generate_new_key(self):
        with XRDSSTTest() as app:
            tls_controller = TlsController()
            tls_controller.app = app
            ssn = 0
            for security_server in self.test.config["security_server"]:
                ss_configuration = tls_controller.create_api_config(security_server, self.test.config)
                tls_certificate_before = get_tsl_certificate(self.test.config, ssn)
                tls_controller.remote_generate_tls_keys(ss_configuration, security_server["name"])
                tls_certificate_after = get_tsl_certificate(self.test.config, ssn)

                assert tls_certificate_before["serial"] != tls_certificate_after["serial"]


    def test_run_configuration(self):
        # self.step_import_tls_certificate()
        # self.step_cert_download_internal_tls()
        self.step_generate_new_key()

