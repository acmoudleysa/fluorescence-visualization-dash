import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html, State
from fluorescence_visualization_dash.components.components import main_content, \
    sidebar, dropdown_content, \
    upload_content, load_bookmarks, save_bookmarks, \
    spectrum_page, return_bookmark_data, table, remove_bookmarks_json
from dash import no_update, callback_context as ctx
from dash.exceptions import PreventUpdate
from fluorescence_visualization_dash.dataloader.dataloader import FluorescenceData
import textwrap
import os
from fluorescence_visualization_dash.utils.utils import load_json_file


DATA_FOLDER_PATH = load_json_file("config.json").get("data_path", None)

app = dash.Dash(external_stylesheets=[dbc.themes.YETI],
                suppress_callback_exceptions=True)

fluorescence_obj = None
fluorescence_obj_scatter_corr = None

if DATA_FOLDER_PATH:
    if os.path.exists(DATA_FOLDER_PATH): 
        fluorescence_obj = FluorescenceData(
                        filepath=DATA_FOLDER_PATH, 
                        scatter_correction=False
                    )
        fluorescence_obj_scatter_corr = FluorescenceData(
                        filepath=DATA_FOLDER_PATH, 
                        scatter_correction=True
                    )

app.layout = html.Div(
    [dcc.Location(id="url"), 
     sidebar(), 
     main_content(), 
     dcc.Store(id="table_store", storage_type="session", data=[]), 
     dcc.Store(id="wavelength_selection", storage_type="session", data=[])])


@app.callback(
    Output(component_id="dropdown_sample", component_property="options"), 
    Input(component_id="dropdown_batch", component_property="value"), 
    prevent_initial_call=True)
def show_samples(val): 
    if val is not None: 
        return list(fluorescence_obj.df.loc[
            lambda x: x.Batch == val, "Name"
        ])
    else: 
        raise PreventUpdate




@app.callback(
    Output("table", "rowData"),
    [Input('dropdown_sample', 'value'),
     Input('dropdown_sample_search', 'value')],
    [State('table', 'rowData'), 
     State('dropdown_batch', 'value'),
     ]
)
def creating_table(sample_first_route, sample_second_route, data, batch): 
    if not ctx.triggered: 
        raise PreventUpdate
    
    if ctx.triggered_id == "dropdown_sample_search": 
        if sample_second_route is not None: 
            _sample, _batch = [str(s.strip()) for s in sample_second_route.split("FROM")]
        else: 
            raise PreventUpdate

    elif ctx.triggered_id == "dropdown_sample": 
        if sample_first_route is not None: 
            _batch = batch
            _sample = sample_first_route
        else: 
            raise PreventUpdate
        
    else: 
        raise PreventUpdate
    
    for row in data: 
        if (row['Batch'] == _batch) and (row['Name'] == _sample): 
            raise PreventUpdate
        
    data.append({"Batch": _batch, "Name": _sample})
    return data



@app.callback(
    Output("table", "rowData", allow_duplicate=True),
    [Input('dropdown_bookmark', 'value')],
    prevent_initial_call=True
)
def creating_table_from_bookmark(bookmark): 
    if (not ctx.triggered) or (bookmark is None): 
        raise PreventUpdate
    
    _data_bookmark = return_bookmark_data(bookmark)
    return _data_bookmark


@app.callback(Output("main-content", "children"), 
              [Input("url", "pathname")], 
              [State("table_store", "data"), 
               State("wavelength_selection", "data")]
              )
def render_page_content(pathname, virtualtabledata, wv_data):
    if pathname == "/page-1":
        return table(virtualtabledata)
    elif pathname == "/page-2":
        return spectrum_page(wv_data)
    else: 
        raise PreventUpdate


@app.callback(
        Output("table_store", "data"),  
        Input("confirm_selection_button", "n_clicks"), 
        State("table", "virtualRowData"), 
        prevent_initial_call=True
)
def store_data(n_clicks, tabledata): 
    if not n_clicks or not tabledata: 
        raise PreventUpdate
    
    if n_clicks: 
        return tabledata
    


@app.callback(
        Output(component_id="left_main_content", component_property="children"), 
        Output("bookmark_button", "n_clicks", allow_duplicate=True), 
        [Input(component_id="data_folder_button", component_property="n_clicks"), 
         Input(component_id="upload_button", component_property="n_clicks"), 
         Input(component_id="bookmark_button", component_property="n_clicks")], 
         prevent_initial_call=True
)
def left_main_content(*unused):
    if (fluorescence_obj is None ) & (ctx.triggered_id in ["data_folder_button", "upload_button"]): 
        return dbc.Alert("There are no csv files in the folder", 
                        color="warning", className="fs-2 text"), no_update
    if ctx.triggered_id == "data_folder_button":
        return dropdown_content(fluorescence_obj.df), no_update
    elif ctx.triggered_id == "upload_button": 
        return upload_content(), no_update
    elif ctx.triggered_id == "bookmark_button": 
        return load_bookmarks(), 1
    else: 
        raise PreventUpdate



@app.callback(
    [Output("modal", "is_open"), 
    Output("bookmark_success", "children"), 
    Output("save-bookmark", "n_clicks"), 
    Output("bookmark_button", "n_clicks", allow_duplicate=True)],
    [Input("bookmark", "n_clicks"), 
    Input("close-modal", "n_clicks"), 
    Input("save-bookmark", "n_clicks")],
    [State("bookmark-name", "value"), 
     State("bookmark_button", "n_clicks"),
     State("modal", "is_open"), 
     State("table", "virtualRowData")], 
    prevent_initial_call=True
)
def toggle_modal(open_click, close_click, save_click, bookmark, val_bookmark_button,  is_open, tableData):
    if not tableData: 
        raise PreventUpdate
    if save_click & (bookmark is not None): 
        return not is_open, save_bookmarks(bookmark, tableData), 0, 1 if val_bookmark_button else no_update 
    elif open_click or close_click or save_click: 
        return not is_open, [], 0, no_update
    return is_open, [], 0, no_update

@app.callback(
    [Output("modal-bookmark-remove", "is_open"), 
    Output("remove-bookmark", "n_clicks"), 
    Output(component_id="bookmark_button", component_property="n_clicks")],
    [Input("remove_bookmark_button", "n_clicks"), 
    Input("donot-remove-modal", "n_clicks"), 
    Input("remove-bookmark", "n_clicks")
    ],
    [State("bookmark-name-to-delete", "value"), 
     State("modal-bookmark-remove", "is_open"), 
     State(component_id="bookmark_button", component_property="n_clicks")], 
    prevent_initial_call=True
)
def toggle_modal(open_click, close_click, remove_click, bookmarks, is_open, clicks):
    if bookmarks is not None: 
        remove_bookmarks_json(bookmarks)
        return not is_open, 0, clicks   # clicks + 1 is not necessary, it turns out even on the same n_clicks it is triggered
    elif open_click or close_click or remove_click: 
        return not is_open, 0, no_update
    return is_open, 0, no_update


@app.callback(
    Output("table", "deleteSelectedRows"),
    Input("delete_button", "n_clicks"),
    State("table", "rowData"),
    prevent_initial_call=True
)
def selected(*unused):
    return True

@app.callback(
        Output("collapse", "is_open"), 
        [Input("button_collapse", "n_clicks")], 
        [State("collapse", "is_open")]
)
def toggle_collapse(n, is_open): 
    if n: 
        return not is_open
    return is_open


@app.callback(
        Output("collapse_preprocess", "is_open"), 
        [Input("preprocessing_button", "n_clicks")], 
        [State("collapse_preprocess", "is_open")]
)
def toggle_collapse_preprocess(n, is_open): 
    if n: 
        return not is_open
    return is_open



@app.callback(
    Output("oneD", "children"),
    Output("twoD", "children"),
    Output("wavelength_selection", "data"),
    [Input('create_figure', 'n_clicks')],
    [State("table_store", "data"), 
    State("emission_min", "value"), 
    State("emission_max", "value"), 
    State("excitation_min", "value"), 
    State("excitation_max", "value"),
    State("preprocessing_type", "value")],
    prevent_initial_call=True
)

def get(click, data, em_min, em_max, ex_min, ex_max, pp_type):
    def check_presence(df):
        indices = []
        for row in data:
            matched_indices = df.index[(df.Batch == row['Batch']) & (df.Name == row['Name'])]
            indices.extend(matched_indices)
        return indices

    if not data: 
        raise PreventUpdate
    
    if click:
            index_loc = check_presence(fluorescence_obj.df)
            # Generate the 1D figure

            if pp_type == "Raw": 
                obj = fluorescence_obj
            else: 
                obj = fluorescence_obj_scatter_corr


            fig_1d = obj.get_spectrum(
                index_loc=index_loc, 
                select_range=([em_min, em_max], [ex_min, ex_max]))

            fig_2d = obj.get_2d_spectra_plotly_multiple(
                index_loc=index_loc,
                select_range=([em_min, em_max], [ex_min, ex_max]))
            
            for traces in fig_1d.data: 
                traces['name'] = '<br>'.join(textwrap.wrap(traces['name'], 25))

            return dcc.Graph(figure=fig_1d, style={"width": "100%", "height": "100%"}),\
                  dcc.Graph(figure=fig_2d, style={"width": "100%", "height": "100%"}), \
                  [em_min, em_max, ex_min, ex_max]
        
    else: 
        raise PreventUpdate
    

def main(): 
    app.run(debug=True, port=4000)

if __name__ == "__main__":
    main()
