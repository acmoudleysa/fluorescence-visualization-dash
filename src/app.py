import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html, State
from components.components import main_content, \
    sidebar, dropdown_content, \
    render_page_1_content, save_page_1_content, \
    upload_content, load_bookmarks, save_bookmarks, \
    spectrum_page, return_bookmark_data
from dash import callback_context as ctx
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

app = dash.Dash(external_stylesheets=[dbc.themes.YETI],
                suppress_callback_exceptions=True)

app.layout = html.Div(
    [dcc.Location(id="url"), 
     sidebar(), 
     main_content(), 
     dcc.Store(id="table_data_store", storage_type='local')])


@app.callback(
    Output(component_id="dropdown_sample", component_property="options"), 
    Input(component_id="dropdown_batch", component_property="value"))
def show_samples(val): 
    if val is not None: 
        return [1,2,3,4,5, "hey"]
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
    [State('table', 'rowData') 
    ], 
    prevent_initial_call=True
)
def creating_table_from_bookmark(bookmark, data): 
    if (not ctx.triggered) or (bookmark is None): 
        raise PreventUpdate
    
    _data_bookmark = return_bookmark_data(bookmark)
    # TO DO: Currently it is possible to first select the bookmark \
    # and then select using batch and samples but not the other way around
    return _data_bookmark


# This callback can be modified by using the in-built dcc.Store class.
# I have used dcc.Store later to save the table data
@app.callback( Output("main-content", "children"), 
              [Input("url", "pathname")], 
              State("main-content", "children")
              )
def render_page_content(pathname, children):
    if pathname == "/page-1":
        return render_page_1_content()
    elif pathname == "/page-2":
        save_page_1_content(data=children)
        return spectrum_page()
    else: 
        raise PreventUpdate


@app.callback(
        Output(component_id="left_main_content", component_property="children"), 
        [Input(component_id="data_folder_button", component_property="n_clicks"), 
         Input(component_id="upload_button", component_property="n_clicks"), 
         Input(component_id="bookmark_button", component_property="n_clicks")], 
         prevent_initial_call=True
)
def left_main_content(*unused):
    if ctx.triggered_id == "data_folder_button": 
        return dropdown_content()
    elif ctx.triggered_id == "upload_button": 
        return upload_content()
    elif ctx.triggered_id == "bookmark_button": 
        return load_bookmarks()
    else: 
        raise PreventUpdate



@app.callback(
    [Output("modal", "is_open"), 
    Output("bookmark_success", "children"), 
    Output("save-bookmark", "n_clicks")],
    [Input("bookmark", "n_clicks"), 
    Input("close-modal", "n_clicks"), 
    Input("save-bookmark", "n_clicks")],
    [State("bookmark-name", "value"), 
     State("modal", "is_open"), 
     State("table", "virtualRowData")], 
    prevent_initial_call=True
)
def toggle_modal(open_click, close_click, save_click, bookmark, is_open, tableData):
    if not tableData: 
        raise PreventUpdate
    if save_click & (bookmark is not None): 
        return not is_open, save_bookmarks(bookmark, tableData), 0
    elif open_click or close_click or save_click: 
        return not is_open, [], 0
    return is_open, [], 0


@app.callback(
    Output("table", "deleteSelectedRows"),
    Input("delete_button", "n_clicks"),
    State("table", "rowData"),
    prevent_initial_call=True
)
def selected(*unused):
    return True


@app.callback(
        Output("table_data_store", "data"), 
        Input("confirm_selection_button", "n_clicks"), 
        State("table", "virtualRowData")
)
def store_data(n_clicks, data): 
    if not data: 
        raise PreventUpdate
    
    if n_clicks: 
        return data
    

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
    Output("oneD", "children"),
    Output("twoD", "children"),
    [Input('create_figure', 'n_clicks')],
    [State("table_data_store", "data"), 
    State("emission_min", "value"), 
    State("emission_max", "value"), 
    State("excitation_min", "value"), 
    State("excitation_max", "value")], 
    prevent_initial_call=True
)

def get(click, data, em_min, em_max, ex_min, ex_max):
    if not data: 
        raise PreventUpdate
    if click:
        fig1 = go.Figure()
        fig2 = go.Figure()
        return dcc.Graph(figure=fig1, style={"width": "100%", "height": "100%"}), dcc.Graph(figure=fig2, style={"width": "100%", "height": "100%"})


if __name__ == "__main__":
    app.run(debug=True, port=4000)

