import os
import click

@click.command()
@click.argument('directory', required=False, type=click.Path(exists=True, file_okay=False, dir_okay=True))
def data_path(directory):
    if directory:
        os.environ['DATA_PATH'] = directory
        click.echo(f"Directory set to: {directory}")
    else:
        os.environ.pop('DATA_PATH', None)
        click.echo("No directory provided. Only upload will be possible.")