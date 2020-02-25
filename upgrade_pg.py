import rados
import sys
import json
import time
import argparse
from datetime import datetime

parser = argparse.ArgumentParser(description='Argument to this python script')
parser.add_argument('--ceph-conf', type=str, required=True, help='Path to ceph.conf file')
parser.add_argument('--ceph-keyring', type=str, required=True, help='Path to the keyring to use')
parser.add_argument('--target-pg', type=int, required=True, help='The target of pg to be reached')
parser.add_argument('--increment-step', type=int, default=1, help='How many pgs to increment at once (Default 1)')
parser.add_argument('--pool', type=str, required=True, help='The pool name to increase')
parser.add_argument('--check', action='store_true', help='Dry run, doesnt perform upgrade')
args = parser.parse_args()

ceph_conf = args.ceph_conf
ceph_keyring = args.ceph_keyring
target_pg = args.target_pg
increment_step = args.increment_step
pool = args.pool
check_mode = args.check

cluster = rados.Rados(conffile=ceph_conf, conf = dict(keyring = ceph_keyring))

print("Will attempt to connect to:", str(cluster.conf_get('mon initial members')))

try:
    cluster.connect()
except Exception as error:
    print("connection error: ", error)
    raise error
finally:
    print("Connected to the cluster.")

# Generic definition for running command against ceph cluster
def run_command(cluster_handle, cmd, is_json=False):
    if is_json:
        return json.loads(cluster_handle.mon_command(json.dumps(cmd), b'', timeout=5)[1])
    return cluster_handle.mon_command(json.dumps(cmd), b'', timeout=5)


def get_pool_pg_num(pg_type):
    pool_pg_num_json = run_command(cluster, {"prefix": "osd pool get","pool": pool,"var": pg_type, "format": "json"},is_json=True)
    return pool_pg_num_json[pg_type]

def get_total_pg_num():
    total_pg_num_json = run_command(cluster, {"prefix": "status", "format": "json"},is_json=True)
    total_pg_num = total_pg_num_json["pgmap"]["num_pgs"]
    return total_pg_num

def get_cluster_clean_pg():
    pgs_clean_count = None
    cluster_status_json = run_command(cluster, {"prefix": "status", "format": "json"},is_json=True)
    for pgs in cluster_status_json["pgmap"]["pgs_by_state"]:
        if pgs["state_name"] == "active+clean":
            pgs_clean_count = pgs["count"]
    return pgs_clean_count


def increase_pg_num(pg_type, pg_count):
    run_command(cluster, {"prefix": "osd pool set","pool": pool,"var": pg_type,"val": pg_count, "format": "json"},is_json=False)

def timestamp():
    return str(datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))


print('Total PG count:', get_total_pg_num())
print('Clean Cluster pgs:', get_cluster_clean_pg())
print('pool detected pgs:', get_pool_pg_num("pg_num"))
print('pool detected pgps:', get_pool_pg_num("pgp_num"))
print('Target PG Count:', target_pg)

if check_mode:
    sys.exit('\n dry run complete')

while get_pool_pg_num("pg_num") < target_pg:
    print()
    print('Begin Operation...', end='\n\n')
    print(timestamp(), 'check if pgs are clean')
    # check if pool is ready to be incremented
    pg_to_increment = get_pool_pg_num("pg_num") + increment_step
    pgp_to_increment = get_pool_pg_num("pgp_num") + increment_step
    # begin pg increment
    print(timestamp(), 'begin pg increment to:', pg_to_increment)
    increase_pg_num("pg_num", pg_to_increment)
    time.sleep(10)

    total_pg_num = get_total_pg_num()
    while total_pg_num != get_cluster_clean_pg():
        print(timestamp(), 'pg still not clean, waiting...', total_pg_num, get_cluster_clean_pg())
        time.sleep(10)

    # begin pgp_increment
    print(timestamp(), 'begin pgp increment to:', pgp_to_increment)
    increase_pg_num("pgp_num", pgp_to_increment)
    time.sleep(10)

    while total_pg_num != get_cluster_clean_pg():
        print(timestamp(),' pgp still not clean, waiting...', total_pg_num, get_cluster_clean_pg())
        time.sleep(10)
    print(timestamp(),' increase of pg and pgp complete')

print()
print(timestamp(), 'Target PG reached, check your cluster')
print(timestamp(), 'terminated')