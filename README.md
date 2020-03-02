
# CEPH PG UPGRADE

This script is used to slowly increase pgs in Ceph clusters without manual intervention, since the autoscale of PG was introduced from Nautilus.
By default it will increase pg and pgp one by one and the impact on the users is minimal (tested with serveral ceph clusters)

**Currentyl doesn't work on Nautilus**

### Prerequisites

This script is written and tested for **Python3.x**
On the node you execute this script you need to install the package **python3-rados**

On debian system run
```
sudo apt update && sudo apt install python3-rados
```

On rhel and centos run:
```
yum install python3-rados
```

### Usage


Typical usage of the script is to pass argument for ceph.conf keyring pool and target pg

```
python3 upgrade_pg.py --ceph-conf /path/to/ceph.conf --ceph-keyring /path/to/keyring --pool rbd --target-pg 0000
```

if you want just to check without touching anything just add **--check**

Since the script might run for several days I suggest to use the script with a terminal like **tmux**

#### Options ####

**--ceph-conf**: path to your ceph.conf (eg. /etc/ceph/ceph.conf)  <br/>
**--ceph-keyring**: path to the admin keyring (eg. /etc/ceph/ceph.client.admin.keyring ) <br/>
**--target-pg**: the final number of pgs that you want to reach in your pool <br/>
**--pool**: the pool that you want increment pgs <br/>
**--increment-step**: increase more than 1pg at time (**Warning: this can badly impact the performance of your ceph cluster**) <br/>
**--check**: just show the current number of pg and the target specified with --target-pg, useful for checking before actually run it <br/>



## Contributing

Anyone is free to contributing, any suggestion for improvment is much welcome



## Authors

* **Giordano Corradini** - *Initial work*


## License

This project is licensed under the Apache License 2.0 - see the [LICENSE.md](LICENSE.md) file for details

