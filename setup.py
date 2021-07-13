#!/usr/bin/env python

from setuptools import find_packages, setup

PROJECT = "esctl"
VERSION = "1.9.0"

with open("requirements.txt") as f:
    requirements = f.read().splitlines()


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name=PROJECT,
    version=VERSION,
    description="Easy to use CLI tool to manage Elasticsearch, preventing long curl commands.",
    long_description=long_description,
    long_description_content_type="text/markdown",
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
    packages=find_packages(exclude=["tests*"]),
    include_package_data=True,
    entry_points={
        "console_scripts": ["esctl = esctl.main:main"],
        "esctl": [
            "alias list = esctl.cmd.alias:AliasList",
            "cat allocation = esctl.cmd.cat:CatAllocation",
            "cat plugins = esctl.cmd.cat:CatPlugins",
            "cat shards = esctl.cmd.cat:CatShards",
            "cat thread-pool = esctl.cmd.cat:CatThreadpool",
            "cat templates = esctl.cmd.cat:CatTemplates",
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
            "document get = esctl.cmd.document:DocumentGet",
            "index close = esctl.cmd.index:IndexClose",
            "index create = esctl.cmd.index:IndexCreate",
            "index delete = esctl.cmd.index:IndexDelete",
            "index list = esctl.cmd.index:IndexList",
            "index open = esctl.cmd.index:IndexOpen",
            "index reindex = esctl.cmd.index:IndexReindex",
            "index settings get = esctl.cmd.settings:IndexSettingsGet",
            "index settings list = esctl.cmd.settings:IndexSettingsList",
            "index settings set = esctl.cmd.settings:IndexSettingsSet",
            "logging get = esctl.cmd.logging:LoggingGet",
            "logging reset = esctl.cmd.logging:LoggingReset",
            "logging set = esctl.cmd.logging:LoggingSet",
            "node exclude = esctl.cmd.node:NodeExclude",
            "node hot-threads = esctl.cmd.node:NodeHotThreads",
            "node list = esctl.cmd.node:NodeList",
            "node stats = esctl.cmd.node:NodeStats",
            "raw = esctl.cmd.raw:RawCommand",
            "repository list = esctl.cmd.repository:RepositoryList",
            "repository show = esctl.cmd.repository:RepositoryShow",
            "repository verify = esctl.cmd.repository:RepositoryVerify",
            "roles get = esctl.cmd.roles:SecurityRolesGet",
            "snapshot list = esctl.cmd.snapshot:SnapshotList",
            "task list = esctl.cmd.task:TaskList",
            "users get = esctl.cmd.users:SecurityUsersGet",
        ],
    },
    zip_safe=False,
)
