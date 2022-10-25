"""Main module."""
import graphlib
import pandas as pd
import os
from pathlib import Path
import subprocess as sp
from io import BytesIO
import re
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx


def parse_automount_file(fname):
    "Parses the file in /etc/automount into a pandas DataFrame. "
    "Tries to guess which is the server:/path/to/mount string since this apparently "
    "is not a well-defined TSV"
    try:
        df = pd.read_csv(fname, delim_whitespace=True, header=None, 
                         index_col=None, comment='#', 
                         on_bad_lines=lambda x: [x[0], [i for i in x if ":/" in i][0]], 
                         engine='python')
        df.columns = ['MOUNT_DIR', "SERVER_LOCAL_DIR"]
        df['AUTOMOUNT_FILE'] = fname
        df[['SERVER', "LOCAL_DIR"]] = df['SERVER_LOCAL_DIR'].str.split(':', n=1, expand=True)
        return df
    except pd.errors.EmptyDataError:
        return None

def parse_automount_master(fname):
    "Return a DataFrame of the automount master. All files in second column are valid "
    "things being automounted. Things with '/-' in the first column are direct autofs maps."
    df = pd.read_csv(fname, delim_whitespace=True, header=None, index_col=None, comment='#')
    df.columns = ['MOUNT_DIR', 'AUTOMOUNT_FILE', '_', '__']
    # remove "/-" which correspond to direct autofs maps
    df["DIRECT_MAP"] = df['MOUNT_DIR'] == "/-"
    return df

def parse_automount_dir(automaster_path, exclude=[]):
    "Parses the given directory (default /etc/automount) and returns a single pandas DataFrame "
    "excluding files in `exclude` because they make no sense (?) and replacing '*' "
    "with the contents of /etc/auto.master for indirect mounts in the corresponding "
    "files"
    automaster_df = parse_automount_master(automaster_path)
    indirect_maps = automaster_df[~automaster_df['DIRECT_MAP']]
    dfs = []

    fnames = (f for f in automaster_df['AUTOMOUNT_FILE'] if f not in exclude)

    for fname in fnames:
        df = parse_automount_file(fname)
        if df is None:
            continue
        if fname in list(indirect_maps['AUTOMOUNT_FILE']):
            mount_dir = automaster_df[automaster_df['AUTOMOUNT_FILE'] == fname]['MOUNT_DIR'].iloc[0]
            df['MOUNT_DIR'] = mount_dir
        dfs.append(df)

    df = pd.concat(dfs)
    pd.set_option('display.max_rows', None)
    return df


def parse_sinfo(cmd):
    "parses sinfo, expanding each deep[5-8] into a separate entry"
    sinfo = sp.check_output(cmd, shell=True)
    df = pd.read_csv(BytesIO(sinfo), encoding="utf-8", delim_whitespace=True)
    new_df = []
    for __, row in df.iterrows():
        for node in expand_nodes(row["NODELIST"]):
            new_row = pd.concat([row.drop(["NODELIST", "NODES"]), pd.Series({"NODE": node})])
            new_df.append(new_row)
    new_df = pd.concat(new_df, axis=1)
    return new_df.T

def expand_nodes(s):
    "Given a string in format deep[13-14] returns a list ['deep13' 'deep14']"
    prefix, nums = re.search("([a-zA-Z]+)\[?([0-9\-,]+)\]?", s).groups()
    final_nums = []
    for num_range in nums.split(","):
        if "-" in num_range:
            first, last = (int(x) for x in num_range.split("-"))
            final_nums += list(range(first, last+1))
        else:
            final_nums.append(int(num_range))
    return [prefix + str(num) for num in final_nums]

def nx_graph_from_automount(df, outfile, sinfo=None):
    "sinfo is optional sinfo cmd"
    graph = nx.Graph()

    server_labels = {}
    mount_labels = {}
    legend = {}

    for __, row in df.iterrows():
        graph.add_node(row['SERVER'], type='server', partition=None)
        graph.add_node(row['MOUNT_DIR'], type='mount', partition=None)
        graph.add_edge(row['SERVER'], row['MOUNT_DIR'])
        server_labels[row['SERVER']] = row['SERVER']
        mount_labels[row['MOUNT_DIR']] = (row['MOUNT_DIR'] + '\n' + row['SERVER'])

    # nodes 
    if sinfo:
        sinfo = parse_sinfo(sinfo)
        for __, row in sinfo.iterrows():
            graph.add_node(row['NODE'], type="server")
            attrs = {row['NODE'] : {'compute-node': True, 'partition': row['PARTITION']}}
            # set node attributes in case the node already exists
            nx.set_node_attributes(graph, attrs)
            server_labels[row['NODE']] = row['NODE']

    pos = nx.spring_layout(graph, k=0.99, iterations=25)

    # mount dirs are blue
    nx.draw_networkx_nodes(graph, pos, list(df['MOUNT_DIR']), node_color="tab:blue", node_size=3600)
    legend['tab:blue'] = 'Mount Directory'

    if sinfo is not None:
        nx.draw_networkx_nodes(graph, pos, list(sinfo['NODE']), node_color='tab:green', node_size=7200)
    legend['tab:green'] = 'Compute Node (exclusively)'

    # servers are red
    nx.draw_networkx_nodes(graph, pos, list(df['SERVER']), node_color='tab:red', node_size=7200)
    legend['tab:red'] = 'File Server'

    # graph edges are sweet
    nx.draw_networkx_edges(graph, pos, edge_color="grey")

    # and so are you 
    nx.draw_networkx_labels(graph, pos, server_labels, font_size=18, font_color="whitesmoke")
    nx.draw_networkx_labels(graph, pos, mount_labels, font_size=5, font_color="whitesmoke")

    ax = plt.gca()
    plt.axis("off")
    fig = plt.gcf()
    fig.set_size_inches(30, 30)
    
    ax.legend(handles=list(mpatches.Patch(color=k, label=v) for k, v in legend.items()))
    #plt.tight_layout()
    plt.show()
    plt.savefig(outfile, dpi=600)

