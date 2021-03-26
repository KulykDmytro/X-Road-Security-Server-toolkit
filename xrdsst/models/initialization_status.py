# coding: utf-8

"""
    X-Road Security Server Admin API

    X-Road Security Server Admin API. Note that the error metadata responses described in some endpoints are subjects to change and may be updated in upcoming versions.  # noqa: E501

    OpenAPI spec version: 1.0.31
    Contact: info@niis.org
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""

import pprint
import re  # noqa: F401

import six

class InitializationStatus(object):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    swagger_types = {
        'is_anchor_imported': 'bool',
        'is_server_code_initialized': 'bool',
        'is_server_owner_initialized': 'bool',
        'software_token_init_status': 'TokenInitStatus'
    }

    attribute_map = {
        'is_anchor_imported': 'is_anchor_imported',
        'is_server_code_initialized': 'is_server_code_initialized',
        'is_server_owner_initialized': 'is_server_owner_initialized',
        'software_token_init_status': 'software_token_init_status'
    }

    def __init__(self, is_anchor_imported=None, is_server_code_initialized=None, is_server_owner_initialized=None, software_token_init_status=None):  # noqa: E501
        """InitializationStatus - a model defined in Swagger"""  # noqa: E501
        self._is_anchor_imported = None
        self._is_server_code_initialized = None
        self._is_server_owner_initialized = None
        self._software_token_init_status = None
        self.discriminator = None
        self.is_anchor_imported = is_anchor_imported
        self.is_server_code_initialized = is_server_code_initialized
        self.is_server_owner_initialized = is_server_owner_initialized
        self.software_token_init_status = software_token_init_status

    @property
    def is_anchor_imported(self):
        """Gets the is_anchor_imported of this InitializationStatus.  # noqa: E501

        whether a configuration anchor has been imported or not  # noqa: E501

        :return: The is_anchor_imported of this InitializationStatus.  # noqa: E501
        :rtype: bool
        """
        return self._is_anchor_imported

    @is_anchor_imported.setter
    def is_anchor_imported(self, is_anchor_imported):
        """Sets the is_anchor_imported of this InitializationStatus.

        whether a configuration anchor has been imported or not  # noqa: E501

        :param is_anchor_imported: The is_anchor_imported of this InitializationStatus.  # noqa: E501
        :type: bool
        """
        if is_anchor_imported is None:
            raise ValueError("Invalid value for `is_anchor_imported`, must not be `None`")  # noqa: E501

        self._is_anchor_imported = is_anchor_imported

    @property
    def is_server_code_initialized(self):
        """Gets the is_server_code_initialized of this InitializationStatus.  # noqa: E501

        whether the server code of the security server has been initialized or not  # noqa: E501

        :return: The is_server_code_initialized of this InitializationStatus.  # noqa: E501
        :rtype: bool
        """
        return self._is_server_code_initialized

    @is_server_code_initialized.setter
    def is_server_code_initialized(self, is_server_code_initialized):
        """Sets the is_server_code_initialized of this InitializationStatus.

        whether the server code of the security server has been initialized or not  # noqa: E501

        :param is_server_code_initialized: The is_server_code_initialized of this InitializationStatus.  # noqa: E501
        :type: bool
        """
        if is_server_code_initialized is None:
            raise ValueError("Invalid value for `is_server_code_initialized`, must not be `None`")  # noqa: E501

        self._is_server_code_initialized = is_server_code_initialized

    @property
    def is_server_owner_initialized(self):
        """Gets the is_server_owner_initialized of this InitializationStatus.  # noqa: E501

        whether the server owner of the security server has been initialized or not  # noqa: E501

        :return: The is_server_owner_initialized of this InitializationStatus.  # noqa: E501
        :rtype: bool
        """
        return self._is_server_owner_initialized

    @is_server_owner_initialized.setter
    def is_server_owner_initialized(self, is_server_owner_initialized):
        """Sets the is_server_owner_initialized of this InitializationStatus.

        whether the server owner of the security server has been initialized or not  # noqa: E501

        :param is_server_owner_initialized: The is_server_owner_initialized of this InitializationStatus.  # noqa: E501
        :type: bool
        """
        if is_server_owner_initialized is None:
            raise ValueError("Invalid value for `is_server_owner_initialized`, must not be `None`")  # noqa: E501

        self._is_server_owner_initialized = is_server_owner_initialized

    @property
    def software_token_init_status(self):
        """Gets the software_token_init_status of this InitializationStatus.  # noqa: E501


        :return: The software_token_init_status of this InitializationStatus.  # noqa: E501
        :rtype: TokenInitStatus
        """
        return self._software_token_init_status

    @software_token_init_status.setter
    def software_token_init_status(self, software_token_init_status):
        """Sets the software_token_init_status of this InitializationStatus.


        :param software_token_init_status: The software_token_init_status of this InitializationStatus.  # noqa: E501
        :type: TokenInitStatus
        """
        if software_token_init_status is None:
            raise ValueError("Invalid value for `software_token_init_status`, must not be `None`")  # noqa: E501

        self._software_token_init_status = software_token_init_status

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value
        if issubclass(InitializationStatus, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, InitializationStatus):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
