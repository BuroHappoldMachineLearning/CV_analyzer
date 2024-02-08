# %%
from stopit import threading_timeoutable as timeoutable
from collections import defaultdict
from dataclasses import dataclass, field
import pathlib
import os
import re
from typing import Optional, Union
import useful_texts


# %% File processing functions
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
    import pathlib
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


# %% Text processing functions

def find_terms_in_text(text: str, terms_to_find: list[str] = ["pytorch", "tensorflow", "deep learning"]) -> set[str]:
    matches: set[str] = set()

    for term in terms_to_find:
        term = str.lower(term)
        res_search = re.search(term, str.lower(text))
        if res_search is not None:
            matches.add(res_search.string)

    return matches


def count_buzzwords(text) -> int:
    buzzword_count = 0
    for buzzword in useful_texts.buzzwords:
        if buzzword in text.lower():
            buzzword_count += 1
    return buzzword_count

# %% Dataclasses


@dataclass
class PageText:
    """Contains the text of a page of a pdf file, as well as the page number and the confidence of the text extraction process.
    Args:
        page_num (int): Page number, starting from 1.
        page_confidence (float): Confidence in the text extraction, from 0 to 100.
        page_text (str): Text extracted from the page.
    """
    page_num: int
    page_confidence: float
    page_text: str


@dataclass
class PdfText:
    filepath: str = ""
    text_per_page: dict[int, PageText] = field(default_factory=lambda: {})

    def all_text(self) -> str:
        return " ".join([page_text.page_text for page_text in self.text_per_page.values()])


@dataclass
class CandidateApplication:
    candidate_id: int = 0
    fullname: Optional[str] = ""
    rating: Optional[float] = None
    application_filepath: str = ""
    cv_filepath: Optional[str] = ""
    answer1: Optional[str] = ""
    answer2: Optional[str] = ""
    answer3: Optional[str] = ""
    answer4: Optional[str] = ""
    answer5: Optional[str] = ""
    mentions_pytorch: bool = False
    mentions_tensorflow: bool = False
    mentions_csharp: bool = False
    mentions_computervision: bool = False
    mentions_azure: bool = False
    mentions_aws: bool = False
    buzzword_count: int = 0
    has_processing_errors: bool = False
    
    def set_nice_to_haves(self, text : str):
        self.mentions_pytorch |= "pytorch" in text.lower()
        self.mentions_tensorflow |= "tensorflow" in text.lower()
        self.mentions_csharp |= "c#" in text.lower()
        self.mentions_computervision |= "computer vision" in text.lower()
        self.mentions_azure |= "azure" in text.lower()
        self.mentions_aws |= "aws" in text.lower()
    
    def get_all_answers(self) -> list[str]:
        answers = [self.answer1, self.answer2, self.answer3, self.answer4, self.answer5]
        return [a for a in answers if a is not None]

    def set_rating(self):
        """Set the rating of the candidate application, based on the mentions of nice-to-have skills and the buzzword count.
        Necessary to correctly serialize dataclass, can't use @property decorator. Must be called before serializing.
        """
        if self.has_processing_errors:
            return

        self.rating = self.mentions_computervision + self.mentions_csharp / 2 + self.mentions_pytorch + self.mentions_tensorflow / 2
        self.rating += self.mentions_azure + self.mentions_aws / 1.1
        self.rating -= (self.buzzword_count / 1.75)
        
        for answer in self.get_all_answers():
            if len(answer) > 0 and len(answer) < 30:
                self.rating -= 1 # candidate attempted response but answer is very short. Sometimes indicates link to another document, which is invalid.
            elif len(answer) > 30 and len(answer) < 250:
                self.rating -= 0.5 # candidate attempted response but answer is too short.
            elif len(answer) > 1800:
                self.rating -= 0.5 # candidate provided a too long answer
        


# %% Text extraction functions


@timeoutable(30)
def get_pdf_text(filepath: str, 
                 tesseract_executable_path=r"C:\Users\alombardi\AppData\Local\Programs\Tesseract-OCR\tesseract.exe", 
                 poppler_bin_path=r'C:\Users\alombardi\Desktop\Software\poppler-23.11.0\Library\bin') -> PdfText:
    import PyPDF2
    import cv2
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = tesseract_executable_path
    import re
    import numpy as np
    from pdf2image import convert_from_bytes

    # create a df to save each pdf's text
    pdf_text = PdfText(filepath, {})

    # open the pdf file
    reader = PyPDF2.PdfReader(filepath)
    print(f"\tAttempting text extraction for file: {pathlib.Path(filepath).name}.")

    # extract text and do the search
    for (i, page) in enumerate(reader.pages):
        text = page.extract_text()
        all_words = text.split()
        words = [w for w in all_words if w.isalpha()]
        if len(words) > 50:
            pdf_text.text_per_page[i] = PageText(i + 1, 100, text)

    if len(pdf_text.text_per_page.keys()) < len(reader.pages):
        print(f"\t\tCould not directly extract text from all pages of pdf: {pathlib.Path(filepath).name}.")
    else:
        print(f"\tText extraction successful.")
        return pdf_text

    def get_conf(page_gray):
        '''return a average confidence value of OCR result '''
        df = pytesseract.image_to_data(page_gray, output_type='data.frame')
        df.drop(df[df.conf == -1].index.values, inplace=True)
        df.reset_index()
        return df.conf.mean()

    print("\t\tAttempting OCR text extraction.")
    # Convert pdf into image.
    # This requires to have Poppler installed -- check https://github.com/Belval/pdf2image?tab=readme-ov-file#how-to-install
    pdf_file = convert_from_bytes(open(filepath, 'rb').read(), poppler_path=poppler_bin_path)

    for (i, page) in enumerate(pdf_file):
        try:
            # transfer image of pdf_file into array
            page_arr = np.asarray(page)
            # transfer into grayscale
            page_arr_gray = cv2.cvtColor(page_arr, cv2.COLOR_BGR2GRAY)
            # get confidence value
            page_conf = get_conf(page_arr_gray)
            # extract text
            page_text = pytesseract.image_to_string(page_arr_gray)

            pdf_text.text_per_page[i] = PageText(i + 1, page_conf, page_text)
        except Exception as e:
            from traceback import print_exc, print_tb
            print(
                f"\tCould not extract text from page {i} of pdf {pathlib.Path(filepath).name}.Error:\n\t\t{type(e).__name__} {e.args}")
            continue

    print(f"\tText extraction successful.")

    return pdf_text


def get_answers_from_text(text: str) -> dict[int, str]:
    import useful_texts
    import re

    answers = {}
    # split the text into lines
    lines = text.split("\n")
    # find the first line that contains the word "answer"
    question_idx = 1
    for line_idx in range(len(lines)):
        line = lines[line_idx]
        if any(t in line for t in useful_texts.all_questions_initial_text):
            # get the answer text
            line_idx += 1
            line = lines[line_idx]
            answer_text = ""
            while any(line in t for t in useful_texts.all_questions):
                line_idx += 1
                line = lines[line_idx]

            while line_idx < len(lines) - 1:
                line = lines[line_idx]
                if any(t in line for t in useful_texts.all_questions_initial_text) or "Additional Information" in line:
                    break
                
                answer_text = " ".join([answer_text.rstrip(), line])
                line_idx += 1

            answers[question_idx] = answer_text.strip()
            question_idx += 1

    return answers


# %% Print functions

def print_pages_text(pages_text: PdfText):
    for page_text in pages_text.text_per_page.values():
        print(f"Page {page_text.page_num}:\n{page_text.page_text}\n")


def get_text_and_print_pages_text(pdf_path: str):
    pages_text = get_pdf_text(pdf_path)
    print_pages_text(pages_text)


# %%
def get_all_candidate_applications(folder_path: str) -> list[CandidateApplication]:
    pdfs_per_id = get_pdfs_per_id(folder_path)
    result_dict: defaultdict[int, CandidateApplication] = defaultdict(CandidateApplication)

    for candidate_id, pdfs_paths in pdfs_per_id.items():
        print(f"Candidate {candidate_id} has {len(pdfs_paths)} pdfs.")
        cand_app: CandidateApplication = result_dict[candidate_id]
        cand_app.candidate_id = candidate_id

        for pdf_path in pdfs_paths:
            filename : str = pathlib.Path(pdf_path).stem
            try:
                if "application" in filename.lower():
                    print(f"\tFound application for candidate {candidate_id}")
                    cand_app.application_filepath = pdf_path
                    application_text : PdfText = get_pdf_text(pdf_path)

                    if not application_text:
                        cand_app.has_processing_errors = True
                        continue
                    
                    all_application_text = application_text.all_text()
                    
                    # Set nice-to-have skills in the application
                    cand_app.set_nice_to_haves(all_application_text)
                    
                    # Check for buzzwords in the application
                    cand_app.buzzword_count += count_buzzwords(all_application_text)
                    
                    answers = get_answers_from_text(application_text.all_text())
                    if not answers:
                        cand_app.has_processing_errors = True
                        continue
                        
                    cand_app.answer1 = answers[1]
                    cand_app.answer2 = answers[2]
                    cand_app.answer3 = answers[3]
                    cand_app.answer4 = answers[4]
                    cand_app.answer5 = answers[5]
                    
                elif "cv" in filename.lower() or "resume" in filename.lower() or "curriculum" in filename.lower():
                    cand_app.cv_filepath = pdf_path
                    process_cv(cand_app)

            except Exception as e:
                print(f"Error processing file {pathlib.Path(pdf_path).name}. Error: {type(e).__name__} {e.args}")
                if (cand_app):
                    cand_app.has_processing_errors = True
                    

        # Final processing
        for c in result_dict.values():
            # If no CV was found, try searching with different terms.
            alternative_cv_terms = ["scientist", "research", "curriculum", "analyst", "engineer", "science"]
            if c.cv_filepath is None:
                possible_cv_files = [f for f in pdfs_per_id[c.candidate_id] if any(t for t in alternative_cv_terms if t in pathlib.Path(f).stem.lower())]
                if len(possible_cv_files) == 1:
                    c.cv_filepath = possible_cv_files[0]
                    try:
                        process_cv(cand_app)

                    except Exception as e:
                        print(f"Error processing file {pathlib.Path(c.cv_filepath).name}. Error: {type(e).__name__} {e.args}")
                        if (cand_app):
                            cand_app.has_processing_errors = True
                        continue
                    
            if c.cv_filepath == "" and c.application_filepath == "":
                print(f"Could not find application or CV for candidate {c.candidate_id}.")
                c.has_processing_errors = True
            
            c.set_rating() # necessary to serialize dataclass, can't use @property decorator.
    
    return list(result_dict.values())



def process_cv(cand_app : CandidateApplication):
    if cand_app.cv_filepath is None:
        return
    
    candidate_name: str = get_name_from_filepath(cand_app.cv_filepath)
    cand_app.fullname = candidate_name

    print(f"\tFound CV for candidate {cand_app.candidate_id}, whose name is {candidate_name}.")
    cv_text : PdfText = get_pdf_text(cand_app.cv_filepath)

    all_cv_text = cv_text.all_text()

    # Set nice-to-have skills from the cv
    cand_app.set_nice_to_haves(all_cv_text)

    # Check for buzzwords in the cv
    cand_app.buzzword_count += count_buzzwords(all_cv_text)


# %%
root = r"C:\Users\alombardi\Buro Happold\Design & Technology - R&D Wishlist\00488_Machine Learning reprise\Funding\InnovateUK\KTP project\Candidates\Candidates applications upto 5th February 2024"
#root = r"C:\Users\alombardi\Buro Happold\Design & Technology - R&D Wishlist\00488_Machine Learning reprise\Funding\InnovateUK\KTP project\Candidates\_subset"

all_candidate_apps: list[CandidateApplication] = get_all_candidate_applications(root)

i = 0
while True:
    filename = "_candidate_applications"
    filepath = f"{os.path.join(root, filename)}{i}.csv"
    try:
        with open(filepath, "w") as f:
            from dataclass_csv import DataclassWriter
            w = DataclassWriter(f, all_candidate_apps, CandidateApplication)
            w.write()

        print(f"File written successfully:\n\t{filepath}")
        break
    except Exception as e:
        i += 1
