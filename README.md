<h1 align="center">
  <br/>
  Esctl
  <br/>
</h1>

<h4 align="center">A Command-Line Interface designed to ease Elasticsearch administration.</h4>

<p align="center">
  <a href="https://github.com/jeromepin/esctl/actions?query=workflow%3A%22Lint+and+test%22+branch%3Amaster">
    <img src="https://github.com/jeromepin/esctl/workflows/Lint%20and%20test/badge.svg" alt="Test status">
  </a>
  <a href="https://github.com/jeromepin/esctl/actions?query=workflow%3A%22Publish+%F0%9F%93%A6%22+branch%3Amaster">
    <img src="https://github.com/jeromepin/esctl/workflows/Publish%20%F0%9F%93%A6/badge.svg" alt="Publish status">
  </a>

  <a href="https://www.codefactor.io/repository/github/jeromepin/esctl">
      <img src="https://www.codefactor.io/repository/github/jeromepin/esctl/badge" alt="Codefactor grade">
  </a>

  <a href="https://sonarcloud.io/dashboard?id=jeromepin_esctl">
    <img src="https://sonarcloud.io/api/project_badges/measure?project=jeromepin_esctl&metric=alert_status" alt="Code quality status">
  </a>
</p>

<p align="center">
  <a href="#key-features">Key Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#how-to-use">How To Use</a> •
  <a href="#examples">Examples</a> •
  <a href="#license">License</a>
  <a href="#developing">Developing</a>
</p>

<hr/>

Esctl is a CLI tool for Elasticsearch. [I designed it](https://jeromepin.fr/posts/esctl-managing-elasticsearch-from-command-line/) to shorten huge `curl` commands Elasticsearch operators were running like :

```bash
curl -XPUT --user "john:doe" 'http://elasticsearch.example.com:9200/_cluster/settings' -d '{
    "transient" : {
        "cluster.routing.allocation.enable": "NONE"
    }
}'
```

The equivalent with `esctl` is

```bash
esctl cluster routing allocation enable none
```

## Key Features

* Cluster-level informations : **stats**, **info**, **health**, **allocation explanation**
* Node-level informations : **list**, **hot threads**, **exclusion**
* Cluster-level and index-level **settings**
* `_cat` API for **allocation**, **plugins** and **thread pools**
* **Index management** : open, close, create, delete, list
* Per-module **log configuration**
* X-Pack APIs : **users** and **roles**


## Installation

### Using PIP

```bash
pip3 install esctl
```

### From source

```bash
pip install git+https://github.com/jeromepin/esctl.git
```


## How To Use

Esctl relies on a `~/.esctlrc` file containing its config. This file is automatically created on the first start if it doesn't exists :

```yaml
clusters:
  bar:
    servers:
      - https://bar.example.com

users:
  john-doe:
    username: john
    password: doe

contexts:
  foo:
    user: john-doe
    cluster: bar

default-context: foo
```

## Examples

<p align="center">
  <img src="node-list-sample.png" alt="node-list sample">
</p>


## License

`esctl` is licensed under the GNU GPLv3. See [LICENCE](https://github.com/jeromepin/esctl/blob/master/LICENSE) file.

## Developing

### Install

```bash
make install
```

### Run tests

```bash
make test
```

### Format code

```bash
make fmt
```
