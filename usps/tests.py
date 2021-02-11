import mock

from lxml import etree

from unittest import TestCase

from .address import Address
from .usps import USPSApi, USPSApiError, TimeCalc


class USPSApiTestCase(TestCase):

    def setUp(self):
        self.usps = USPSApi('XXXXXXXXXXXX', test=True)

    def test_get_url(self):
        self.assertEqual(
            self.usps.get_url('tracking', 'test'),
            'https://secure.shippingapis.com/ShippingAPI.dll?API=TrackV2Certify&XML=test'
        )
        self.assertEqual(
            self.usps.get_url('label', 'test'),
            'https://secure.shippingapis.com/ShippingAPI.dll?API=eVSCertify&XML=test'
        )
        self.assertEqual(
            self.usps.get_url('validate', 'test'),
            'https://secure.shippingapis.com/ShippingAPI.dll?API=Verify&XML=test'
        )
        usps = USPSApi('XXXXXXXXXXXX', test=False)
        self.assertEqual(
            usps.get_url('tracking', 'test'),
            'https://secure.shippingapis.com/ShippingAPI.dll?API=TrackV2&XML=test'
        )
        self.assertEqual(
            usps.get_url('label', 'test'),
            'https://secure.shippingapis.com/ShippingAPI.dll?API=eVS&XML=test'
        )
        self.assertEqual(
            usps.get_url('validate', 'test'),
            'https://secure.shippingapis.com/ShippingAPI.dll?API=Verify&XML=test'
        )
    
    @mock.patch('requests.get')
    def test_send_request_error(self, requests_mock):
        requests_mock.return_value.content = b'<Error><Description>Test Error</Description></Error>'
        with self.assertRaises(USPSApiError):
            self.usps.send_request('tracking', etree.Element('asdf'))

    @mock.patch('requests.get')
    def test_send_request_valid(self, requests_mock):
        requests_mock.return_value.content = b'<Valid>test</Valid>'
        response = self.usps.send_request('tracking', etree.Element('asdf'))
        self.assertEqual(response, {'Valid': 'test'})

    @mock.patch('usps.usps.AddressValidate.__init__')
    @mock.patch('usps.usps.TrackingInfo.__init__')
    @mock.patch('usps.usps.ShippingLabel.__init__')
    def test_wrapper_methods(self, address_mock, track_mock, ship_mock):
        address_mock.return_value = None
        track_mock.return_value = None
        ship_mock.return_value = None

        self.usps.validate_address()
        self.usps.track()
        self.usps.create_label()

        address_mock.assert_called()
        track_mock.assert_called()
        ship_mock.assert_called()


class AddressTestCase(TestCase):
    
    def test_address_xml(self):
        address = Address('Test', '123 Test St.', 'Test', 'NE', '55555')
        root = etree.Element('Test')
        address.add_to_xml(root, prefix='')

        elements = [
            'Name', 'Firm', 'Address1', 'Address2', 'City', 'State',
            'Zip5', 'Zip4', 'Phone'
        ]
        for child in root:
            self.assertTrue(child.tag in elements)

            
class TimeCalcTestCase(TestCase):
    
    usps = USPSApi("XXXXXX", test=True)

    #usps.urls['calc'] = 'PriorityMail&XML={xml}'

    usps.urls['calc'] = 'StandardB&XML={xml}'


    def time_calc(self, *args, **kwargs):
	    return TimeCalc(self, *args, **kwargs)

    usps.time_calc = time_calc


    # Test function
    label = usps.time_calc('20002', '99550')
    print(label.result)
    
    
class AddressValidateTestCase(TestCase):
    pass


class TrackingInfoTestCase(TestCase):
    pass


class ShippingLabelTestCase(TestCase):
    pass

