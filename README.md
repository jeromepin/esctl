# Esctl

Esctl is a CLI tool for Elasticsearch. It should prevent Elasticsearch operators to use huge `curl` commands with complex bodies like

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

```
$ esctl cluster health
+----------------------------------+-----------------+
| Attribute                        |           Value |
+----------------------------------+-----------------+
| active_primary_shards            |            2545 |
| active_shards                    |           28000 |
| active_shards_percent_as_number  |           100.0 |
| cluster_name                     |             foo |
| delayed_unassigned_shards        |               0 |
| initializing_shards              |               0 |
| number_of_data_nodes             |             200 |
| number_of_in_flight_fetch        |               0 |
| number_of_nodes                  |             215 |
| number_of_pending_tasks          |              12 |
| relocating_shards                |               0 |
| status                           |           green |
| task_max_waiting_in_queue_millis |               0 |
| timed_out                        |           False |
| unassigned_shards                |               0 |
+----------------------------------+-----------------+
```

```
$ esctl node list
+------------+--------+-------+-----+---------+---------+----------+------+--------+---------------------------+
| IP         | Heap % | RAM % | Cpu | Load 1M | Load 5M | Load 15M | Role | Master | Name                      |
+------------+--------+-------+-----+---------+---------+----------+------+--------+---------------------------+
| 10.0.0.1   | 45     | 80    | 8   | 2.05    | 1.13    | 1.10     | m    | *      | master001-foo01-prd-sfo1  |
| 10.0.0.117 | 88     | 91    | 12  | 8.03    | 9.03    | 9.00     | d    | -      | data117-foo01-prd-sfo3    |
| 10.0.0.12  | 92     | 94    | 12  | 9.00    | 9.01    | 9.00     | d    | -      | data012-foo01-prd-sfo2    |
+------------+--------+-------+-----+---------+---------+----------+------+--------+---------------------------+
```


# Installation

## From source

```bash
pip install git+https://github.com/jeromepin/esctl.git
```

# Usage

Esctl relies on a `~/.esctlrc` file containing its config :

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

# License

`esctl` is licensed under the GNU GPLv3. See [LICENCE](https://github.com/jeromepin/esctl/blob/master/LICENSE) file.

# Developing

### Run

```bash
python3 setup.py install --user --prefix= >> /dev/null && esctl
```

### Run tests

```bash
python3 setup.py install --user --prefix= >> /dev/null && pytest -s
```
