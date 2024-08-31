# fluorescence-visualization-dash
Supposed to work with `*.csv` files generated from Cary Eclipse Fluorescence Spectrophotometer.
Quick setup guide for windows in terminal: 
1) `pip install poetry`
2) `git clone git@github.com:acmoudleysa/fluorescence-visualization-dash.git`
3) `poetry install`
4) `poetry shell`
5) Locate the folder where the `*.csv` files are present using `set_data_path \path`, where `\path` is the actual path of the folder
6) Run `run_fluorescence_app`



### To do: 
1) User can upload the file using the upload button but need to add the functionality
2) Could use docker
3) Different wavelength selection for 1D and 2D spectrum. 
4) Cannot be deployed on a server because right now the data objects are global variables. Need to figure this out.

