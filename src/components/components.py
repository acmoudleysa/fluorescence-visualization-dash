import dash_bootstrap_components as dbc
from dash import dcc, html
from typing import List, Any, Union, Dict
import dash_ag_grid as dag
from pathlib import Path
from utils.utils import load_json_file, save_json_file


_PATH = Path(__file__).parents[1]/"cache"

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
    "height": "95vh"
}


def make_break(num_breaks: int) -> List[html.Div]: 
    return [html.Br()]*num_breaks


def sidebar() -> html.Div: 
    return html.Div(
                [
                    html.P(
                        "Visualization of spectrum obtained using Fluorescence Spectroscopy", className="fs-4 text fst-italic"
                    ),
                    *make_break(1),
                    dbc.Nav(
                        [
                            dbc.NavLink("Data", href="/page-1", active="exact"),
                            dbc.NavLink("Spectra", href="/page-2", active="exact"),
                        ],
                        vertical=True,
                        pills=True,
                        className="lead fw-bolder"
                    ),
                ],
                style=SIDEBAR_STYLE,
            )


def dropdown_batches() -> dbc.Row: 
    return dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id="dropdown_batch", 
                options=["2014", "2015", "2016"]
            ),
            width={"size": 10}
        )
    ]
    )


def dropdown_samples() -> dbc.Row: 
    return dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id="dropdown_sample", 
                options=["dadsda", "sdsd", "ksdjlfjsd"]
            ),
            width={"size": 10}
        )
    ]
    )

def dropdown_search_samples() -> dbc.Row: 
    return dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id="dropdown_sample_search", 
                options=["ABC FROM 22.csv", "BCD FROM 24.csv", "KJDFD FROM 33.csv"]
            ),
            width={"size": 12}
        )
    ]
    )

def dropdown_content() -> List: 
    return [
        dbc.Row(dbc.Col(html.P("Select a Batch"), className="lead")),
        dropdown_batches(), 
        *make_break(2), 
        dbc.Row(dbc.Col(html.P("Select sample/samples",className="lead"))),
        dropdown_samples(), 
        *make_break(2), 
        dbc.Row(dbc.Col(html.P("Or you can search for the sample name", 
                       className="lead text fst-italic"))),
        dropdown_search_samples()
    ]


def upload_content() -> dcc.Upload:
    return dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select Files')
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px'
                        },
                        multiple=True
                    ) 


def load_bookmarks() -> Union[dcc.Dropdown, dbc.Alert]: 
    file_path = _PATH/"bookmarks.json"
    data = load_json_file(file_path)
    if data: 
        return dcc.Dropdown(
                id="dropdown_bookmark", 
                options=list(data.keys()))
    return dbc.Alert("There are no bookmarks", color="warning", className="fs-2 text"),
     
def return_bookmark_data(key) -> List: 
    file_path = _PATH/"bookmarks.json"
    data = load_json_file(file_path)
    return data[key]

def save_bookmarks(bookmark_name: str, data: Dict) -> dbc.Alert: 
    file_path = _PATH/"bookmarks.json"
    existing_data = load_json_file(file_path)
    if bookmark_name in existing_data: 
            return dbc.Alert("A bookmark with same name already exists!", color="warning", duration=3000)    
    existing_data[bookmark_name] = data
    save_json_file(file_path, existing_data)
    return dbc.Alert("Bookmark saved successfully!", color="success", duration=3000)


def create_table() ->  html.Div: 
    return dag.AgGrid(
            id="table", 
            columnDefs=[

                {"headerName": "Batch", "field": "Batch","checkboxSelection": True, "headerCheckboxSelection": True}, 
                {"headerName": "Name", "field": "Name"}
            ],   
            rowData=[],
            columnSize="sizeToFit",
            defaultColDef={"resizeable": False, "sortable": False},
            dashGridOptions={
                "rowDragManaged": True,
                "rowDragMultiRow": True,
                "rowSelection": "multiple",
                "rowDragEntireRow": True,
            }, style={"fontSize": "16px"})


def table(): 
    return [dbc.Row(html.P("Choose a method to load the data"), className="lead", loading_state={"prop_name": "holds_table", "component_name": "holds_table"}), 
            
            dbc.Row(
                    dbc.Col(dbc.Accordion([dbc.AccordionItem(
                            [html.P("Use the data present in data folder."),
                                dbc.Button("Click here", id="data_folder_button")],
                            title="Use data folder"),
                            dbc.AccordionItem(
                            [html.P("Upload your own data. Make sure the data is in .csv format."),
                                dbc.Button("Click here", id="upload_button")],
                                title="Upload",
                            ),
                            dbc.AccordionItem(
                            [html.P("Use bookmarked data."),
                             dbc.Button("Click here", id='bookmark_button')],
                            title="Load bookmarks",
                            )],
                            start_collapsed=True),
                            width=4), className="mb-4"
                        ),

            dbc.Row([
                    dbc.Col(children=[], id="left_main_content", width=4),
                    dbc.Col(
                        [dbc.Row([
                                dbc.Col([dbc.Button("Delete selected", id="delete_button", color="danger", n_clicks=0),
                                dbc.Tooltip("Delete the selected rows?", 
                                            target="delete_button")]),
                                dbc.Col([dbc.Button("Do you want to bookmark this data?", 
                                        id="bookmark", color="dark", className="float-end")])]), 
                                create_table(),
                                dbc.Modal(
                                    [
                                        dbc.ModalHeader("Enter Bookmark Name"),
                                        dbc.ModalBody(
                                            dbc.Input(id="bookmark-name", placeholder="Type bookmark name...", type="text")
                                        ),
                                        dbc.ModalFooter(
                                            [dbc.Button("Save", id="save-bookmark", color="success", n_clicks=0),
                                            dbc.Button("Cancel", id="close-modal", color="danger", n_clicks=0)]
                                        ),
                                    ],
                                    id="modal",
                                    is_open=False, 
                                ),
                        
                        dbc.Tooltip(
                            "You can save the data on the table for quick references.", 
                            target="bookmark"
                        ),
                        dbc.Row([dbc.Col(children=[], id="bookmark_success", width=8), 
                                dbc.Col(dbc.Button("Confirm Selection", id="confirm_selection_button",className="float-end")
                                , width=4)])], 
                        width=5)
                    ], 
                    justify="between")
            ]


tab_2d_content = html.Div(
    children=[], 
    id="oneD", 
    style={"height": "82vh"}
)

tab_1d_content = html.Div(
    children=[], 
    id="twoD", 
    style={"height": "82vh"}
)

def collapse_wavelength_selection(): 
    return html.Div(
        children=[
            dbc.Button("Change wavelength?", size="sm", id="button_collapse"), 
            
            dbc.Collapse([
                *make_break(1), 
                dbc.Row(
                    [html.P("Emission (minimum)"), 
                     dbc.Input(id="emission_min", min=200, max=800, value=200, style={"width": "60%"}, class_name="mx-3")]
                ), 
                *make_break(1),
                dbc.Row(
                    [html.P("Emission (maximum)"), 
                     dbc.Input(id="emission_max", min=200, max=800, value=800, style={"width": "60%"}, class_name="mx-3")]
                ), 
                *make_break(1),
                dbc.Row(
                    [html.P("Excitation (minimum)"), 
                     dbc.Input(id="excitation_min", min=200, max=800, value=200, style={"width": "60%"}, class_name="mx-3")]
                ), 
                *make_break(1),
                dbc.Row(
                    [html.P("Excitation (maximum)"), 
                     dbc.Input(id="excitation_max", min=200, max=800, value=800, style={"width": "60%"}, class_name="mx-3")]
                )], 
                id="collapse", 
                is_open=False
            )
        ], 
        className="float-end"
    )


def spectrum_page() -> List: 
    return [
        dbc.Row(
            dbc.Col([dbc.Button("Click here to create the figure", id="create_figure")], 
                    width=5)
            ), 
        *make_break(1), 
        dbc.Row([dbc.Col(html.Div(dbc.Tabs
                ([
                dbc.Tab([*make_break(1), tab_1d_content], label="1D spectra", tab_class_name ="flex-grow-1 text-center ", active_tab_class_name ="fw-bold"),
                dbc.Tab([*make_break(1), tab_2d_content], label="2D spectra", tab_class_name ="flex-grow-1 text-center", active_tab_class_name ="fw-bold")
                ]
                ,
                ),style={"height":"90%"}), width=11), 
                dbc.Col(collapse_wavelength_selection(), width=1, class_name="float-end")])
    ]

def render_page_1_content() -> List[Any]: 
    data_file = _PATH/"data_tab.json"
    data = load_json_file(data_file)
    if data: 
        return data
    return table()


def save_page_1_content(data: Any) -> None: 
    data_file = _PATH/"data_tab.json"
    # TO DO: Find better ways to do this
    try: 
        if data and isinstance(data, list) and \
        (data[0]['props']['children']['props']['children'] 
         == "Choose a method to load the data"): 
            save_json_file(data_file, data)

    except KeyError as err: 
        print("I am a bug but I am ignored") 

    
def main_content() -> html.Div: 
    return html.Div(  
        id="main-content", 
        style=CONTENT_STYLE
        )


