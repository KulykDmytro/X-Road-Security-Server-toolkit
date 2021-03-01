# Return list of configuration keys that are NOT among known ConfKeys*, in hierarchical representation
def validate_conf_keys(xrdsst_conf):
    # Return only configuration keys from ConfKey list class (CONF_KEY_)
    def _keys_only(conf_key_X):
        return {getattr(conf_key_X, x) for x in vars(conf_key_X) if x.startswith('CONF_KEY')}

    # Return only used keys that are NOT among known ConfKeys
    def _invalid(used_keys, conf_key_X):
        return used_keys.difference(_keys_only(conf_key_X))

    def _validate_conf_keys(xrdsst_conf_fragment, conf_key_X):
        result = []
        if isinstance(xrdsst_conf_fragment, dict):
            fragment_keys = set(xrdsst_conf_fragment.keys())
            invalid_fragment_keys = _invalid(fragment_keys, conf_key_X)
            result.extend(map(lambda key: ('.' + key, key, _keys_only(conf_key_X)), invalid_fragment_keys))

            for desc_key in {x for x in conf_key_X.descendant_conf_keys() if xrdsst_conf_fragment.get(x[0])}:
                result.extend(map(
                    lambda key: ('.' + desc_key[0] + str(key[0]), key[1], key[2]),
                    _validate_conf_keys(xrdsst_conf_fragment[desc_key[0]], desc_key[1])
                ))
        elif isinstance(xrdsst_conf_fragment, list):
            for i in range(0, len(xrdsst_conf_fragment)):
                result.extend(map(
                    lambda key: ('[' + str(i+1) + ']' + str(key[0]), key[1], key[2]),
                    _validate_conf_keys(xrdsst_conf_fragment[i], conf_key_X)
                ))

        return result

    return _validate_conf_keys(xrdsst_conf, ConfKeysRoot)


# Known keys for xrdsst configuration file root.
class ConfKeysRoot:
    CONF_KEY_ROOT_API_KEY = 'api_key'
    CONF_KEY_ROOT_SERVER = 'security_server'
    CONF_KEY_ROOT_LOGGING = 'logging'

    # Return the tuples ('child key', child conf keys class) for keys with descendants of their own
    @staticmethod
    def descendant_conf_keys():
        return [
            (ConfKeysRoot.CONF_KEY_ROOT_API_KEY, ConfKeysApiKey),
            (ConfKeysRoot.CONF_KEY_ROOT_SERVER, ConfKeysSecurityServer),
            (ConfKeysRoot.CONF_KEY_ROOT_LOGGING, ConfKeysLogging)
        ]


# Known keys for xrdsst configuration file security server API key creation section.
class ConfKeysApiKey:
    CONF_KEY_API_KEY_CREDENTIALS = 'credentials'
    CONF_KEY_API_KEY_KEY = 'key'
    CONF_KEY_API_KEY_ROLES = 'roles'
    CONF_KEY_API_KEY_URL = 'url'

    @staticmethod
    def descendant_conf_keys():
        return []


# Known keys for xrdsst configuration file logging section.
class ConfKeysLogging:
    CONF_KEY_LOGGING_FILE = 'file'
    CONF_KEY_LOGGING_LEVEL = 'level'

    @staticmethod
    def descendant_conf_keys():
        return []


# Known keys for xrdsst configuration file security server configuration section.
class ConfKeysSecurityServer:
    CONF_KEY_ANCHOR = 'configuration_anchor'
    CONF_KEY_API_KEY = 'api_key'
    CONF_KEY_CERTS = 'certificates'
    CONF_KEY_CLIENTS = 'clients'
    CONF_KEY_DN_C = 'owner_dn_country'
    CONF_KEY_DN_ORG = 'owner_dn_org'
    CONF_KEY_NAME = 'name'
    CONF_KEY_MEMBER_CLASS = 'owner_member_class'
    CONF_KEY_MEMBER_CODE = 'owner_member_code'
    CONF_KEY_SERVER_CODE = 'security_server_code'
    CONF_KEY_SOFT_TOKEN_ID = 'software_token_id'
    CONF_KEY_SOFT_TOKEN_PIN = 'software_token_pin'
    CONF_KEY_URL = 'url'

    @staticmethod
    def descendant_conf_keys():
        return [
            (ConfKeysSecurityServer.CONF_KEY_CLIENTS, ConfKeysSecServerClients)
        ]


# Known keys for xrdsst configuration file security server client configuration section.
class ConfKeysSecServerClients:
    CONF_KEY_SS_CLIENT_MEMBER_CLASS = 'member_class'
    CONF_KEY_SS_CLIENT_MEMBER_CODE = 'member_code'
    CONF_KEY_SS_CLIENT_SUBSYSTEM_CODE = 'subsystem_code'
    CONF_KEY_SS_CLIENT_CONNECTION_TYPE = 'connection_type'
    CONF_KEY_SS_CLIENT_SERVICE_DESCS = 'service_descriptions'

    @staticmethod
    def descendant_conf_keys():
        return [
            (ConfKeysSecServerClients.CONF_KEY_SS_CLIENT_SERVICE_DESCS, ConfKeysSecServerClientServiceDesc)
        ]


# Known keys for xrdsst configuration file security server client service descriptions configuration section.
class ConfKeysSecServerClientServiceDesc:
    CONF_KEY_SS_CLIENT_SERVICE_DESC_URL = 'url'
    CONF_KEY_SS_CLIENT_SERVICE_DESC_REST_SERVICE_CODE = 'rest_service_code'
    CONF_KEY_SS_CLIENT_SERVICE_DESC_TYPE = 'type'

    @staticmethod
    def descendant_conf_keys():
        return []
