import json
import os
import logging
from typing import Dict, List, Any

FILE_PATH = "institutions_and_departments.json"


def load_data() -> Dict[str, Any]:
    """
    Loads the JSON data from file. If the file doesn't exist,
    returns a default structure with an empty institution list.

    :return: Dictionary containing institutions and their departments
    """
    if not os.path.exists(FILE_PATH):
        return {"institutions": {}}

    with open(FILE_PATH, encoding="utf-8") as file:
        return json.load(file)


def save_data(data: Dict[str, Any]) -> None:
    """
    Saves the provided dictionary to the JSON file with pretty formatting.

    :param data: Dictionary to write to file
    """
    with open(FILE_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


async def add_institution(institution: str) -> None:
    """
    Adds an institution to the JSON file if it does not already exist

    :param institution: Name of the institution to add
    """
    data = load_data()

    if institution not in data['institutions']:
        data['institutions'][institution] = []
        save_data(data)
        logging.info(f"Institution added: {institution}")


async def add_department_to_institution(institution: str, department: str) -> None:
    """
    Adds a department to the specified institution, if it is not already listed

    :param institution: Name of the institution
    :param department: Name of the department to add
    """
    data = load_data()

    if institution not in data['institutions']:
        data['institutions'][institution] = []

    if department not in data['institutions'][institution]:
        data['institutions'][institution].append(department)
        save_data(data)
        logging.info(f"Department '{department}' added to {institution}")


async def get_institution_departments(institution: str) -> List[str]:
    """
    Retrieves the list of departments associated with the given institution

    :param institution: Institution name
    :return: List of department names
    """
    data = load_data()
    return data['institutions'].get(institution, [])
