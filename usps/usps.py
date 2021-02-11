import json
import requests
import xmltodict

from lxml import etree

from .constants import LABEL_ZPL, SERVICE_PRIORITY


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

    def send_request(self, action, xml):
        # The USPS developer guide says "ISO-8859-1 encoding is the expected character set for the request."
        # (see https://www.usps.com/business/web-tools-apis/general-api-developer-guide.htm)
        xml = etree.tostring(xml, encoding='iso-8859-1', pretty_print=self.test).decode()
        url = self.get_url(action, xml)
        xml_response = requests.get(url).content
        response = json.loads(json.dumps(xmltodict.parse(xml_response)))
        if 'Error' in response:
            raise USPSApiError(response['Error']['Description'])
        return response

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

    def __init__(self, usps, zip):
        xml = etree.Element('CityStateLookupRequest', {'USERID': usps.api_user_id})
        _zip = etree.SubElement(xml, 'ZipCode', {'ID': '0'})
        zip.add_to_xml(_zip, prefix='', validate=False)

        self.result = usps.send_request('citystatelookup', xml)


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
