"""Console script for automount_viz."""
import sys
import click
from .automount_viz import parse_automount_dir, nx_graph_from_automount

@click.option('-m', '--automount-master', default='/etc/auto.master', 
              type=click.Path(exists=True))
@click.option('-s', '--sinfo-cmd', default='module load slurm; sinfo')
@click.option('-e', '--automount-exclude', default=[], 
              multiple=True, type=click.Path(exists=True))
@click.option('-p', '--parse-slurm', default=True)
@click.option('-o', '--outfile', default="automount_viz.pdf")
@click.command()
def main(sinfo_cmd, automount_master, outfile, automount_exclude, parse_slurm):
    """Console script for automount_viz."""
    click.echo("Replace this message by putting your code into "
               "automount_viz.cli.main")
    click.echo("See click documentation at https://click.palletsprojects.com/")
    df = parse_automount_dir(automount_master, exclude=automount_exclude)
    sinfo = sinfo_cmd if parse_slurm else None
    nx_graph_from_automount(df, outfile, sinfo=sinfo)

