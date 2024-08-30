from typing import Union, List, Tuple, Optional, Literal
import os
import pathlib
import logging
import json
import pandas as pd
from tqdm import tqdm
from datetime import datetime
import numpy as np
import numpy.typing as npt
from src.utils.utils import scatter_removal, spectrum, RangeCutTransformer2D
import math
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from itertools import product


class FluorescenceData:
    """
    """
    def __init__(self, 
                 filepath: Union[str, os.PathLike], 
                 scatter_correction = False, 
                 cache_filename: str = "rawdata_cache.pickle",
                 rename_filename: str = "rename.json",
                 purge_cache: bool = False,                 
                 ) -> None:
        
        self.filepath = pathlib.Path(filepath)
        self.scatter_correction = scatter_correction
        self.df = None
        if self.scatter_correction: 
            self.cache_filename = "corrected_" + cache_filename
        else: 
            self.cache_filename = cache_filename
        self.__purge_cache(purge_cache)
        self._preprocessed_files = self.__load_processed_file_names(self.cache_filename)
        self._rename_dict = self.__load_json_config(rename_filename)
        self.__load_data()


    def __purge_cache(self, purge_cache: bool) -> None:
        """Delete the cache file if purge_cache is True."""
        if purge_cache and (self.filepath/self.cache_filename).exists():
            logging.warning("Deleting the cache")
            os.remove(self.filepath/self.cache_filename)


    def __load_json_config(self, filename: str) -> dict:
        """
        Load JSON configuration from the given file, or return an empty dictionary if not found.
        """
        if (self.filepath / filename).exists():
            with open(self.filepath / filename, 'r') as f:
                return json.load(f)
        return {}


    def __load_processed_file_names(self, filename: str) -> List: 
        """
        Loads if cachce file is present
        """
        if (self.filepath/filename).exists():
            try: 
                self.df = pd.read_pickle(self.filepath/filename)
                return self.df.Batch.tolist()
            except Exception as e: 
                raise e
        self.df = pd.DataFrame({
                                    "Batch": pd.Series(dtype="str"), 
                                    "Name": pd.Series(dtype="str"), 
                                    "Metadata": pd.Series(dtype="object"),
                                    "Data": pd.Series(dtype="object")
                                   
                                })
        return list()
    

    def __save_processed_data(self) -> None: 
        """
        Saves the files to existing/non-existing cache
        """
        pd.to_pickle(self.df ,
                     self.filepath/self.cache_filename)
        

    def __load_data(self) -> None: 
        filenames = list(self.filepath.glob("*.csv"))
        logging.info(f"{len(filenames)} files are found.")
        newfiles = set(filenames) - set(map(lambda x: self.filepath/x, self._preprocessed_files))
        logging.info(f"{len(newfiles)} new files are found.")
        new_data = []
        if newfiles: 
            for file in tqdm(sorted(newfiles, key=os.path.getmtime), desc="Processing files"):
                dataframe_temp = pd.read_csv(file)    # TO DO: Consider using polars for efficiency 
                unique_samples = set([col.split("_EX_")[0] for col in dataframe_temp.columns if "_EX_" in col])  # sadly this doesnt presever the order
                temp_dict = self._rename_dict[file.name] if file.name in self._rename_dict else {}
                date = datetime.fromtimestamp(os.path.getmtime(file))
                for sample in unique_samples: 
                    metadata = {}
                    metadata['Date'] = date
                    (indiv_data, excitation_wl, emission_wl) = self.indiv_dataframe(dataframe_temp, file.name, sample)
                    metadata['Excitation'] = excitation_wl
                    metadata['Emission'] = emission_wl
                    if sample in temp_dict: 
                        new_data.append([file.name, temp_dict[sample], metadata, indiv_data])
                    else: 
                        new_data.append([file.name, sample, metadata, indiv_data])

            self.df = pd.concat((self.df, 
                                    (pd.DataFrame(new_data, 
                                                columns=['Batch', 'Name', 'Metadata', 'Data'])
                                    .astype({
                                            "Batch": "str",
                                            "Name": "str",
                                            "Metadata": "object", 
                                            "Data": "object", 
                                            
                                        }))),
                                ignore_index=True
                                )
           
            self.__save_processed_data()  

    def indiv_dataframe(self, 
                        dataframe: pd.DataFrame, 
                        file: str, 
                        sample: str) -> Tuple[npt.NDArray, npt.NDArray, npt.NDArray]: 
        """
        Get the numpy array for individual samples. 
        Receives emission along the rows and excitation along the columns
        Returns the excitation along the rows and emission along the columns. 
        """
        idx, ex_wl = zip(*[[i+1, wavelengths.split("_EX_")[-1].split(".")[0]] 
                           for i, wavelengths in enumerate(dataframe.columns) if sample + "_EX_" in wavelengths])
        
        df = (dataframe.iloc[1:, list(idx)]
              .set_axis(np.array(ex_wl, dtype=int), axis="columns")
              .set_axis(dataframe.iloc[1:, 0].to_numpy().astype(float).astype(int), 
                        axis="index")
              )
        if self.scatter_correction: 
            df = scatter_removal(df, excision_width=25, truncate="below")

        return (df.to_numpy(dtype=np.float32).T, 
                df.columns.to_numpy(),   # ex
                df.index.to_numpy())   # em
    

    def get_spectrum(self, 
                     batch: Optional[str] = None, 
                     name: Optional[str] = None, 
                     index_loc: Optional[List[int]] = None, 
                     select_range: Optional[Tuple] = ([200, 800], [200, 800])
                ) -> go.Figure:
        
        if index_loc is not None: 
            df = self.df.loc[index_loc]

        elif (batch is not None) and (name is not None): 
            df = self.df.loc[lambda x: (x.Batch == batch) & (x.Name == name)]
        
        else: 
            df = self.df

        try: 
            data_stacked = np.stack(df.Data.to_numpy(), axis=0) 
            ex_em_dict = df.iloc[0]['Metadata'].copy()
            del ex_em_dict['Date']
            
            rg_transform = RangeCutTransformer2D(select_range, 
                                                 ex_em_dict,
                                                 True)
            data_stacked = rg_transform.fit_transform(data_stacked)
            ex_em_dict['Emission'] = rg_transform.final_state['Emission']
            ex_em_dict['Excitation'] = rg_transform.final_state['Excitation']

        except ValueError: 
            raise ValueError("Make sure the data is complete.")
        

        fig = spectrum(
            np.vstack(data_stacked), 
            labels=(df.Name + " " + df.Batch).to_numpy().repeat(len(ex_em_dict['Excitation'])), 
            wavenumbers=ex_em_dict['Emission']
        )


        fig.update_xaxes(nticks=10, title='Emission')
        fig.update_layout(legend_title_text="Samples",
                          title='', 
        )
        fig.update_yaxes(title='Intensity')
        return fig
    


    def get_2d_spectra_plotly_multiple(self, 
                    batch: Optional[str] = None, 
                    name: Optional[str] = None, 
                    index_loc: Optional[List[int]] = None, 
                    select_range: Optional[Tuple] = ([200, 800], [200, 800]), 
                    colorbar: Literal["individual", "hide"] = "individual"
                    ) -> go.Figure:
        
        if index_loc is not None:
            df = self.df.loc[index_loc]

        elif (batch is not None) and (name is not None): 
            df = self.df.loc[lambda x: (x.Batch == batch) & (x.Name == name)]
        
        else: 
            df = self.df

        try:
            data_stacked = np.stack(df.Data.to_numpy(), axis=0)
            ex_em_dict = self.df.iloc[0]['Metadata'].copy()
            del ex_em_dict['Date']
            
            rg_transform = RangeCutTransformer2D(select_range, 
                                                ex_em_dict,
                                                True)
            data_stacked = rg_transform.fit_transform(data_stacked)
            ex_em_dict['Emission'] = rg_transform.final_state['Emission']
            ex_em_dict['Excitation'] = rg_transform.final_state['Excitation']

        except ValueError:
            raise ValueError("Make sure the data is complete.")

        n_samples = df.shape[0]
        rows = math.ceil(n_samples/3)
        fig = make_subplots(rows=rows, cols=3, subplot_titles=df.Name.tolist(), 
                            horizontal_spacing=0.17)
        coloraxis = dict()
        colorscale= "Cividis"
        for i in range(n_samples):
            z_data = data_stacked[i]
            row, col = (i // 3) + 1, (i % 3) + 1 
            contour = go.Contour(
                z=z_data,
                x=ex_em_dict['Emission'],
                y=ex_em_dict['Excitation'],
                colorscale=colorscale, 
                colorbar=dict(title='Intensity'),
                showscale=False if colorbar=="hide" else True,
                coloraxis= None if colorbar=="hide" else f'coloraxis{i + 1}' 
            )

            fig.add_trace(contour, row=row, col=col)
        fig.update_xaxes(nticks=10, title_text='Emission')
        fig.update_yaxes(title_text='Excitation')
        fig.update_layout(
            title_text="",
            showlegend=False
        )
        if colorbar != "hide": 
            for i in range(n_samples): 
                if i == 0: 
                    coloraxis['coloraxis1'] = dict(colorscale=colorscale, 
                                            colorbar_x=fig._layout['xaxis']['domain'][1]+0.01, 
                                            colorbar_y=np.mean(fig._layout['yaxis']['domain'])+0.01, 
                                            colorbar_len=1/rows - 0.07)
                else: 
                    coloraxis[f"coloraxis{i+1}"] = dict(colorscale=colorscale,
                                                    colorbar_x=fig._layout[f"xaxis{i+1}"]['domain'][1]+0.01, 
                                                    colorbar_y=np.mean(fig._layout[f"yaxis{i+1}"]['domain'])+0.01, 
                                                    colorbar_len=1/rows - 0.07)

            fig.update_layout(**coloraxis)
        return fig
    

    @property
    def flattened_df(self): 
        return self.get_1d_dataframe()
    
    

    def get_1d_dataframe(self) -> pd.DataFrame: 
        """
        Returns dataframe for samples with complete data.. the columns are 
        Excitation/Emission pairs.
        """
        def concatenate_data(df): 
            emission, excitation = [self.df
                                    .loc[lambda x: x.is_complete].iloc[0]['Metadata'][key] 
                                    for key in ['Emission', 'Excitation']
                                    ]
            columns = [f"{ex}EX/{em}EM" 
                       for ex, em in product(excitation, emission)]
            
            return pd.concat([df.reset_index(drop=True), 
                            pd.DataFrame(data=self.to_numpy_array(one_dim=True), 
                                        columns=columns)], axis=1)
        
