#!/usr/bin/env python

from setuptools import find_packages, setup

PROJECT = "esctl"
VERSION = "1.5.0"

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name=PROJECT,
    version=VERSION,
    description="Easy to use CLI tool to manage Elasticsearch, preventing long curl commands.",
    author="Jérôme Pin",
    maintainer="Jérôme Pin",
    url="https://github.com/jeromepin/esctl",
    keywords=["elasticsearch", "es", "cli"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Utilities",
        "Topic :: System :: Shells",
    ],
    platforms=["Any"],
    scripts=[],
    provides=[],
    install_requires=requirements,
    namespace_packages=[],
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": ["esctl = esctl.main:main"],
        "esctl": [
            "cat allocation = esctl.cmd.cat:CatAllocation",
            "cat plugins = esctl.cmd.cat:CatPlugins",
            "cat thread-pool = esctl.cmd.cat:CatThreadpool",
            "cluster allocation explain = esctl.cmd.cluster:ClusterAllocationExplain",
            "cluster health = esctl.cmd.cluster:ClusterHealth",
            "cluster info = esctl.cmd.cluster:ClusterInfo",
            "cluster routing allocation enable = esctl.cmd.cluster:ClusterRoutingAllocationEnable",
            "cluster stats = esctl.cmd.cluster:ClusterStats",
            "cluster settings list = esctl.cmd.settings:ClusterSettingsList",
            "cluster settings get = esctl.cmd.settings:ClusterSettingsGet",
            "cluster settings reset = esctl.cmd.settings:ClusterSettingsReset",
            "cluster settings set = esctl.cmd.settings:ClusterSettingsSet",
            "config cluster list = esctl.cmd.config:ConfigClusterList",
            "config context list = esctl.cmd.config:ConfigContextList",
            "config context set = esctl.cmd.config:ConfigContextSet",
            "config user list = esctl.cmd.config:ConfigUserList",
            "index close = esctl.cmd.index:IndexClose",
            "index create = esctl.cmd.index:IndexCreate",
            "index delete = esctl.cmd.index:IndexDelete",
            "index list = esctl.cmd.index:IndexList",
            "index open = esctl.cmd.index:IndexOpen",
            "index settings get = esctl.cmd.settings:IndexSettingsGet",
            "index settings list = esctl.cmd.settings:IndexSettingsList",
            "index settings set = esctl.cmd.settings:IndexSettingsSet",
            "logging get = esctl.cmd.logging:LoggingGet",
            "logging reset = esctl.cmd.logging:LoggingReset",
            "logging set = esctl.cmd.logging:LoggingSet",
            "node exclude = esctl.cmd.node:NodeExclude",
            "node hot-threads = esctl.cmd.node:NodeHotThreads",
            "node list = esctl.cmd.node:NodeList",
            "roles get = esctl.cmd.roles:SecurityRolesGet",
            "users get = esctl.cmd.users:SecurityUsersGet",
        ],
    },
    zip_safe=False,
)
