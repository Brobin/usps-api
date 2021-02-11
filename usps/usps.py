import json
import requests
import xmltodict

from lxml import etree

from .address import Zip
from .constants import LABEL_ZPL, SERVICE_PRIORITY, MAX_LOOKUPS_IN_REQUEST


class USPSApiError(Exception):
    pass


class USPSApi(object):
    BASE_URL = 'https://secure.shippingapis.com/ShippingAPI.dll?API='
    urls = {
        'tracking': 'TrackV2{test}&XML={xml}',
        'label': 'eVS{test}&XML={xml}',
        'validate': 'Verify&XML={xml}',
        'citystatelookup': 'CityStateLookup&XML={xml}'
    }

    def __init__(self, api_user_id, test=False):
        self.api_user_id = api_user_id
        self.test = test

    def get_url(self, action, xml):
        return self.BASE_URL + self.urls[action].format(
            **{'test': 'Certify' if self.test else '', 'xml': xml}
        )

    def send_request(self, action, xml, return_type=('dict', 'json', 'ordered_dict')[0]):
        # The USPS developer guide says "ISO-8859-1 encoding is the expected character set for the request."
        # (see https://www.usps.com/business/web-tools-apis/general-api-developer-guide.htm)
        xml = etree.tostring(xml, encoding='iso-8859-1', pretty_print=self.test).decode()
        url = self.get_url(action, xml)
        response_xml = requests.get(url).content
        response_ordered_dict = xmltodict.parse(response_xml)
        if 'Error' in response_ordered_dict:
            raise USPSApiError(response_ordered_dict['Error']['Description'])
        # NB: seems the json library is being used solely to turn the OrderedDicts into dicts...
        if return_type == 'ordered_dict':
            return response_ordered_dict
        response_json = json.dumps(response_ordered_dict)
        if return_type == 'json':
            return response_json
        response_dict = json.loads(response_json)
        if return_type != 'dict':
            raise ValueError('unknown return_type: {}'.format(return_type))

        return response_dict

    def validate_address(self, *args, **kwargs):
        return AddressValidate(self, *args, **kwargs)

    def lookup_citystate(self, *args, **kwargs):
        return CityStateLookup(self, *args, **kwargs)

    def track(self, *args, **kwargs):
        return TrackingInfo(self, *args, **kwargs)

    def create_label(self, *args, **kwargs):
        return ShippingLabel(self, *args, **kwargs)


class AddressValidate(object):

    def __init__(self, usps, address):
        xml = etree.Element('AddressValidateRequest', {'USERID': usps.api_user_id})
        _address = etree.SubElement(xml, 'Address', {'ID': '0'})
        address.add_to_xml(_address, prefix='', validate=True)

        self.result = usps.send_request('validate', xml)


class CityStateLookup(object):

    def __init__(self, usps, zips, return_type=('dict', 'json', 'pandas', 'ordered_dict')[0]):
        """
        Accepts either a single Zip or a sequence of them, up to the API maximum of 5.
        """
        xml = etree.Element('CityStateLookupRequest', {'USERID': usps.api_user_id})

        if isinstance(zips, Zip):
            zips = [zips]

        if len(zips) > MAX_LOOKUPS_IN_REQUEST:
            raise ValueError('each request limited to {:d} ZIPs ({:d} provided)'.format(MAX_LOOKUPS_IN_REQUEST,
                                                                                        len(zips)))

        for ii, zz in enumerate(zips):
            _zip = etree.SubElement(xml, 'ZipCode', {'ID': '{:d}'.format(ii)})
            zz.add_to_xml(_zip, prefix='', validate=False)

        _res = usps.send_request('citystatelookup', xml, 'ordered_dict' if return_type == 'pandas' else return_type)
        if return_type == 'pandas':
            import pandas as pd  # probably not great practice, but means we dont import unless needed
            if len(zips) > 1:
                self.result = pd.read_json(json.dumps(_res['CityStateLookupResponse']['ZipCode']),
                                       dtype=False)  # disable dtype inference to preserve ZIP codes
            else:
                # if there's only a single return, the JSON doesnt include an array so we have to load
                # it into a series and then turn it back into a DataFrame
                self.result = pd.DataFrame(pd.read_json(json.dumps(
                    _res['CityStateLookupResponse']['ZipCode']),
                    typ='series',
                    dtype=False  # disable dtype inference to preserve ZIP codes
                )).T

        else:
            self.result = _res


class TrackingInfo(object):

    def __init__(self, usps, tracking_number, **kwargs):
        xml = etree.Element('TrackFieldRequest', {'USERID': usps.api_user_id})
        if 'source_id' in kwargs:
            self.source_id = kwargs['source_id']
            self.client_ip = kwargs['client_ip'] if 'client_ip' in kwargs else '127.0.0.1'

            etree.SubElement(xml, "Revision").text = "1"
            etree.SubElement(xml, "ClientIp").text = self.client_ip
            etree.SubElement(xml, "SourceId").text = self.source_id

        child = etree.SubElement(xml, 'TrackID', {'ID': tracking_number})

        self.result = usps.send_request('tracking', xml)


class ShippingLabel(object):

    def __init__(self, usps, to_address, from_address, weight,
                 service=SERVICE_PRIORITY, label_type=LABEL_ZPL):
        root = 'eVSRequest' if not usps.test else 'eVSCertifyRequest'
        xml = etree.Element(root, {'USERID': usps.api_user_id})

        label_params = etree.SubElement(xml, 'ImageParameters')
        label = etree.SubElement(label_params, 'ImageParameter')
        label.text = label_type

        from_address.add_to_xml(xml, prefix='From', validate=False)
        to_address.add_to_xml(xml, prefix='To', validate=False)

        package_weight = etree.SubElement(xml, 'WeightInOunces')
        package_weight.text = str(weight)

        delivery_service = etree.SubElement(xml, 'ServiceType')
        delivery_service.text = service

        etree.SubElement(xml, 'Width')
        etree.SubElement(xml, 'Length')
        etree.SubElement(xml, 'Height')
        etree.SubElement(xml, 'Machinable')
        etree.SubElement(xml, 'ProcessingCategory')
        etree.SubElement(xml, 'PriceOptions')
        etree.SubElement(xml, 'InsuredAmount')
        etree.SubElement(xml, 'AddressServiceRequested')
        etree.SubElement(xml, 'ExpressMailOptions')
        etree.SubElement(xml, 'ShipDate')
        etree.SubElement(xml, 'CustomerRefNo')
        etree.SubElement(xml, 'ExtraServices')
        etree.SubElement(xml, 'HoldForPickup')
        etree.SubElement(xml, 'OpenDistribute')
        etree.SubElement(xml, 'PermitNumber')
        etree.SubElement(xml, 'PermitZIPCode')
        etree.SubElement(xml, 'PermitHolderName')
        etree.SubElement(xml, 'CRID')
        etree.SubElement(xml, 'MID')
        etree.SubElement(xml, 'LogisticsManagerMID')
        etree.SubElement(xml, 'VendorCode')
        etree.SubElement(xml, 'VendorProductVersionNumber')
        etree.SubElement(xml, 'SenderName')
        etree.SubElement(xml, 'SenderEMail')
        etree.SubElement(xml, 'RecipientName')
        etree.SubElement(xml, 'RecipientEMail')
        etree.SubElement(xml, 'ReceiptOption')
        image = etree.SubElement(xml, 'ImageType')
        image.text = 'PDF'

        self.result = usps.send_request('label', xml)


class TimeCalc(object):
    """
        Extends USPS application to include a Time to deliver class
        Time to deliver calculates estimated delivery time between two zip codes.

        Can be extended to switch between Standard and Priority, but Standard is hard-coded right now
    """

    def __init__(self, usps, origin, destination):
        # StandardBRequest
        xml = etree.Element('StandardBRequest', {'USERID': usps.api_user_id})
        # xml = etree.Element('PriorityMailRequest', {'USERID': usps.api_user_id})
        _origin = etree.SubElement(xml, 'OriginZip')
        _origin.text = str(origin)

        _destination = etree.SubElement(xml, 'DestinationZip')
        _destination.text = str(destination)

        print(etree.tostring(xml, pretty_print=True))

        self.result = usps.send_request('calc', xml)
