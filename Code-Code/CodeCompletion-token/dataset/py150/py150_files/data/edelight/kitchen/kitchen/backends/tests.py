"""Tests for the kitchen.backends app"""
import simplejson as json
from django.test import TestCase
from mock import patch

from kitchen.backends import lchef as chef
from kitchen.backends import plugins
from kitchen.backends.plugins import loader

chef.build_node_data_bag()
TOTAL_NODES = 10


class TestRepo(TestCase):

    def test_good_repo(self):
        """Should return true when a valid repository is found"""
        self.assertTrue(chef._check_kitchen())

    @patch('kitchen.backends.lchef.KITCHEN_DIR', '/badrepopath/')
    def test_bad_repo(self):
        """Should raise RepoError when the kitchen is not found"""
        self.assertRaises(chef.RepoError, chef._check_kitchen)

    @patch('kitchen.backends.lchef.KITCHEN_DIR', '../kitchen/')
    def test_invalid_kitchen(self):
        """Should raise RepoError when the kitchen is incomplete"""
        self.assertRaises(chef.RepoError, chef._check_kitchen)

    def test_missing_node_data_bag(self):
        """Should raise RepoError when there is no node data bag"""
        nodes = chef._load_data("nodes")
        with patch('kitchen.backends.lchef.DATA_BAG_PATH', 'badpath'):
            self.assertRaises(chef.RepoError, chef._load_extended_node_data,
                              nodes)

    def test_missing_node_data_json_error(self):
        """Should raise RepoError when there is a JSON error"""
        nodes = chef._load_data("nodes")  # Load before mocking
        with patch.object(json, 'loads') as mock_method:
            mock_method.side_effect = json.decoder.JSONDecodeError(
                "JSON syntax error", "", 10)
            self.assertRaises(chef.RepoError, chef._load_extended_node_data,
                              nodes)

    def test_incomplete_node_data_bag(self):
        """Should raise RepoError when a node is missing its data bag item"""
        nodes = chef._load_data("nodes")
        nodes.append({'name': 'extra_node'})
        self.assertRaises(chef.RepoError, chef._load_extended_node_data, nodes)


class TestData(TestCase):

    def test_data_loader(self):
        """Should return nodes when the given argument is 'nodes'"""
        data = chef._data_loader('nodes')
        self.assertEqual(len(data), TOTAL_NODES)
        self.assertTrue(data[1]['name'].startswith('testnode'))

    def test_data_loader_json_error(self):
        """Should raise RepoError when LittleChef raises SystemExit"""
        with patch('kitchen.backends.lchef.lib.get_nodes') as mock_method:
            mock_method.side_effect = SystemExit()
            self.assertRaises(chef.RepoError, chef._data_loader, 'nodes')

    def test_load_data_nodes(self):
        """Should return nodes when the given argument is 'nodes'"""
        data = chef._load_data('nodes')
        self.assertEqual(len(data), TOTAL_NODES)
        self.assertTrue(data[1]['name'].startswith('testnode'))

    def test_load_data_roles(self):
        """Should return roles when the given argument is 'roles'"""
        data = chef._load_data('roles')
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0]['name'], "dbserver")

    def test_load_data_unsupported(self):
        """Should return None when an invalid arg is given"""
        self.assertEqual(chef._load_data('rolezzzz'), None)

    def test_get_nodes(self):
        """Should return all nodes when calling get_nodes()"""
        data = chef.get_nodes()
        self.assertEqual(len(data), TOTAL_NODES)
        self.assertTrue(data[1]['name'].startswith('testnode'))

    def test_get_environments(self):
        """Should return a list of all chef_environment values found"""
        data = chef.get_environments(chef.get_nodes_extended())
        self.assertEqual(len(data), 3)
        expected = [{'counts': 1, 'name': 'none'},
                    {'counts': 8, 'name': 'production'},
                    {'counts': 1, 'name': 'staging'}]
        self.assertEqual(data, expected)

    def test_filter_nodes_all(self):
        """Should return all nodes when empty filters are are given"""
        data = chef.filter_nodes(chef.get_nodes_extended())
        self.assertEqual(len(data), TOTAL_NODES)

    def test_filter_nodes_env(self):
        """Should filter nodes belonging to a given environment"""
        data = chef.filter_nodes(chef.get_nodes_extended(), 'production')
        self.assertEqual(len(data), 8)

        data = chef.filter_nodes(chef.get_nodes_extended(), 'staging')
        self.assertEqual(len(data), 1)

        data = chef.filter_nodes(chef.get_nodes_extended(), 'non_existing_env')
        self.assertEqual(len(data), 0)

    def test_filter_nodes_roles(self):
        """Should filter nodes acording to their virt value"""
        data = chef.filter_nodes(chef.get_nodes_extended(),
                                 roles=['dbserver'])
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['name'], "testnode3.mydomain.com")

        data = chef.filter_nodes(chef.get_nodes_extended(),
                                 roles=['loadbalancer'])
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], "testnode1")

        data = chef.filter_nodes(chef.get_nodes_extended(),
                                 roles=['webserver'])
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0]['name'], "testnode2")

        data = chef.filter_nodes(chef.get_nodes_extended(),
                                 roles=['webserver', 'dbserver'])
        self.assertEqual(len(data), 6)
        self.assertEqual(data[1]['name'], "testnode3.mydomain.com")

    def test_filter_nodes_virt(self):
        """Should filter nodes acording to their virt value"""
        total_guests = 7
        total_hosts = 3
        data = chef.filter_nodes(chef.get_nodes_extended(), virt_roles='guest')
        self.assertEqual(len(data), total_guests)

        data = chef.filter_nodes(chef.get_nodes_extended(), virt_roles='host')
        self.assertEqual(len(data), total_hosts)

        data = chef.filter_nodes(chef.get_nodes_extended(),
                                 virt_roles='host,guest')
        self.assertEqual(len(data), TOTAL_NODES)

    def test_filter_nodes_combined(self):
        """Should filter nodes acording to their virt value"""
        data = chef.filter_nodes(chef.get_nodes_extended(),
                                 env='production',
                                 roles=['loadbalancer', 'webserver'],
                                 virt_roles='guest')
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['name'], "testnode1")
        self.assertEqual(data[1]['name'], "testnode2")
        self.assertEqual(data[2]['name'], "testnode7")

        data = chef.filter_nodes(chef.get_nodes_extended(), env='staging',
                                 roles=['webserver'], virt_roles='guest')
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], "testnode4")

    def test_group_by_hosts(self):
        """Should group all guests by hosts when called without arguments"""
        data = chef.group_nodes_by_host(chef.get_nodes_extended())
        self.assertEqual(len(data), 3)
        for host in data:
            self.assertEqual(host['virtualization']['role'], 'host')
        self.assertEqual(data[2]['name'], "testnode9")
        vms = data[2]['virtualization']['guests']
        expected_vms = ['testnode1', 'testnode2', 'testnode4']
        self.assertEqual(len(vms), len(expected_vms))
        for vm in vms:
            fqdn = vm['fqdn']
            self.assertTrue(fqdn in expected_vms)
            expected_vms.remove(fqdn)

    def test_group_by_hosts_with_env(self):
        """Should group guests in env by hosts when env is given"""
        data = chef.group_nodes_by_host(chef.get_nodes_extended(),
                                        env='staging')
        self.assertEqual(len(data), 1)
        for host in data:
            self.assertEqual(host['virtualization']['role'], 'host')
        expected_vms = ['testnode4']
        self.assertEqual(len(data[0]['virtualization']['guests']), 3)

    def test_group_by_hosts_with_role(self):
        """Should group guests by hosts when giving a role filter"""
        data = chef.group_nodes_by_host(chef.get_nodes_extended(),
                                        roles=['loadbalancer'])
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'testnode9')
        self.assertEqual(len(data[0]['virtualization']['guests']), 3)


class TestPlugins(TestCase):

    def test_import_plugin_not_found(self):
        """Should not load plugin when module doesn't exist"""
        self.assertEqual(len(loader.import_plugins(['bad_name'])), 0)

    def test_import_plugin(self):
        """Should load plugin when module exists"""
        self.assertEqual(len(loader.import_plugins(['monitoring'])), 1)

    def test_inject_plugin_data(self):
        """Should add link data when plugin is applied"""
        chef.plugins = plugins.import_plugins(['monitoring'])
        node = {
            'fqdn': 'testnode',
            'kitchen': {'data': {'links': [{"foo": "bar"}], 'other': {}}}
        }
        chef.inject_plugin_data([node])
        self.assertTrue('other' in node['kitchen']['data'])
        self.assertEqual(len(node['kitchen']['data']['links']), 2)

    def test_plugin_view(self):
        """Should load plugin when module exists"""
        plugins = loader.import_plugins(['monitoring'])
        self.assertEqual(len(plugins), 1)
        inject = getattr(plugins['monitoring'], 'inject')
        self.assertFalse(getattr(inject, '__is_view__', False))
        links = getattr(plugins['monitoring'], 'links')
        self.assertTrue(getattr(links, '__is_view__'))
