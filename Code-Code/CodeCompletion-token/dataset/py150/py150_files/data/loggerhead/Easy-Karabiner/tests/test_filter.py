# -*- coding: utf-8 -*-
from easy_karabiner import util
from easy_karabiner.filter import *


def test_basic_filter():
    f1 = Filter('GOOGLE_CHROME')
    s = ''' <only> GOOGLE_CHROME </only>'''
    util.assert_xml_equal(f1, s)

    f2 = ReplacementFilter('{{EMACS_IGNORE_APP}}', type='not')
    s = ''' <not> {{EMACS_IGNORE_APP}} </not>'''
    util.assert_xml_equal(f2, s)

    try:
        f1 + f2
        assert(False)
    except:
        pass

def test_device_filter():
    f = DeviceFilter('DeviceVendor::APPLE_COMPUTER', 'DeviceProduct::ANY')
    s = '''
        <device_only>
          DeviceVendor::APPLE_COMPUTER,
          DeviceProduct::ANY
        </device_only>'''
    util.assert_xml_equal(f, s)

    f = DeviceFilter('DeviceVendor::APPLE_COMPUTER', 'DeviceProduct::ANY',
                     'DeviceVendor::Apple_Bluetooth', 'DeviceProduct::ANY',
                     type='not')
    s = '''
        <device_not>
          DeviceVendor::APPLE_COMPUTER, DeviceProduct::ANY,
          DeviceVendor::Apple_Bluetooth, DeviceProduct::ANY
        </device_not>'''
    util.assert_xml_equal(f, s)

def test_windowname_filter():
    f = WindowNameFilter('Gmail')
    s = ''' <windowname_only> Gmail </windowname_only> '''
    util.assert_xml_equal(f, s)

def test_uielementrole_filter():
    f = UIElementRoleFilter('AXTextField', 'AXTextArea')
    s = ''' <uielementrole_only> AXTextField, AXTextArea </uielementrole_only> '''
    util.assert_xml_equal(f, s)

def test_inputsource_filter():
    f = InputSourceFilter('UKRAINIAN')
    s = ''' <inputsource_only> UKRAINIAN </inputsource_only> '''
    util.assert_xml_equal(f, s)

    f = InputSourceFilter('SWISS_FRENCH', 'SWISS_GERMAN', type='not')
    s = ''' <inputsource_not> SWISS_FRENCH, SWISS_GERMAN </inputsource_not> '''
    util.assert_xml_equal(f, s)


def test_parse_filter():
    f = parse_filter(['LOGITECH', 'LOGITECH_USB_RECEIVER'])
    s = '''
        <device_only>
          DeviceVendor::LOGITECH,
          DeviceProduct::LOGITECH_USB_RECEIVER
        </device_only>'''
    util.assert_xml_equal(f[0], s)

    f = parse_filter(['!{{EMACS_MODE_IGNORE_APPS}}', '!FINDER', '!SKIM'])
    s = '''
        <not>
          {{EMACS_MODE_IGNORE_APPS}}, FINDER, SKIM
        </not>'''
    util.assert_xml_equal(f[0], s)