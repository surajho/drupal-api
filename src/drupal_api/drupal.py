"""Necessary classes and modules"""
import pprint
import copy
import json
import collections
import urllib
import sys
from bson import json_util
import requests
import urllib3
from fake_useragent import UserAgent


class Drupal:
    def __init__(
        self,
        domain: str,
        environment: str,
        username: str,
        password: str
    ):
        self.domain = domain
        self.request_verification = None

        if environment == "prod":
            self.request_verification = True
        elif environment == "dev":
            self.request_verification = False
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        else:
            raise SystemExit(f"There is no Drupal environment chosen")

        self.json_api_username = username
        self.json_api_password = password
        self.default_headers = {
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        }

    def get_entities(
        self,
        url: str,
        **kwargs
    ):
        """
        Get entities from a given URL.

        This method makes an HTTP GET request to the given URL using the
        `requests` library to retrieve entities. The request is authenticated
        using the credentials provided during object instantiation. The
        response is checked for any HTTP errors, and if any are encountered,
        the error message is printed along with the response JSON, and the
        program is exited with a status code of 0.

        Parameters
        ----------
        url : str
            The URL from which entities need to be retrieved.
        **kwargs : dict, optional
            Optional keyword arguments that can be passed to the
            `requests.get()` method, such as query parameters and headers.

        Returns
        -------
        requests.Response
            The response object returned by the `requests.get()` method, which
            contains the entities retrieved from the given URL.

        Notes
        -----
        - This method relies on the availability and consistency of the given
          URL, and the authentication credentials provided during object
          instantiation.

        - The `headers`, `params`, `verify`, and `auth` arguments of the
          `requests.get()` method are used to configure the HTTP request made
          by this method.

        - The `response` object returned by the `requests.get()` method is
          checked for HTTP errors using the `raise_for_status()` method. If any
          HTTP errors are encountered, the error message is printed along with
          the response JSON, and the program is exited with a status code of 0.

        - This method is responsible for making an authenticated HTTP GET
          request to the given URL and retrieving the entities from it.
        """

        current_url = ''

        if url.find(self.domain) == -1:
            current_url = self.domain + url
        else:
            current_url = url

        response = requests.get(
            current_url,
            headers=self.default_headers,
            params=kwargs.get("parameters", {}),
            verify=self.request_verification,
            auth=(self.json_api_username, self.json_api_password)
        )

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            print(error)
            pprint.pprint(response.json())
            sys.exit(0)

        return response

    def get_drupal_entity_collection(
        self,
        url: str,
        **kwargs
    ):
        """
        Retrieves a collection of entities from Drupal using the specified URL
        and query parameters. This method fetches entities in paginated batches
        and accumulates them in a list until all entities are retrieved. The
        retrieved entities are returned as a list.

        Parameters
        ----------
            url : str
                The URL endpoint to retrieve the entities from. This should be
                the endpoint specific to the entity type being retrieved,
                e.g., '/jsonapi/node' for nodes or '/jsonapi/taxonomy_term' for
                taxonomy terms.
            **kwargs :
                Additional keyword arguments to be included as query parameters
                in the API request. These parameters can be used to filter or
                paginate the results, and should be provided as keyword
                arguments, where the keyword represents the parameter name and
                the value represents the parameter value.

        Returns
        -------
            list:
                A list of entities retrieved from Drupal.

        Notes
        -----
            - This method makes use of the 'get_entities' method, which is
              assumed to be implemented elsewhere in the codebase. Please
              ensure  that the 'get_entities' method is properly implemented
              and available for use with this method.
            - The retrieved entities are accumulated in a list, and the
              pagination is handled internally until all entities are
              retrieved. This may result in multiple requests to the Drupal
              API, depending on the number of entities and the page size
              configured on the Drupal server.
            - The 'url' argument should be provided as a string, and should be
              specific to the entity type being retrieved, including the API
              endpoint and any additional path or query parameters.
            - Additional query parameters can be provided as keyword arguments,
              where the keyword represents the parameter name and the value
              represents the parameter value. These parameters can be used to
              filter or paginate the results as needed.
        """

        entities_list = []

        next_page = True
        counter = 0
        current_url = self.domain + url

        while next_page:
            entity_page = self.get_entities(
                current_url,
                parameters=kwargs.get("query", {})
            ).json()

            if len(entity_page["data"]) == 0:
                return {}

            entities_list.extend(entity_page["data"])

            counter += len(entity_page["data"])
            print(
                f"Retrieved {counter} nodes of "
                f"content type {url.split('/')[-1]}",
                end="\r"
            )

            if "next" in entity_page["links"]:
                current_url = entity_page["links"]["next"]["href"]
            else:
                next_page = False

        print()

        return entities_list

    def post_entity(
        self,
        entity_url: str,
        data_package: dict,
        file=False,
        filename=""
    ):
        this_header = copy.deepcopy(self.default_headers)
        data = {}

        if file:
            this_header["Content-Disposition"] = "file; filename=\"" + \
                filename + "\""
            this_header["Content-Type"] = "application/octet-stream"
            data = data_package
        else:
            data = json.dumps(data_package, default=json_util.default)

        response = requests.post(
            self.domain + entity_url,
            headers=this_header,
            data=data,
            verify=self.request_verification,
            auth=(self.json_api_username, self.json_api_password)
        )

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            print(error)
            pprint.pprint(response.json())
            sys.exit(0)

        return response

    def update_entity(
        self,
        entity_url: str,
        data_package: dict
    ):
        response = requests.patch(
            self.domain + entity_url,
            headers=self.default_headers,
            data=json.dumps(data_package, default=json_util.default),
            verify=self.request_verification,
            auth=(self.json_api_username, self.json_api_password)
        )

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            print(error)
            pprint.pprint(response.json())
            sys.exit(0)

        return response

    def delete_entity(
        self,
        entity_url
    ):
        response = requests.delete(
            self.domain + entity_url,
            headers=self.default_headers,
            verify=self.request_verification,
            auth=(self.json_api_username, self.json_api_password)
        )

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            print(error)
            pprint.pprint(response.json())
            sys.exit(0)

        return response

    def get_taxonomy_term(
        self,
        postUrl: str,
        data: dict,
        extraData: dict = {}
    ):
        params = {
            ("filter[a-label][condition][path]", "name"),
            ("filter[a-label][condition][operator]", "="),
            ("filter[a-label][condition][value]",
             data["data"]["attributes"]["name"]),
        }

        taxonomy_term_response = self.get_entities(postUrl, parameters=params)

        if len(json.loads(taxonomy_term_response.text)["data"]) == 0:
            data_to_send = {}

            if len(extraData) != 0:
                data_to_send = self.merge_dicts(data, extraData)
            else:
                data_to_send = data

            created_taxonomy_term_response = self.post_entity(
                postUrl, data_to_send)

            return json.loads(created_taxonomy_term_response.text)["data"]

        return json.loads(taxonomy_term_response.text)["data"][0]

    def merge_dicts(
        self,
        dict1: dict,
        dict2: dict
    ):
        """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
        updating only top-level keys, dict2 recurses down into dicts nested
        to an arbitrary depth, updating keys. The ``dict2`` is merged into
        ``dict1``.
        :param dict1: dict onto which the merge is executed
        :param dict2: dct merged into dct
        :return: None
        """
        for k, v in dict2.items():
            if (k in dict1 and isinstance(dict1[k], dict)
                    and isinstance(dict2[k], collections.Mapping)):
                self.merge_dicts(dict1[k], dict2[k])
            else:
                dict1[k] = dict2[k]

        return dict1

    def get_file_id(
        self,
        drupal_field_url: str,
        **kwargs
    ):
        """
        Retrieves the UUID of a file from the Drupal website or uploads the file
        if it does not exist yet.

        Parameters
        ----------
            drupal_field_url : str
                the string object representing the url of the field to which
                the file will be uploaded. This has the example format:
                '/jsonapi/[node]/[content type]/[field name]'
            file_url_or_path : str
                the string object representing the URL or the local path of the
                file
            filename : str
                the string object representing the filename
            local_file : bool
                the boolean object that determines whether the file is
                uploaded locally from the computer or downloaded through
                a URL
        """

        filename = kwargs.get("filename", None)
        file_url_or_path = kwargs.get("file_url_or_path", None)

        if filename is None:
            splitted_url = file_url_or_path.split("/")

            if splitted_url[len(splitted_url) - 1] == "":
                filename = splitted_url[len(splitted_url) - 2]
            else:
                filename = splitted_url[len(splitted_url) - 1]

        params = {
            ("filter[a-label][condition][path]", "filename"),
            ("filter[a-label][condition][operator]", "="),
            ("filter[a-label][condition][value]", filename),
        }

        file_response = self.get_entities(
            self.domain + "/jsonapi/file/file", parameters=params)

        uuid = None

        if len(file_response.json()["data"]) == 0:
            file_bytes = kwargs.get("file_bytes", None)

            if file_bytes is None:
                local_file = kwargs.get("local_file", False)

                file_bytes = self.__get_file_bytes(
                    local_file,
                    file_url_or_path
                )

            uploaded_file_response = self.post_entity(
                drupal_field_url,
                file_bytes,
                True,
                filename
            )

            uuid = uploaded_file_response.json()["data"]["id"]
        else:
            uuid = file_response.json()["data"][0]["id"]

        return uuid

    @classmethod
    def __get_file_bytes(
        cls,
        local_file: bool,
        file_url_or_path: str
    ):
        file_bytes = None

        if local_file:
            with open(file_url_or_path, "rb") as file_to_read:
                loaded_file = file_to_read.read()
                file_byte_array = bytearray(loaded_file)
                file_bytes = bytes(file_byte_array)
        else:
            try:
                user_agent = UserAgent()
                headers = {"User-Agent": user_agent.random}

                custom_request = urllib.request.Request(
                    file_url_or_path,
                    headers=headers
                )

                file_bytes = urllib.request.urlopen(custom_request).read()
            except urllib.error.HTTPError as error:
                print(error)
                sys.exit(0)
            except urllib.error.URLError as error:
                print(error)
                sys.exit(0)

        return file_bytes
