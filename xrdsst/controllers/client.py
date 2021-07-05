import cement.utils.fs
from cement import ex
from xrdsst.api import ClientsApi
from xrdsst.api_client.api_client import ApiClient
from xrdsst.controllers.base import BaseController
from xrdsst.core.conf_keys import ConfKeysSecurityServer, ConfKeysSecServerClients
from xrdsst.core.util import convert_swagger_enum, parse_argument_list
from xrdsst.models import ClientAdd, Client, ConnectionType, ClientStatus
from xrdsst.rest.rest import ApiException
from xrdsst.resources.texts import texts


class ClientController(BaseController):
    class Meta:
        label = 'client'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = texts['client.controller.description']

    CLIENTS_API_FIND_CLIENTS = 'ClientsApi->find_clients'
    CLIENTS_API_GET_CLIENT_SERVICE_DESCRIPTION = 'ClientsApi->get_client_service_description'

    @ex(help="Add client subsystem", arguments=[])
    def add(self):
        active_config = self.load_config()
        full_op_path = self.op_path()

        active_config, invalid_conf_servers = self.validate_op_config(active_config)
        self.log_skipped_op_conf_invalid(invalid_conf_servers)

        if not self.is_autoconfig():
            active_config, unconfigured_servers = self.regroup_server_ops(active_config, full_op_path)
            self.log_skipped_op_deps_unmet(full_op_path, unconfigured_servers)

        self.add_client(active_config)

    @ex(help="Register client", arguments=[])
    def register(self):
        active_config = self.load_config()
        full_op_path = self.op_path()

        active_config, invalid_conf_servers = self.validate_op_config(active_config)
        self.log_skipped_op_conf_invalid(invalid_conf_servers)

        if not self.is_autoconfig():
            active_config, unconfigured_servers = self.regroup_server_ops(active_config, full_op_path)
            self.log_skipped_op_deps_unmet(full_op_path, unconfigured_servers)

        self.register_client(active_config)

    @ex(help="Update client", arguments=[])
    def update(self):
        active_config = self.load_config()
        full_op_path = self.op_path()

        active_config, invalid_conf_servers = self.validate_op_config(active_config)
        self.log_skipped_op_conf_invalid(invalid_conf_servers)

        if not self.is_autoconfig():
            active_config, unconfigured_servers = self.regroup_server_ops(active_config, full_op_path)
            self.log_skipped_op_deps_unmet(full_op_path, unconfigured_servers)

        self.update_client(active_config)

    @ex(help="Import TLS certificates", arguments=[])
    def import_tls_certs(self):
        active_config = self.load_config()
        full_op_path = self.op_path()

        active_config, invalid_conf_servers = self.validate_op_config(active_config)
        self.log_skipped_op_conf_invalid(invalid_conf_servers)

        if not self.is_autoconfig():
            active_config, unconfigured_servers = self.regroup_server_ops(active_config, full_op_path)
            self.log_skipped_op_deps_unmet(full_op_path, unconfigured_servers)

        self.client_import_tls_cert(active_config)

    @ex(help="Unregister client(s)",
        arguments=[
            (['--ss'], {'help': 'Security server name', 'dest': 'ss'}),
            (['--client'], {'help': 'Client(s) Id', 'dest': 'clients'})
        ]
        )
    def unregister(self):
        active_config = self.load_config()

        if self.app.pargs.clients is None:
            self.log_info('Client Id is required for unregister clients')
            return
        if self.app.pargs.ss is None:
            self.log_info('Security server name is required for unregister clients')
            return

        self.unregister_client(active_config, self.app.pargs.ss, parse_argument_list(self.app.pargs.clients))

    # This operation can (at least sometimes) also be performed when global status is FAIL.
    def add_client(self, config):
        ss_api_conf_tuple = list(zip(config["security_server"], map(lambda ss: self.create_api_config(ss, config), config["security_server"])))

        for security_server in config["security_server"]:
            ss_api_config = self.create_api_config(security_server, config)
            BaseController.log_debug('Starting client add process for security server: ' + security_server['name'])
            if "clients" in security_server:  # Guards both against empty section (->None) & complete lack of section
                for client in security_server["clients"]:
                    self.remote_add_client(ss_api_config, client)

        BaseController.log_keyless_servers(ss_api_conf_tuple)

    # This operation fails when global status is not up to date.
    def register_client(self, config):
        ss_api_conf_tuple = list(zip(config["security_server"], map(lambda ss: self.create_api_config(ss, config), config["security_server"])))

        for security_server in config["security_server"]:
            ss_api_config = self.create_api_config(security_server, config)
            BaseController.log_debug('Starting client registrations for security server: ' + security_server['name'])
            if "clients" in security_server:
                for client in security_server["clients"]:
                    self.remote_register_client(ss_api_config, security_server, client)

        BaseController.log_keyless_servers(ss_api_conf_tuple)

    def update_client(self, config):
        ss_api_conf_tuple = list(zip(config["security_server"], map(lambda ss: self.create_api_config(ss, config), config["security_server"])))

        for security_server in config["security_server"]:
            ss_api_config = self.create_api_config(security_server, config)
            BaseController.log_debug('Starting client registrations for security server: ' + security_server['name'])
            if "clients" in security_server:
                for client in security_server["clients"]:
                    self.remote_update_client(ss_api_config, security_server, client)

        BaseController.log_keyless_servers(ss_api_conf_tuple)

    def client_import_tls_cert(self, config):
        ss_api_conf_tuple = list(zip(config["security_server"], map(lambda ss: self.create_api_config(ss, config), config["security_server"])))
        for security_server in config["security_server"]:
            ss_api_config = self.create_api_config(security_server, config)
            BaseController.log_debug('Starting internal TLS certificate import for security server: ' + security_server['name'])
            if ConfKeysSecurityServer.CONF_KEY_TLS_CERTS in security_server:
                client_conf = {
                    "member_name": security_server["owner_dn_org"],
                    "member_code": security_server["owner_member_code"],
                    "member_class": security_server["owner_member_class"]
                }
                self.remote_import_tls_certificate(ss_api_config, security_server[ConfKeysSecurityServer.CONF_KEY_TLS_CERTS], client_conf)

            if "clients" in security_server:
                for client_conf in security_server["clients"]:
                    if ConfKeysSecServerClients.CONF_KEY_SS_CLIENT_TLS_CERTIFICATES in client_conf:
                        self.remote_import_tls_certificate(ss_api_config, client_conf[ConfKeysSecServerClients.CONF_KEY_SS_CLIENT_TLS_CERTIFICATES],
                                                           client_conf)

        BaseController.log_keyless_servers(ss_api_conf_tuple)

    def unregister_client(self, config, security_server_name, clientsId):
        ss_api_conf_tuple = list(zip(config["security_server"],
                                     map(lambda ss: self.create_api_config(ss, config), config["security_server"])))

        security_server = list(filter(lambda ss_server: ss_server["name"] == security_server_name, config["security_server"]))
        if len(security_server) == 0:
            BaseController.log_info("Security server with name: %s not found in config file" % security_server_name)
        else:
            ss_api_config = self.create_api_config(security_server[0], config)
            BaseController.log_debug('Starting client unregistration for security server: ' + security_server[0]['name'])
            self.remote_unregister_client(ss_api_config, security_server[0], clientsId)

        BaseController.log_keyless_servers(ss_api_conf_tuple)


    def remote_add_client(self, ss_api_config, client_conf):
        conn_type = convert_swagger_enum(ConnectionType, client_conf['connection_type'])
        client = Client(member_class=client_conf['member_class'],
                        member_code=client_conf['member_code'],
                        connection_type=conn_type,
                        member_name=client_conf['member_name'],
                        subsystem_code=client_conf['subsystem_code'] if 'subsystem_code' in client_conf else None,
                        owner=False,
                        has_valid_local_sign_cert=False)

        client_add = ClientAdd(client=client, ignore_warnings=True)
        clients_api = ClientsApi(ApiClient(ss_api_config))
        try:
            response = clients_api.add_client(body=client_add)
            BaseController.log_info("Added client subsystem " + self.partial_client_id(client_conf) + " (got full id " + response.id + ")")
            return response
        except ApiException as err:
            if err.status == 409:
                BaseController.log_info("Client for '" + self.partial_client_id(client_conf) + "' already exists.")
            else:
                BaseController.log_api_error('ClientsApi->add_client', err)

    def remote_register_client(self, ss_api_config, security_server_conf, client_conf):
        clients_api = ClientsApi(ApiClient(ss_api_config))
        try:
            client = self.find_client(clients_api, client_conf)
            if client:
                if ClientStatus.SAVED != client.status:
                    BaseController.log_info(
                        security_server_conf['name'] + ": " + self.partial_client_id(client_conf) + " already registered."
                    )
                    return

                try:
                    clients_api.register_client(id=client.id)
                    BaseController.log_info("Registered client " + self.partial_client_id(client_conf))
                except ApiException as reg_err:
                    BaseController.log_api_error('ClientsApi->register_client', reg_err)
        except ApiException as find_err:
            BaseController.log_api_error(ClientController.CLIENTS_API_FIND_CLIENTS, find_err)

    def remote_update_client(self, ss_api_config, security_server_conf, client_conf):
        clients_api = ClientsApi(ApiClient(ss_api_config))
        try:
            client = self.find_client(clients_api, client_conf)
            if client:
                if client.status not in [ClientStatus.SAVED, ClientStatus.REGISTERED, ClientStatus.REGISTRATION_IN_PROGRESS]:
                    BaseController.log_info(
                        security_server_conf['name'] + ": " + self.partial_client_id(client_conf) + " not added/registered yet."
                    )
                    return

                try:
                    client.connection_type = convert_swagger_enum(ConnectionType, client_conf['connection_type'])
                    response = clients_api.update_client(client.id, body=client)
                    BaseController.log_info("Updated client " + self.partial_client_id(client_conf) + " connection type")
                    return response
                except ApiException as reg_err:
                    BaseController.log_api_error('ClientsApi->update_client', reg_err)
        except ApiException as find_err:
            BaseController.log_api_error(ClientController.CLIENTS_API_FIND_CLIENTS, find_err)

    def remote_import_tls_certificate(self, ss_api_config, tls_certs, client_conf):
        clients_api = ClientsApi(ApiClient(ss_api_config))
        try:
            client = self.find_client(clients_api, client_conf)
            if client:
                for tls_cert in tls_certs:
                    self.remote_add_client_tls_certificate(tls_cert, clients_api, client)
        except ApiException as find_err:
            BaseController.log_api_error(ClientController.CLIENTS_API_FIND_CLIENTS, find_err)

    def remote_unregister_client(self, ss_api_config, security_server, clientsId):
        clients_api = ClientsApi(ApiClient(ss_api_config))
        for clientId in clientsId:
            try:
                result = clients_api.unregister_client(clientId)
                BaseController.log_info("Unregister client: '%s' for security server: '%s'" % (clientId, security_server))
            except ApiException as err:
                if err.status == 409:
                    BaseController.log_info("Client: '%s' for security server: '%s'" % (clientId, security_server))
                else:
                    BaseController.log_api_error(ClientController.CLIENTS_API_FIND_CLIENTS, err)

    @staticmethod
    def remote_add_client_tls_certificate(tls_cert, clients_api, client):
        try:
            location = cement.utils.fs.join_exists(tls_cert)
            if not location[1]:
                BaseController.log_info("Import TLS certificate '%s' for client %s does not exist" % (location[0], client.id))
            else:
                cert_file_loc = location[0]
                cert_file = open(cert_file_loc, "rb")
                cert_data = cert_file.read()
                cert_file.close()
                response = clients_api.add_client_tls_certificate(client.id, body=cert_data)
                BaseController.log_info(
                    "Import TLS certificate '%s' for client %s" % (tls_cert, client.id))
                return response
        except ApiException as err:
            if err.status == 409:
                BaseController.log_info(
                    "TLS certificate '%s' for client %s already exists" % (tls_cert, client.id))
            else:
                BaseController.log_api_error('ClientsApi->import_tls_certificate', err)

    def find_client(self, clients_api, client_conf):
        if 'subsystem_code' in client_conf:
            found_clients = clients_api.find_clients(
                member_class=client_conf['member_class'],
                member_code=client_conf['member_code'],
                subsystem_code=client_conf["subsystem_code"]
            )
        else:
            all_clients = clients_api.find_clients(
                member_class=client_conf['member_class'],
                member_code=str(client_conf['member_code']),
                name=client_conf["member_name"]
            )
            found_clients = list(found_client for found_client in all_clients if found_client.subsystem_code is None)
        if not found_clients:
            BaseController.log_info(
                client_conf["member_name"] + ": Client matching " + self.partial_client_id(client_conf) + " not found")
            return None

        if len(found_clients) > 1:
            BaseController.log_info(
                client_conf["member_name"] + ": Error, multiple matching clients found for " + self.partial_client_id(client_conf)
            )
            return None
        return found_clients[0]

    @staticmethod
    def partial_client_id(client_conf):
        client_id = str(client_conf['member_class']) + ":" + str(client_conf['member_code'])
        if 'subsystem_code' in client_conf and client_conf['subsystem_code'] is not None:
            client_id = client_id + ":" + client_conf['subsystem_code']
        return client_id

    @staticmethod
    def get_clients_service_client_candidates(clients_api, client_id, candidates_ids):
        try:
            candidates = clients_api.find_service_client_candidates(client_id)

            if candidates_ids is None or len(candidates_ids) == 0:
                return candidates
            else:
                return [x for x in candidates if x.id in candidates_ids]

        except ApiException as find_err:
            BaseController.log_api_error('ClientsApi->find_service_client_candidates', find_err)

    @staticmethod
    def is_client_base_member(client_conf, security_server_conf):
        return client_conf["member_class"] == security_server_conf["owner_member_class"] and client_conf["member_code"] == security_server_conf[
            "owner_member_code"]

    @staticmethod
    def get_client_conf_id(client_conf):
        client_id = "%s/%s/%s" % (client_conf["member_class"], client_conf["member_code"], client_conf["member_name"])
        if ConfKeysSecServerClients.CONF_KEY_SS_CLIENT_SUBSYSTEM_CODE in client_conf:
            client_id = client_id + "/" + client_conf[ConfKeysSecServerClients.CONF_KEY_SS_CLIENT_SUBSYSTEM_CODE]

        return client_id
