# Copyright 2023 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import psycopg2 as pg
import sys
import subprocess

def connection():

    conn = pg.connect(
        database = "omniadb",
        user = "postgres",
        host = "localhost",
        port = "5432",
    )

    return conn


def run_cmd(cmd):
    run = subprocess.run(cmd,shell=True,capture_output=True,text=True)

    if 'ERROR' in run.stderr:
        return False,run.stderr,run.stdout
    else:
        return True,run.stderr,run.stdout


def fetch_nodes(conn,host_ip):

    cur = conn.cursor()

    sql = '''select node, bmc_ip from cluster.nodeinfo where bmc_ip = inet('{host_ip}')'''.format(host_ip=host_ip)
    cur.execute(sql)
    rows = cur.fetchall()

    if len(rows) != 0:
        return rows[0]
    else:
        return None


def fetch_group(rows):

    if len(rows) != 0:

        cmd = '''lsdef {nodename} -i groups -c | sed -n "/{nodename}: groups=/s/{nodename}: groups=//p"'''.format(nodename=rows[0])

        grps, err, out = run_cmd(cmd)

        if grps:
            return str(out).strip(),rows
        else:
            print(f" No group found for the node {rows[0]}, error : {err}")


def rset_boot(node,osimage):

    nodename = node[0]
    nodeip = node[1]

    cmd = ''' rsetboot {} net'''.format(nodename)

    set_boot, err ,out = run_cmd(cmd)

    if set_boot:

        cmd = ''' rpower {} reset '''.format(nodename)
        boot_node, er, ou = run_cmd(cmd)

        if boot_node:
            print(f"Started provisioning node : {nodename} having IP Address : {nodeip} with {osimage} using bmc")
        else:
            print(f" Failed to power on the node {nodename} having IP Address : {nodeip}. Please check the connection. Error : {er}")
    else:
        print(f"Setting PXE boot on {nodename} having IP Address : {nodeip}. Failed with error : {err} ")


def node_set(node,osimage):

    nodename = node[0]
    nodeip = node[1]

    cmd = ''' nodeset {node} osimage = {os}'''.format(node=nodename,os=osimage)

    set_boot, err, out = run_cmd(cmd)

    if set_boot:
        print(f"Provisioning started for node : {nodename} having IP Address : {nodeip} with {osimage} using snmp/mapping. Please reboot the node to trigger the OS Installation")
    else:
        print(f"Setting the osimage for snmp/mapping node : boot on {nodename} having IP Address : {nodeip}. Failed with error : {err} ")


def set_image(node,osimage):

    nodename = node[0]
    nodeip = node[1]

    cmd = ''' chdef {node} chain=runcmd=bmcsetup,osimage={osimage}'''.format(node=nodename,osimage=osimage)
    img, err, out = run_cmd(cmd)

    if not img:
        print(f"Setting the osimage failed for the node : {node} having IP Address : {nodeip} with the error : {err}")
    else:
        return 1


def reprovision_nodes(grp,node,osimage):
    nodename = node[0]
    nodeip = node[1]

    if grp == 'snmp':
        node_set(node,osimage)

    elif grp == 'bmc':
        img = set_image(node,osimage)
        rset_boot(node,osimage)

    elif grp == 'mapping':
        node_set(node,osimage)

    else:
        print(f"Node : {nodename} having IP Address : {nodeip} doesn't belong to any group[snmp,bmc,mapping], please check whether the node was added using Omnia")


def main():


    host_ip = sys.argv[1:-1]
    osimage = sys.argv[-1]

    conn = connection()

    for ip in host_ip:
        group = ''
        node = ''
        rows = fetch_nodes(conn,ip)

        if rows != None:
            group,node = fetch_group(rows)
        else:
            print(f"{ip} doesn't exists, please check the IP and run the script again")
            continue

        if group != None and node != None:
            reprovision_nodes(group,node,osimage)
    
    conn.close()

if __name__ == '__main__':
    main()
