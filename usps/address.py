from lxml import etree
from urllib.parse import quote


class Address(object):
    QUOTE_SAFE_CHARS = " /"

    def __init__(self, name, address_1, city, state, zipcode,
                 zipcode_ext='', company='', address_2='', phone=''):
        self.name = name
        self.company = company
        self.address_1 = address_1
        self.address_2 = address_2
        self.city = city
        self.state = state
        self.zipcode = zipcode
        self.zipcode_ext = zipcode_ext
        self.phone = phone

    def _escape(self, string):
        return quote(string, self.QUOTE_SAFE_CHARS)

    def add_to_xml(self, root, prefix='To', validate=False):
        if not validate:
            name = etree.SubElement(root, prefix + 'Name')
            name.text = self._escape(self.name)

        company = etree.SubElement(root, prefix + 'Firm' + ('Name' if validate else ''))
        company.text = self._escape(self.company)
    
        address_1 = etree.SubElement(root, prefix + 'Address1')
        address_1.text = self._escape(self.address_1)

        address_2 = etree.SubElement(root, prefix + 'Address2')
        address_2.text = self._escape(self.address_2) or '-'
    
        city = etree.SubElement(root, prefix + 'City')
        city.text = self._escape(self.city)

        state = etree.SubElement(root, prefix + 'State')
        state.text = self._escape(self.state)

        zipcode = etree.SubElement(root, prefix + 'Zip5')
        zipcode.text = self._escape(self.zipcode)

        zipcode_ext = etree.SubElement(root, prefix + 'Zip4')
        zipcode_ext.text = self._escape(self.zipcode_ext)

        if not validate:
            phone = etree.SubElement(root, prefix + 'Phone')
            phone.text = self._escape(self.phone)
