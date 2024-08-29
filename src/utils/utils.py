import json 
import pathlib
from typing import Union, Any, Dict, TypedDict, List, Self
import numpy as np
import plotly.graph_objects as go 
import pandas as pd
import plotly_express as px
import numpy.typing as npt

def load_json_file(file_path: pathlib.Path) -> Union[Any, Dict]: 
    """Helper function to load the json file
    """
    if file_path.exists(): 
        with open(file_path, "r") as f: 
            return json.load(f)
    return {}


def save_json_file(file_path: pathlib.Path, data: Any) -> None: 
    """ Helper method to save as a json file"""
    with open(file_path, "w") as f: 
        json.dump(data, f)


class ExcitationEmissionRange(TypedDict): 
    Excitation: List
    Emission: List

class RangeCutTransformer2D():
    """ 
    column_range_modes : ([emi, emi],[exic, exic])
    Make sure the array is in 2d format with excitation as rows and emission as columns.
    """
    def __init__(self,
                columns_range_modes:tuple=([300, 400], [400, 500]),
                exic_emis: ExcitationEmissionRange=None,
                return_2d: bool=False) -> None:
        
        self.columns_range_modes = columns_range_modes
        self.exic_emis = exic_emis
        self._initial_state = {'Excitation': np.array([int(i) for i in self.exic_emis['Excitation']]), 
                              'Emission': np.array([int(i) for i in self.exic_emis['Emission']])}
        self._em = None
        self._ex = None
        self.final_state = {}
        
    def fit(self, 
            X: np.ndarray, 
            y: np.ndarray=None) -> Self:
        
        self._em = np.argmin(np.abs(np.array(self._initial_state['Emission']).reshape(-1, 1) - self.columns_range_modes[0]), axis=0) + [0, 1]
        self._ex = np.argmin(np.abs(np.array(self._initial_state['Excitation']).reshape(-1, 1) - self.columns_range_modes[1]), axis=0) + [0, 1]

        for keys, value in self._initial_state.items(): 
            if keys == 'Emission': 
                self.final_state[keys] = value[slice(*self._em)]
            elif keys == 'Excitation': 
                self.final_state[keys] = value[slice(*self._ex)]
        return self


    def transform(self, 
                  X: np.ndarray) -> np.ndarray:
        return X[:, slice(self._ex[0], self._ex[1]), slice(self._em[0], self._em[1])]



    



def spectrum(data: npt.NDArray, 
             labels: Union[npt.NDArray, List], 
             wavenumbers: ExcitationEmissionRange
             ) -> go.Figure: 
    df = (
        pd.DataFrame(data, columns=wavenumbers)
        .reset_index(drop=False)
        .assign(Excitation=labels)
        .melt(id_vars=["index", "Excitation"], 
              value_name='intensity', 
              var_name="Emission")
    ) 
    colors = px.colors.qualitative.Set1 + \
             px.colors.qualitative.Set2 + \
             px.colors.qualitative.Set3
    label_colors = {
        label:colors[col] for label, col in enumerate(np.unique(labels))
    }

    fig = px.line(
        df, 
        x='Emission', 
        y='intensity', 
        color='Excitation', 
        color_discrete_map=label_colors
    )
    fig.update_layout(
        {"xaxis": dict(mirror=True, 
                       ticks="outside", 
                       nticks=20, 
                       showgrid=False), 
        "yaxis": dict(showgrid=False)
        }, 
    )

    return fig
    

# TO DO: This code needs major refractoring. Way too slow. 
# We will need to vectorize this some day. 
def scatter_removal(
    eem_df, band='rayleigh', order="both", excision_width=50, fill='interp', truncate=None
):
    """
    Author: X from Github
    """
   
    fl = eem_df.to_numpy()
    em = eem_df.index.values.astype(float).astype(int)
    ex = eem_df.columns.to_numpy().astype(float).astype(int)
    grid_ex, grid_em = np.meshgrid(ex, em)
    values_to_excise = np.zeros(eem_df.shape, dtype=bool)

    bands_df = _scatter_bands()
    r = excision_width / 2
    bands_df["above"], bands_df["below"] = [r, r]

    band = band.lower()
    if band in ["rayleigh", "raman"]:
        bands_df = bands_df[bands_df["band"].str.lower() == band]

    order = order.lower()
    if order in ["first", "second"]:
        bands_df = bands_df[bands_df["order"].str.lower() == order]

    def _truncation(row):
        if truncate == "below":
            if row["order"] == "first":
                row["below"] = np.inf

        elif truncate == "above":
            if row["order"] == "second":
                row["above"] = np.inf

        elif truncate == "both":
            if row["order"] == "first":
                row["below"] = np.inf

            if row["order"] == "second":
                row["above"] = np.inf

        return row[["above", "below"]]

    bands_df[["above", "below"]] = bands_df.apply(_truncation, axis=1)

    for index, row in bands_df.iterrows():
        band_name, band_order = row[["band", "order"]]
        peaks = np.polyval(row["poly1d"], ex)
        peaks_grid = np.tile(peaks.reshape(1, -1), (em.size, 1))

        # Create logical arrays with 'True' where flourescent values
        # should be kept.
        keep_above = (grid_em - np.subtract(peaks_grid, row["below"])) <= 0
        keep_below = (grid_em - np.add(peaks_grid, row["above"])) >= 0

        # Update locations of fluorescent values to excise.
        values_to_excise = values_to_excise + np.invert(keep_above + keep_below)

    if fill == None:
        # Create an array with 'nan' in the place of values where scatter
        # is located. This may be used for vizualizing the locations of
        # scatter removal.
        fl_nan = np.array(fl)
        fl_nan = fl_nan.astype(object)
        fl_nan[values_to_excise] = fl_nan[values_to_excise].astype("float64")
        fl_nan[values_to_excise] = np.nan
        eem_df = pd.DataFrame(data=fl_nan, index=em, columns=ex)

    elif fill == "zeros":
        fl_zeros = np.array(fl)
        fl_zeros[values_to_excise] = 0
        eem_df = pd.DataFrame(data=fl_zeros, index=em, columns=ex)

    else:
        # Any other input for fill treat as default fill value of "interp"
        # Create a boolean array of values to keep to use when interpolating.
        values_to_keep = np.invert(values_to_excise)

        # Interpolate to fill the missing values.
        # 'points' is a 'Number of Points' x 2 array containing coordinates
        # of datapoints to be used when interpolating to fill in datapoints.
        points = np.array(
            [
                np.reshape(grid_ex[values_to_keep], (-1)),
                np.reshape(grid_em[values_to_keep], (-1)),
            ]
        )
        points = np.transpose(points)
        values = fl[values_to_keep]

        fl_interp = scipy.interpolate.griddata(
            points, values, (grid_ex, grid_em), fill_value=0
        )
        # Replace excised values with interpolated values.
        fl_clean = np.array(fl)
        fl_clean[values_to_excise] = fl_interp[values_to_excise]
        eem_df = pd.DataFrame(data=fl_clean, index=em, columns=ex)

    return eem_df


def _scatter_bands():
    data = [
        {"band": "Rayleigh", "order": "first", "poly1d": np.poly1d([0, 1.0000, 0])},
        {
            "band": "Raman",
            "order": "first",
            "poly1d": np.poly1d([0.0006, 0.8711, 18.7770]),
        },
        {"band": "Rayleigh", "order": "second", "poly1d": np.poly1d([0, 2.0000, 0])},
        {
            "band": "Raman",
            "order": "second",
            "poly1d": np.poly1d([-0.0001, 2.4085, -47.2965]),
        },
    ]
    return pd.DataFrame.from_records(data)
 

if __name__ == "__main__": 
    example_data = np.random.normal(5, 2.5, size=(3, 100))
    fig = spectrum(example_data, 
             labels=[0, 1, 1], 
             wavenumbers=np.arange(example_data.shape[1]), 
             )
    
    fig.show()

    

