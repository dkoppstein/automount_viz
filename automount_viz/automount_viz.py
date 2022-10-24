"""Main module."""
import pandas as pd
import os
from pathlib import Path

def parse_automount_file(fname):
    try:
        df = pd.read_csv(fname, delim_whitespace=True, header=None, index_col=None, comment='#', on_bad_lines=lambda x: [x[0], [i for i in x if ":/" in i][0]], engine='python')
        df.columns = ['MOUNT_DIR', "SERVER_LOCAL_DIR"]
        df[['SERVER', "LOCAL_DIR"]] = df['SERVER_LOCAL_DIR'].str.split(':', n=1, expand=True)
        return df
    except pd.errors.EmptyDataError:
        return None

def parse_automount_dir(dname, exclude=["auto.vmhosts"]):
    dfs = []
    fnames = (f for f in os.listdir(dname) if f not in exclude)
    for fname in fnames:
        print(fname)
        df = parse_automount_file(Path(dname) / fname)
        if df is not None:
            dfs.append(df)
    df = pd.concat(dfs)
    pd.set_option('display.max_rows', None)
    print(df)

def parse_automount_master(fname):
    df = pd.read_csv(fname, delim_whitespace=True, header=None, index_col=None, comment='#', on_bad_lines=lambda x: [x[0], [i for i in x if ":/" in i][0]], engine='python')