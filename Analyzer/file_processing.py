# %% File processing functions
import os
import pathlib
import re


def get_all_pdfs(folder_path: str) -> list[str]:
    return [os.path.join(dp, f) for dp, dn, filenames in os.walk(folder_path) for f in filenames if os.path.splitext(f)[1] == '.pdf']


def get_id_from_filepath(filepath: str) -> int:
    import pathlib
    import re
    candidate_id_str: str = re.split(r'[\s-]+', pathlib.Path(filepath).stem)[0]
    if str.isdigit(candidate_id_str):
        return int(candidate_id_str)

    return -1


def get_name_from_filepath(filepath: str) -> str:
    import pathlib
    distrinct = set([s for s in re.split(
        r'[^a-zA-Z]+', pathlib.Path(filepath).stem)])
    result = []
    words_to_exclude = ["cv", "resume", "curriculum", "vitae", "application", "cover", "letter", "science", "scientist", "research", "analyst", "engineer", "data", "msc", "degree"]
    for s in distrinct:
        if len(s) > 1 and s.lower() not in words_to_exclude:
            result.append(s.strip())

    return " ".join(result).strip()


def get_application_files(folder_path: str) -> dict[int, str]:
    all_files = get_all_pdfs(folder_path)
    res: dict[int, str] = {}
    for file in all_files:
        if "application" in file.lower():
            print(
                f"Found application for candidate {get_id_from_filepath(file)}")
            candidate_id = get_id_from_filepath(file)
            res[candidate_id] = file

    return res


def get_all_ids(folder_path: str) -> list[int]:
    import glob
    all_files = get_all_pdfs(folder_path)
    result: list[int] = []
    for file in all_files:
        result.append(get_id_from_filepath(file))

    result = list(set(result))
    return result


def get_pdfs_per_id(folder_path: str) -> dict[int, list[str]]:
    all_files = get_all_pdfs(folder_path)
    res: dict[int, list[str]] = {}
    for file in all_files:
        candidate_id = get_id_from_filepath(file)
        if candidate_id in res:
            res[candidate_id].append(file)
        else:
            res[candidate_id] = [file]
    return res