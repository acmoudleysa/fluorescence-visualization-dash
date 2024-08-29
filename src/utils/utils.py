import json 
import pathlib
from typing import Union, Any, Dict, TypedDict, List, Self
import numpy as np

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



    




    
