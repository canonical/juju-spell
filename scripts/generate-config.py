#!/usr/bin/env python3

import os
import subprocess
import sys

import click
import yaml

CONTROLLERS_FILE = "/home/{}/.local/share/juju/controllers.yaml"
ACCOUNTS_FILE = "/home/{}/.local/share/juju/accounts.yaml"
CONFIG_FILE = "~/.local/share/juju-spell/config.yaml"
CONFIG_PERSONAL_FILE = "~/.local/share/juju-spell/config-personal.yaml"


def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, str_presenter)
yaml.representer.SafeRepresenter.add_representer(str, str_presenter)


def get_yaml_content(user, host, file):
    cmd = ["ssh", host, "sudo", "cat", file.format(user)]
    try:
        controller_config = subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        return

    return yaml.safe_load(controller_config)


def get_controllers(user, host):
    return get_yaml_content(user, host, CONTROLLERS_FILE)


def get_accounts(user, host):
    return get_yaml_content(user, host, ACCOUNTS_FILE)


def get_config(user, host, owner):
    controllers = get_controllers(user, host)

    if not controllers:
        return []

    accounts = get_accounts(user, host)
    configs = []
    for controller in controllers["controllers"]:
        config = {
            "name": host + "_" + controller,
            "customer": host,
            "owner": owner,
            "tags": ["automatic"],
        }
        api_endpoints = controllers["controllers"][controller]["api-endpoints"]
        if len(api_endpoints) > 0:
            config["endpoint"] = api_endpoints[0]
        else:
            config["endpoint"] = ""

        config["uuid"] = controllers["controllers"][controller]["uuid"]
        config["ca_cert"] = controllers["controllers"][controller]["ca-cert"]
        config["model_mapping"] = {"lma": [], "default": []}
        config["connection"] = {"destination": host, "port_range": "17071:17170"}
        config["user"] = accounts["controllers"][controller]["user"]
        if "password" in accounts["controllers"][controller]:
            config["password"] = accounts["controllers"][controller]["password"]
        else:
            config["password"] = ""
        configs.append(config)

    return configs


def get_all_configs(user, hosts, owner):
    config = {"controllers": []}

    for host in hosts:
        config["controllers"] += get_config(user, host, owner)

    return config


def get_yaml_configs(user, hosts, owner):
    return yaml.dump(get_all_configs(user, hosts, owner))


@click.option("-o", "--owner", type=str, required=True, help="Owner of the cloud")
@click.option(
    "-u",
    "--user",
    type=str,
    required=True,
    help="User that bootstrapped the remote juju controller",
)
@click.option("-f", "--file", type=str, required=True, help="Path to the hosts file")
@click.command()
def main(owner, user, file):
    if not os.path.isfile(file):
        print(f"Host file {file} doesn't exist")
        sys.exit(1)

    hosts = list(map(str.strip, open(file, "r").readlines()))
    print(get_yaml_configs(user, hosts, owner))


if __name__ == "__main__":
    main()
