"""Console script for automount_viz."""
import sys
import click
from .automount_viz import parse_automount_dir


@click.option('-i', '--indir', default='/etc/automount', type=click.Path(exists=True))
@click.command()
def main(indir):
    """Console script for automount_viz."""
    click.echo("Replace this message by putting your code into "
               "automount_viz.cli.main")
    click.echo("See click documentation at https://click.palletsprojects.com/")
    parse_automount_dir(indir)

