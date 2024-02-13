# %% Text processing functions

import re


def find_terms_in_text(text: str, terms_to_find: list[str] = ["pytorch", "tensorflow", "deep learning"]) -> set[str]:
    matches: set[str] = set()

    for term in terms_to_find:
        term = str.lower(term)
        res_search = re.search(term, str.lower(text))
        if res_search is not None:
            matches.add(res_search.string)

    return matches