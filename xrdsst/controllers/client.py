import urllib3

from cement import ex

from xrdsst.api import ClientsApi
from xrdsst.api_client.api_client import ApiClient
from xrdsst.controllers.base import BaseController
from xrdsst.models import ClientAdd, Client, ConnectionType, ServiceDescriptionAdd, ClientStatus
from xrdsst.rest.rest import ApiException
from xrdsst.resources.texts import texts


class ClientController(BaseController):
    class Meta:
        label = 'client'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = texts['client.controller.description']

    @ex(label='add-client-subsystem', help="Add client subsystem", arguments=[])
    def add(self):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.add_client(self.load_config())

    @ex(label='add-service-description', help="Add client service description", arguments=[])
    def add_description(self):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.add_client(self.load_config())

    @ex(help="Register client", arguments=[])
    def register(self):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.register_client(self.load_config())

    def add_client(self, configuration):
        self.init_logging(configuration)
        for security_server in configuration["security_server"]:
            BaseController.log_info('Starting client add process for security server: ' + security_server['name'])
            ss_configuration = self.initialize_basic_config_values(security_server, configuration)
            for client in security_server["clients"]:
                self.remote_add_client(ss_configuration, client)

    def add_service_description(self, configuration):
        self.init_logging(configuration)
        for security_server in configuration["security_server"]:
            BaseController.log_info('Starting service description add process for security server: ' + security_server['name'])
            ss_configuration = self.initialize_basic_config_values(security_server, configuration)
            for client in security_server["clients"]:
                for service_description in client["service_descriptions"]:
                    self.remote_add_service_description(ss_configuration, client, service_description)

    def register_client(self, configuration):
        self.init_logging(configuration)
        for security_server in configuration["security_server"]:
            BaseController.log_info('Starting client registrations for security server: ' + security_server['name'])
            ss_configuration = self.initialize_basic_config_values(security_server, configuration)
            for client in security_server["clients"]:
                self.remote_register_client(ss_configuration, security_server, client)

    @staticmethod
    def remote_add_client(ss_configuration, client_conf):
        conn_type = BaseController.convert_swagger_enum(ConnectionType, client_conf['connection_type'])
        client = Client(member_class=client_conf['member_class'],
                        member_code=client_conf['member_code'],
                        subsystem_code=client_conf['subsystem_code'],
                        connection_type=conn_type)

        client_add = ClientAdd(client=client, ignore_warnings=True)
        clients_api = ClientsApi(ApiClient(ss_configuration))
        try:
            response = clients_api.add_client(body=client_add)
            BaseController.log_info("Added client subsystem " + partial_client_id(client_conf) + " (got full id " + response.id + ")")
        except ApiException as err:
            if err.status == 409:
                BaseController.log_info("Client for '" + partial_client_id(client_conf) + "' already exists.")
            else:
                BaseController.log_api_error('ClientsApi->add_client', err)

    @staticmethod
    def remote_add_service_description(ss_configuration, client_conf, service_description_conf):
        description_add = ServiceDescriptionAdd(url=service_description_conf['url'],
                                                rest_service_code=service_description_conf['rest_service_code'],
                                                ignore_warnings=True)
        clients_api = ClientsApi(ApiClient(ss_configuration))
        try:
            clients = clients_api.find_clients(member_class=client_conf['member_class'],
                                               member_code=client_conf['member_code'],
                                               subsystem_code=client_conf['subsystem_code'])
            response = clients_api.add_client_service_description(clients[0].id, body=description_add)
            BaseController.log_info("Added client subsystem " + partial_client_id(client_conf) + " service description" + " (got full id " + response.id + ")")
        except ApiException as err:
            if err.status == 409:
                BaseController.log_info("Service description for '" + partial_client_id(client_conf) + "' already exists.")
            else:
                BaseController.log_api_error('ClientsApi->add_client_service_description', err)

    def remote_register_client(ss_configuration, security_server_conf, client_conf):
        clients_api = ClientsApi(ApiClient(ss_configuration))
        try:
            found_clients = clients_api.find_clients(
                member_class=client_conf['member_class'],
                member_code=client_conf['member_code'],
                subsystem_code=client_conf['subsystem_code']
            )

            if not found_clients:
                BaseController.log_info(
                    security_server_conf['name'] + ": Client matching " + partial_client_id(client_conf) + " not found")
                return

            if len(found_clients) > 1:
                BaseController.log_info(
                    security_server_conf['name'] + ": Error, multiple matching clients found for " + partial_client_id(client_conf)
                )
                return

            client = found_clients[0]
            if ClientStatus.SAVED != client.status:
                BaseController.log_info(
                    security_server_conf['name'] + ": " + partial_client_id(client_conf) + " already registered."
                )
                return

            try:
                clients_api.register_client(id=client.id)
                BaseController.log_info("Registered client " + partial_client_id(client_conf))
            except ApiException as reg_err:
                BaseController.log_api_error('ClientsApi->register_client', reg_err)
        except ApiException as find_err:
            BaseController.log_api_error('ClientsApi->find_clients', find_err)

def partial_client_id(client_conf):
    return str(client_conf['member_class']) + ":" + \
           str(client_conf['member_code']) + ":" + \
           str(client_conf['subsystem_code'])
