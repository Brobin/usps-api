========
USPS API
========

|python| |license|

-------------------

This is a simple Python wrapper for the USPS API. Instead of having to deal with XML, use this library and receive nicely formatted JSON back while tracking shipments, creating shipments, and validating addresses.

------------
Installation
------------

To install usps-api, use pip::

    pip install usps-api

Or to install from source::

    python setup.py install

-------------
Configuration
-------------

Note: In order to use any of these APIs, you need to register with USPS and get a `USERID` https://www.usps.com/business/web-tools-apis/welcome.htm. For the create_shipment endpoint, you will also need to request further permissions by emailing uspstechnicalsupport@mailps.custhelp.com about Label API access.

-----
Usage
-----


Track Shipments
---------------

.. code-block:: python

    from usps import USPSApi

    usps = USPSApi('XXXXXXXXXXXX')
    track = usps.track('00000000000000000000')
    print(track.result)


Create Shipment
---------------

The `create_shipment` function needs a to and crom address, weight (in ounces), service type and label type. Service types and lable types can be found in `usps/constants.py`. Defaults are `SERVICE_PRIORITY` and `LABEL_ZPL`.

.. code-block:: python

    from usps import USPSApi, Address
    from usps import SERVICE_PRIORITY, LABEL_ZPL

    to_address = Address(
        name='Tobin Brown',
        address_1='1234 Test Ave.',
        city='Test',
        state='NE',
        zipcode='55555'
    )

    from_address = Address(
        name='Tobin Brown',
        address_1='1234 Test Ave.',
        city='Test',
        state='NE',
        zipcode='55555'
    )
    weight = 12  # weight in ounces

    usps = USPSApi('XXXXXXXXXXXX', test=True)
    label = usps.create_label(to_address, from_address, weight, SERVICE_PRIORITY, LABEL_ZPL)
    print(label.result)

Validate Address
----------------

.. code-block:: python

    from usps import USPSApi, Address

    address = Address(
        name='Tobin Brown',
        address_1='1234 Test Ave.',
        city='Test',
        state='NE',
        zipcode='55555'
    )
    usps = USPSApi('XXXXXXXXXXXX', test=True)
    validation = usps.validate_address(address)
    print(validation.result)

-------  
License
-------

MIT. See `LICENSE`_ for more details.


.. _LICENSE: https://github.com/Brobin/usps-api/blob/master/LICENSE

.. |license| image:: https://img.shields.io/github/license/Brobin/django-seed.svg?style=flat-square
    :target: https://github.com/Brobin/django-seed/blob/master/LICENSE
    :alt: MIT License

.. |python| image:: https://img.shields.io/pypi/pyversions/usps-api.svg?style=flat-square
    :target: https://pypi.python.org/pypi/usps-api
    :alt: Python 3.4, 3.5, 3.6
