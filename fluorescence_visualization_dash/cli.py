import click
from fluorescence_visualization_dash.utils.utils import save_json_file

@click.command()
@click.argument('directory', required=False, type=click.Path(exists=True, file_okay=False, dir_okay=True))
def data_path(directory):
    if directory:
        save_json_file("config.json", 
                       {"data_path": directory})
        click.echo(f"Directory set to: {directory}")
    else:
        click.echo("No directory provided. Only upload will be possible.")