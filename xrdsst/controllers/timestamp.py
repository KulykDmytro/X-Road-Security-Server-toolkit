import logging
import urllib3
from cement import ex

from .base import BaseController
from xrdsst.api_client.api_client import ApiClient
from xrdsst.resources.texts import texts
from ..api import TimestampingServicesApi
from xrdsst.api.system_api import SystemApi
from ..models import TimestampingService
from ..rest.rest import ApiException


class TimestampServiceListMapper:
    @staticmethod
    def headers():
        return ['NAME', 'URL']

    @staticmethod
    def as_list(timestamping_service):
        return [timestamping_service.name, timestamping_service.url]

    @staticmethod
    def as_object(timestamping_service):
        return {
            'name' : timestamping_service.name,
            'url': timestamping_service.url
        }


class TimestampController(BaseController):
    class Meta:
        label = 'timestamp'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = texts['timestamp.controller.description']

    # Possible listing approaches for later:
    #   merged, with approval/configuration flags
    #   separate, separate subcommands
    #   merged, with separate command line filtering (--approved, ... etc)

    # Protobonus: approved timestamp services list
    @ex(label='list-approved', help='List approved timestamping services.', arguments=[])
    def list_approved(self):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.timestamp_service_list_approved(self.load_config())

    # Protobonus: configured timestamp services list
    @ex(label='list-configured', help='List configured timestamping services', arguments=[])
    def list_configured(self):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.timestamp_service_list(self.load_config())

    @ex(help='Select and activate single approved timestamping service.', arguments=[])
    def init(self):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.timestamp_service_init(self.load_config())

    # Since this is read-only operation, do not log anything, only console output
    def timestamp_service_list(self, configuration):
        for security_server in configuration["security-server"]:
            ss_config = self.initialize_basic_config_values(security_server)
            self.remote_timestamp_service_list(ss_config, security_server)

    def timestamp_service_list_approved(self, configuration):
        for security_server in configuration["security-server"]:
            ss_config = self.initialize_basic_config_values(security_server)
            self.remote_timestamp_service_list_approved(ss_config, security_server)

    def render_timestamping_services(self, ts_list):
        render_data = []
        if self.is_output_tabulated():
            render_data = [TimestampServiceListMapper.headers()]
            render_data.extend(map(TimestampServiceListMapper.as_list, ts_list))
        else:
            render_data.extend(map(TimestampServiceListMapper.as_object, ts_list))
        self.render(render_data)

    # Helper for timestamping services listing via TimestampingServices & System APIs.
    def remote_ts_list(self, apicall):
        try:
            ts_list_response = apicall()
            self.render_timestamping_services(ts_list_response)
        except ApiException as e:
            print("Exception when listing timestamping services: %s\n", e)

    def get_approved_timestamping_services(self, ss_configuration):
        timestamping_api = TimestampingServicesApi(ApiClient(ss_configuration))
        return timestamping_api.get_approved_timestamping_services()

    def remote_timestamp_service_list_approved(self, ss_configuration, security_server):
        self.remote_ts_list(lambda: self.get_approved_timestamping_services(ss_configuration))

    def remote_timestamp_service_list(self, ss_configuration, security_server):
        system_api = SystemApi(ApiClient(ss_configuration))
        self.remote_ts_list(lambda: system_api.get_configured_timestamping_services())

    def timestamp_service_init(self, configuration): # logging required
        self.init_logging(configuration)
        for security_server in configuration["security-server"]:
            ss_config = self.initialize_basic_config_values(security_server)
            self.remote_timestamp_service_init(ss_config, security_server)

    def remote_timestamp_service_init(self, ss_configuration, security_server):
        try:
            approved_ts = self.get_approved_timestamping_services(ss_configuration)
            if approved_ts:
                system_api = SystemApi(ApiClient(ss_configuration))
                ts_init_response = system_api.add_configured_timestamping_service(
                    body=TimestampingService(name=approved_ts[0].name, url=approved_ts[0].url)
                )
                if ts_init_response: # single timestamping service added is also returned
                    print(security_server['name'])
                    self.render_timestamping_services([ts_init_response])
        except ApiException as excn:
            if 409 == excn.status:
                print(security_server['name'], "Timestamping service already configured.")
            else:
                tsiferr_msg = "Timestamping service initialization configuration failure"
                print(security_server['name'], tsiferr_msg, excn)
                logging.error(security_server['name'] + ' '  + tsiferr_msg, excn)
