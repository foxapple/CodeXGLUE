# -*- coding: utf-8 -*-
from easy_karabiner import __version__
from easy_karabiner import util
from easy_karabiner import alias
from easy_karabiner import exception
from easy_karabiner.generator import *


def test_generator():
    KEYMAP_ALIAS = {
        'flip': 'FlipScrollWheel',
    }
    DEFINITIONS = {
        'BILIBILI': 'com.typcn.Bilibili',
        'DeviceVendor::CHERRY': '0x046a',
        'DeviceProduct::3494' : '0x0011',
    }
    REMAPS = [
        ['cmd', 'alt'],
        ['alt', 'cmd', ('CHERRY', 'BILIBILI', '3494')],
        ['(flip)', 'flipscrollwheel_vertical', ['!APPLE_COMPUTER', '!ANY']],
    ]
    alias.update_alias('KEYMAP_ALIAS', KEYMAP_ALIAS)
    g = Generator(remaps=REMAPS, definitions=DEFINITIONS)
    s = '''
        <root>
          <Easy-Karabiner>{version}</Easy-Karabiner>
          <item>
            <name>Easy-Karabiner</name>
            <appdef>
              <appname>BILIBILI</appname>
              <equal>com.typcn.Bilibili</equal>
            </appdef>
            <deviceproductdef>
              <productname>3494</productname>
              <productid>0x0011</productid>
            </deviceproductdef>
            <devicevendordef>
              <vendorname>CHERRY</vendorname>
              <vendorid>0x046a</vendorid>
            </devicevendordef>
            <item>
              <name>Enable</name>
              <identifier>private.easy_karabiner</identifier>
              <block>
                <autogen> __KeyToKey__ KeyCode::COMMAND_L, KeyCode::OPTION_L</autogen>
              </block>
              <block>
                <device_only> DeviceVendor::CHERRY, DeviceProduct::3494 </device_only>
                <only>BILIBILI</only>
                <autogen> __KeyToKey__ KeyCode::OPTION_L, KeyCode::COMMAND_L </autogen>
              </block>
              <block>
                <device_not> DeviceVendor::APPLE_COMPUTER, DeviceProduct::ANY </device_not>
                <autogen> __FlipScrollWheel__ Option::FLIPSCROLLWHEEL_VERTICAL </autogen>
              </block>
            </item>
          </item>
        </root>
        '''.format(version=__version__)
    util.assert_xml_equal(g, s)
    # test for reentrant of `XML_base` methods
    assert(str(g) == str(g))

    DEFINITIONS = {
        'KeyCode::VK_OPEN_URL_FINDER': '/Applications/Finder.app',
        'Open::Calculator': '/Applications/Calculator.app',
    }
    REMAPS = [
        ['alt', 'cmd', ['fn']],
        ['ctrl alt F', 'Open::FINDER', ['!fn']],
        ['cmd', 'alt', ['fn']],
        ['ctrl shift C', 'Open::Calculator', ['!fn']],
    ]
    g = Generator(remaps=REMAPS, definitions=DEFINITIONS)
    s = '''
        <root>
          <Easy-Karabiner>{version}</Easy-Karabiner>
          <item>
            <name>Easy-Karabiner</name>
            <vkopenurldef>
              <name>KeyCode::VK_OPEN_URL_FINDER</name>
              <url type="file">/Applications/Finder.app</url>
            </vkopenurldef>
            <vkopenurldef>
              <name>KeyCode::VK_OPEN_URL_Calculator</name>
              <url type="file">/Applications/Calculator.app</url>
            </vkopenurldef>
            <item>
              <name>Enable</name>
              <identifier>private.easy_karabiner</identifier>
              <block>
                <modifier_only>ModifierFlag::fn</modifier_only>
                <autogen> __KeyToKey__ KeyCode::OPTION_L, KeyCode::COMMAND_L </autogen>
                <autogen> __KeyToKey__ KeyCode::COMMAND_L, KeyCode::OPTION_L </autogen>
              </block>
              <block>
                <modifier_not>ModifierFlag::fn</modifier_not>
                <autogen> __KeyToKey__
                  KeyCode::F, ModifierFlag::CONTROL_L, ModifierFlag::OPTION_L, ModifierFlag::NONE,
                  KeyCode::VK_OPEN_URL_FINDER
                </autogen>
                <autogen> __KeyToKey__
                  KeyCode::C, ModifierFlag::CONTROL_L, ModifierFlag::SHIFT_L, ModifierFlag::NONE,
                  KeyCode::VK_OPEN_URL_Calculator
                </autogen>
              </block>
            </item>
          </item>
        </root>
        '''.format(version=__version__)
    util.assert_xml_equal(g, s)

def test_exception():
    def assert_raise_exception(remaps=(), definitions=()):
        try:
            g = Generator(remaps=remaps, definitions=definitions)
            assert(str(g) and False)
        except exception.ConfigError:
            pass

    DEFINITIONS = { 'Invalid::Definition': 'Will Raise Exception', }
    assert_raise_exception(definitions=DEFINITIONS)

    REMAPS = ['Remap must be list or tuple']
    assert_raise_exception(remaps=REMAPS)

    REMAPS = [['Undefined', ['Filter']]]
    assert_raise_exception(remaps=REMAPS)