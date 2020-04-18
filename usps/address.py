from lxml import etree


class Address(object):

    def __init__(self, name, address_1, city, state, zipcode='',
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

    def add_to_xml(self, root, prefix='To', validate=False):
        if not validate:
            name = etree.SubElement(root, prefix + 'Name')
            name.text = self.name

        company = etree.SubElement(root, prefix + 'Firm' + ('Name' if validate else ''))
        company.text = self.company
    
        address_1 = etree.SubElement(root, prefix + 'Address1')
        address_1.text = self.address_1

        address_2 = etree.SubElement(root, prefix + 'Address2')
        address_2.text = self.address_2 or '-'
    
        city = etree.SubElement(root, prefix + 'City')
        city.text = self.city

        state = etree.SubElement(root, prefix + 'State')
        state.text = self.state

        if self.zipcode:
            zipcode = etree.SubElement(root, prefix + 'Zip5')
            zipcode.text = self.zipcode

        if self.zipcode_ext:
            zipcode_ext = etree.SubElement(root, prefix + 'Zip4')
            zipcode_ext.text = self.zipcode_ext

        if not validate:
            phone = etree.SubElement(root, prefix + 'Phone')
            phone.text = self.phone
