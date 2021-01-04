import os

import urllib3
from cement import ex

from xrdsst.api import KeysApi
from xrdsst.api.token_certificates_api import TokenCertificatesApi
from xrdsst.controllers.base import BaseController
from xrdsst.models import SecurityServerAddress, CsrFormat
from xrdsst.api_client.api_client import ApiClient
from xrdsst.api.tokens_api import TokensApi
from xrdsst.resources.texts import texts


from xrdsst.rest.rest import ApiException


class DownloadedCsr:
    def __init__(self, csr_id, key_id, key_type, fs_loc):
        self.csr_id = csr_id
        self.key_id = key_id
        self.key_type = key_type
        self.fs_loc = fs_loc


class DownloadedCsrListMapper:
    @staticmethod
    def headers():
        return ['CSR ID', 'KEY ID', 'TYPE', 'LOCATION']

    @staticmethod
    def as_list(dwn_csr):
        return [dwn_csr.csr_id, dwn_csr.key_id, dwn_csr.key_type, dwn_csr.fs_loc]

    @staticmethod
    def as_object(dwn_csr):
        return {
            'csr_id': dwn_csr.csr_id,
            'key_id': dwn_csr.key_id,
            'key_type': dwn_csr.key_type,
            'fs_location': dwn_csr.fs_loc
        }


class CertController(BaseController):
    class Meta:
        label = 'cert'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = texts['cert.controller.description']

    @ex(help="Import certificate(s)", label="import", arguments=[])
    def import_(self):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.import_certificates(self.load_config())

    @ex(help="Register authentication certificate(s)", arguments=[])
    def register(self):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.register_certificate(self.load_config())

    @ex(help="Activate registered centrally approved authentication certificate", arguments=[])
    def activate(self):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.activate_certificate(self.load_config())

    @ex(help="Download certificate requests for sign and auth keys, if any.", arguments=[])
    def download_csrs(self):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return self._download_csrs(self.load_config())

    def import_certificates(self, configuration):
        self.init_logging(configuration)
        for security_server in configuration["security_server"]:
            BaseController.log_info('Starting configuration process for security server: ' + security_server['name'])
            ss_configuration = self.initialize_basic_config_values(security_server, configuration)
            self.remote_import_certificates(ss_configuration, security_server)

    def register_certificate(self,  configuration):
        self.init_logging(configuration)
        for security_server in configuration["security_server"]:
            BaseController.log_info('Starting configuration process for security server: ' + security_server['name'])
            ss_configuration = self.initialize_basic_config_values(security_server, configuration)
            self.remote_register_certificate(ss_configuration, security_server)

    def activate_certificate(self,  configuration):
        self.init_logging(configuration)
        for security_server in configuration["security_server"]:
            BaseController.log_info('Starting configuration process for security server: ' + security_server['name'])
            ss_configuration = self.initialize_basic_config_values(security_server, configuration)
            self.remote_activate_certificate(ss_configuration, security_server)

    def _download_csrs(self, configuration):
        self.init_logging(configuration)
        for security_server in configuration["security_server"]:
            BaseController.log_info('Starting configuration process for security server: ' + security_server['name'])
            ss_configuration = self.initialize_basic_config_values(security_server, configuration)
            return self.remote_download_csrs(ss_configuration, security_server)

    # requires token to be logged in
    @staticmethod
    def remote_import_certificates(ss_configuration, security_server):
        import cement.utils.fs
        token_cert_api = TokenCertificatesApi(ApiClient(ss_configuration))
        for cert in security_server["certificates"]:
            location = cement.utils.fs.join_exists(cert)
            if not location[1]:
                BaseController.log_info("Certificate '" + location[0] + "' does not exist")
            else:
                certfile = location[0]
                try:
                    cert_file = open(location[0], "rb")
                    cert_data = cert_file.read()
                    cert_file.close()
                    token_cert_api.import_certificate(body=cert_data)
                except ApiException as err:
                    if err.status == 409 and err.body.count("certificate_already_exists"):
                        print("Certificate '" + certfile + "' already imported.")
                    else:
                        BaseController.log_api_error('TokenCertificatesApi->import_certificate', err)

    @staticmethod
    def remote_register_certificate(ss_configuration, security_server):
        registrable_cert = CertController.find_actionable_auth_certificate(ss_configuration, security_server, 'REGISTER')
        if not registrable_cert:
            return

        token_cert_api = TokenCertificatesApi(ApiClient(ss_configuration))
        ss_address = SecurityServerAddress(BaseController.security_server_address(security_server))
        try:
            token_cert_api.register_certificate(registrable_cert.certificate_details.hash, body=ss_address)
            BaseController.log_info("Registered certificate " + registrable_cert.certificate_details.hash + " for address '" + str(ss_address) + "'")
        except ApiException as err:
            BaseController.log_api_error('TokenCertificatesApi->import_certificate', err)

    @staticmethod
    def remote_activate_certificate(ss_configuration, security_server):
        activatable_cert = CertController.find_actionable_auth_certificate(ss_configuration, security_server, 'ACTIVATE')
        if not activatable_cert:
            return

        token_cert_api = TokenCertificatesApi(ApiClient(ss_configuration))
        token_cert_api.activate_certificate(activatable_cert.certificate_details.hash) # responseless PUT
        cert_actions = token_cert_api.get_possible_actions_for_certificate(activatable_cert.certificate_details.hash)
        if 'ACTIVATE' not in cert_actions:
            BaseController.log_info("Activated certificate " + activatable_cert.certificate_details.hash)
        else:
            BaseController.log_info("Could not activate certificate " + activatable_cert.certificate_details.hash)

    def remote_download_csrs(self, ss_configuration, security_server):
        key_labels = {
            'auth': BaseController.default_auth_key_label(security_server),
            'sign': BaseController.default_sign_key_label(security_server)
        }

        token = remote_get_token(ss_configuration, security_server)
        auth_keys = list(filter(lambda key: key.label == key_labels['auth'], token.keys))
        sign_keys = list(filter(lambda key: key.label == key_labels['sign'], token.keys))

        if not (auth_keys or sign_keys):
            return

        keys_api = KeysApi(ApiClient(ss_configuration))
        downloaded_csrs = []

        for keytype in [(sign_keys, 'sign'), (auth_keys, 'auth')]:
            for key in keytype[0]:
                for csr in key.certificate_signing_requests:
                    from cement.utils import fs
                    with fs.Tmp(
                        prefix=csr_file_prefix(keytype[1], csr, security_server),
                        suffix='.der',
                        cleanup=False
                    ) as tmp:
                        # Impossible to get valid byte array via generated client API conversion, resort to HTTP response.
                        http_response = keys_api.download_csr(key.id, csr.id, csr_format=CsrFormat.DER, _preload_content=False)
                        if 200 == http_response.status:
                            with open(tmp.file, 'wb') as f:
                                f.write(http_response.data)
                                downloaded_csrs.append(DownloadedCsr(csr.id, key.id, keytype[1].upper(), f.name))
                        else:
                            BaseController.log_info(
                                "Failed to download key '" + key.id + "' CSR '" + csr.id + "' (HTTP " + http_response.status + ", " + http_response.reason + ")"
                            )
                        # Remove empty folder that fs.Tmp creates and that would remain with auto-clean off
                        os.rmdir(tmp.dir)

        render_data = []
        if self.is_output_tabulated():
            render_data = [DownloadedCsrListMapper.headers()]
            render_data.extend(map(DownloadedCsrListMapper.as_list, downloaded_csrs))
        else:
            render_data.extend(map(DownloadedCsrListMapper.as_object, downloaded_csrs))

        self.render(render_data)
        return downloaded_csrs

    @staticmethod
    def find_actionable_auth_certificate(ss_configuration, security_server, cert_action):
        token = remote_get_token(ss_configuration, security_server)
        # Find the authentication certificate by conventional name
        auth_key_label = BaseController.default_auth_key_label(security_server)
        auth_keys = list(filter(lambda key: key.label == auth_key_label, token.keys))
        found_auth_key_count = len(auth_keys)
        if found_auth_key_count == 0:
            BaseController.log_info("Did not found authentication key labelled '" + auth_key_label + "'.")
            return None
        if found_auth_key_count > 1:
            BaseController.log_info("Found multiple authentication keys labelled '" + auth_key_label + "', skipping registration.")
            return None

        # So far so good, are there actual certificates attached to key?
        auth_key = auth_keys[0]
        if not auth_key.certificates:
            BaseController.log_info("No certificates available for authentication key labelled '" + auth_key_label + "'.")
            return None

        # Find actionable certs
        actionable_certs = list(filter(lambda c: cert_action in c.possible_actions, auth_key.certificates))
        if len(actionable_certs) == 0:
            BaseController.log_info("No certificates to '" + cert_action + "' for key labelled '" + auth_key_label + "'.")
            return None
        if len(actionable_certs) > 1:
            BaseController.log_info("Multiple certificates to '" + cert_action + "' for key labelled '" + auth_key_label + "'.")
            return None

        return actionable_certs[0]


def remote_get_token(ss_configuration, security_server):
    token_id = security_server['software_token_id']
    token_api = TokensApi(ApiClient(ss_configuration))
    token = token_api.get_token(token_id)
    return token


def csr_file_prefix(type, key, security_server):
    return security_server['name'] + '-' + type +  "-CSR-" + key.id + "-"
