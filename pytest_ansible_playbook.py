# -*- coding: utf-8 -*-
"""
Implementation of pytest-ansible-playbook plugin.
"""


from __future__ import print_function
import os
import subprocess

import pytest


def pytest_addoption(parser):
    """
    Define py.test command line options for this plugin.
    """
    group = parser.getgroup('ansible-playbook')
    group.addoption(
        '--ansible-playbook-directory',
        action='store',
        dest='ansible_playbook_directory',
        metavar="PLAYBOOK_DIR",
        help='Directory where ansible playbooks are stored.',
        )
    group.addoption(
        '--ansible-playbook-inventory',
        action='store',
        dest='ansible_playbook_inventory',
        metavar="INVENTORY_FILE",
        help='Ansible inventory file.',
        )


def pytest_configure(config):
    """
    Validate pylatest-ansible-playbook options: when such option is used,
    the given file or directory should exist.

    This check makes the pytest fail immediatelly when wrong path is
    specified, without waiting for the first test case with ansible_playbook
    fixture to fail.
    """
    dir_path = config.getvalue('ansible_playbook_directory')
    if dir_path is not None and not os.path.isdir(dir_path):
        msg = (
            "value of --ansible-playbook-directory option ({0}) "
            "is not a directory").format(dir_path)
        raise pytest.UsageError(msg)
    inventory_path = config.getvalue('ansible_playbook_inventory')
    if inventory_path is None:
        return
    if not os.path.isabs(inventory_path) and dir_path is not None:
        inventory_path = os.path.join(dir_path, inventory_path)
    if not os.path.isfile(inventory_path):
        msg = (
            "value of --ansible-playbook-inventory option ({}) "
            "is not accessible").format(inventory_path)
        raise pytest.UsageError(msg)


@pytest.fixture
def ansible_playbook(request):
    """
    Pytest fixture which runs given ansible playbook. When ansible returns
    nonzero return code, the test case which uses this fixture is not
    executed and ends in ``ERROR`` state.
    """
    setup_marker = request.node.get_marker('ansible_playbook_setup')
    if setup_marker is None:
        msg = (
            "ansible playbook not specified for the test case, "
            "please add a decorator like this one "
            "``@pytest.mark.ansible_playbook_setup('playbook.yml')`` "
            "for ansible_playbook fixture to know which playbook to use")
        raise Exception(msg)
    if len(setup_marker.args) == 0:
        msg = (
            "no playbook is specified in "
            "``@pytest.mark.ansible_playbook_setup`` "
            "decorator of this test case, please add at least one playbook "
            "file name as a parameter into the marker, eg. "
            "``@pytest.mark.ansible_playbook_setup('playbook.yml')``")
        raise Exception(msg)
    for playbook_file in setup_marker.args:
        ansible_command = [
            "ansible-playbook",
            "-vv",
            "-i", request.config.option.ansible_playbook_inventory,
            playbook_file,
            ]
        subprocess.check_call(
            ansible_command,
            cwd=request.config.option.ansible_playbook_directory)
