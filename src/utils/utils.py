import json 
import pathlib
from typing import Union, Any, Dict

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


    




    
