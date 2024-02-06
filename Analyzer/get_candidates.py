# %%
from dataclasses import dataclass, field
import pathlib
import os
import re
from typing import Optional
import useful_texts


# %%
def get_all_pdfs(folder_path: str) -> list[str]:
    return [os.path.join(dp, f) for dp, dn, filenames in os.walk(folder_path) for f in filenames if os.path.splitext(f)[1] == '.pdf']


def get_id_from_filepath(filepath: str) -> int:
    import pathlib
    import re
    candidate_id_str: str = re.split('[\s-]+', pathlib.Path(filepath).stem)[0]
    if str.isdigit(candidate_id_str):
        return int(candidate_id_str)
    
    
def get_application_files(folder_path: str) -> dict[int, str]:
    all_files = get_all_pdfs(folder_path)
    res : dict[int, str] = {}
    for file in all_files:
        if "application" in file.lower():
            print(f"Found application for candidate {get_id_from_filepath(file)}")
            candidate_id = get_id_from_filepath(file)
            res[candidate_id] = file
            
    return res


def get_all_ids(folder_path: str) -> list[int]:
    import pathlib
    import glob
    all_files = get_all_pdfs(folder_path)
    result : set[int] = set()
    for file in all_files:
        result.add(get_id_from_filepath(file))
        
    result = list(result)
    result.sort()
    return result


#%%

def get_name_from_filepath(filepath: str) -> str:
    import pathlib
    distrinct = set([s for s in re.split(
        r'[^a-zA-Z]+', pathlib.Path(filepath).stem)])
    result = []
    for s in distrinct:
        if (s.lower() != "cv" and s.lower() != "resume" and len(s) > 1):
            result.append(s)

    return " ".join(result)


def find_terms_in_text(text: str, terms_to_find: list[str] = ["pytorch", "tensorflow", "deep learning"]) -> set[str]:
    matches: set[str] = set()

    for term in terms_to_find:
        term = str.lower(term)
        res_search = re.search(term, str.lower(text))
        matches.add(res_search)

    return matches


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
class CandidateApplication(PdfText):
    candidate_id: int = 0
    candidate_fullname: str = ""
    candidate_application_filepath : str = ""
    candidate_cv_filepath : str = ""
    answer1: str = ""
    answer2: str = ""
    answer3: str = ""
    answer4: str = ""
    answer5: str = ""
    mentions_pytorch: bool = False
    mentions_tensorflow: bool = False
    mentions_csharp: bool = False
    mentions_computervision: bool = False
    buzzword_count : int = 0
    rating : float = False


def get_pdf_text(filepath: str, tesseract_executable_path=r"C:\Users\alombardi\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
                 poppler_bin_path=r'C:\Users\alombardi\Desktop\Software\poppler-23.11.0\Library\bin') -> PdfText:
    import PyPDF2
    import cv2
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r"C:\Users\alombardi\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
    import re
    import numpy as np
    from pdf2image import convert_from_bytes

    # create a df to save each pdf's text
    pdf_text = PdfText(filepath, {})

    # open the pdf file
    reader = PyPDF2.PdfReader(filepath)

    # extract text and do the search
    for (i, page) in enumerate(reader.pages):
        text = page.extract_text()
        all_words = text.split()
        words = [w for w in all_words if w.isalpha()]
        if len(words) > 50:
            pdf_text.text_per_page[i] = PageText(i + 1, 100, text)

    if len(pdf_text.text_per_page.keys()) < len(reader.pages):
        print(
            f"Could not directly extract text from all pages of pdf:\n\t{filepath}.")
    else:
        return pdf_text

    def get_conf(page_gray):
        '''return a average confidence value of OCR result '''
        df = pytesseract.image_to_data(page_gray, output_type='data.frame')
        df.drop(df[df.conf == -1].index.values, inplace=True)
        df.reset_index()
        return df.conf.mean()

    print("Attempting OCR text extraction.")
    # Convert pdf into image.
    # This requires to have Poppler installed -- check https://github.com/Belval/pdf2image?tab=readme-ov-file#how-to-install
    pdf_file = convert_from_bytes(
        open(filepath, 'rb').read(), poppler_path=poppler_bin_path)

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
                f"Could not extract text from page {i} of pdf {pdf_file}. Error: {type(e).__name__} {e.args}")
            continue

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
                
            while (not any(line in t for t in useful_texts.all_questions)) and "additional information" not in line.lower():
                line = lines[line_idx]
                answer_text = " ".join([answer_text.rstrip(), line])
                line_idx += 1
                
                if re.search("Additional Information", line):
                    break
                 
            answers[question_idx] = answer_text.strip()
            question_idx += 1

    return answers



# %%

def print_pages_text(pages_text: PdfText):
    for page_text in pages_text.text_per_page.values():
        print(f"Page {page_text.page_num}:\n{page_text.page_text}\n")


def get_text_and_print_pages_text(pdf_path: str):
    pages_text = get_pdf_text(pdf_path)
    print_pages_text(pages_text)

           

# %%
def get_all_candidate_applications(folder_path: str) -> list[CandidateApplication]:
    all_files = get_all_pdfs(folder_path)
    result : list[CandidateApplication] = []
    
    for i in range(len(all_files)):
        file: str = all_files[i]
        candidate_id = get_id_from_filepath(file)

        if (not candidate_id):
            continue

        if "application" in file.lower():
            print(f"Found application for candidate {candidate_id}")
            cand_app = CandidateApplication(candidate_id=candidate_id)
            cand_app.filepath = file
            candidate_id = get_id_from_filepath(file)
            application_text = get_pdf_text(file)
            
            if application_text:
                answers = get_answers_from_text(application_text.all_text())
                if answers:
                    cand_app.answer1 = answers[1]
                    cand_app.answer2 = answers[2]
                    cand_app.answer3 = answers[3]
                    cand_app.answer4 = answers[4]
                    cand_app.answer5 = answers[5]
                
                all_application_text = application_text.all_text()
                
                # Check for nice-to-have skills in the application
                cand_app.mentions_pytorch = "pytorch" in all_application_text.lower()
                cand_app.mentions_tensorflow = "tensorflow" in all_application_text.lower()
                cand_app.mentions_csharp = "c#" in all_application_text.lower()
                cand_app.mentions_computervision = "computer vision" in all_application_text.lower()
                
                # Check for buzzwords in the application
                for buzzword in useful_texts.buzzwords:
                    if buzzword in all_application_text.lower():
                        cand_app.buzzword_count += 1
            
            possible_cv_file = all_files[i + 1]
            if (i < len(all_files) - 1) and get_id_from_filepath(possible_cv_file) == candidate_id:
                candidate_name: str = get_name_from_filepath(possible_cv_file)
                candidate_name = candidate_name.strip()
                cand_app.candidate_fullname = candidate_name
                
                print(f"Found CV for candidate {candidate_name}")
                cv_text = get_pdf_text(possible_cv_file)
                
                all_cv_text = cv_text.all_text()
                
                # Check for nice-to-have skills in the cv
                cand_app.mentions_pytorch |= "pytorch" in all_cv_text.lower()
                cand_app.mentions_tensorflow |= "tensorflow" in all_cv_text.lower()
                cand_app.mentions_csharp |= "c#" in all_cv_text.lower()
                cand_app.mentions_computervision |= "computer vision" in all_cv_text.lower()
                
                # Check for buzzwords in the cv
                for buzzword in useful_texts.buzzwords:
                    if buzzword in all_cv_text.lower():
                        cand_app.buzzword_count += 1

            cand_app.rating = cand_app.mentions_pytorch + cand_app.mentions_tensorflow + cand_app.mentions_csharp + cand_app.mentions_computervision
            cand_app.rating -= cand_app.buzzword_count
            result.append(cand_app)
            
    return result
            

# %%
root = r"C:\Users\alombardi\Buro Happold\Design & Technology - R&D Wishlist\00488_Machine Learning reprise\Funding\InnovateUK\KTP project\Candidates\Candidates applications 26th january 2024"
root = r"C:\Users\alombardi\Buro Happold\Design & Technology - R&D Wishlist\00488_Machine Learning reprise\Funding\InnovateUK\KTP project\Candidates\_subset"

all_candidate_apps : list[CandidateApplication] = get_all_candidate_applications(root)

with open("candidate_applications.csv", "w") as f:
    from dataclass_csv import DataclassWriter
    w = DataclassWriter(f, all_candidate_apps, CandidateApplication)
    w.write()