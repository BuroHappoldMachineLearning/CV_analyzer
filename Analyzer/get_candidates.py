# %%
from dataclasses import dataclass
import pathlib
import os
import re
import useful_texts

input_path: str = r"C:\Users\alombardi\Buro Happold\Design & Technology - R&D Wishlist\00488_Machine Learning reprise\Funding\InnovateUK\KTP project\Candidates\Candidates applications 26th january 2024"

all_files: list[str] = os.listdir(input_path)

# %%
ids: list[str] = list(set([re.split('[\s-]+', f)[0] for f in all_files]))
ids = [int(i) for i in ids if str.isdigit(i)]
ids.sort()
ids

# %%


def get_id_from_filepath(filepath: str) -> int:
    import pathlib
    candidate_id_str: str = re.split('[\s-]+', pathlib.Path(filepath).stem)[0]
    if str.isdigit(candidate_id_str):
        return int(candidate_id_str)


def get_name_from_filepath(filepath: str) -> str:
    import pathlib
    distrinct = set([s for s in re.split(
        r'[^a-zA-Z]+', pathlib.Path(filepath).stem)])
    result = []
    for s in distrinct:
        if (s.lower() != "cv" and s.lower() != "resume" and len(s) > 1):
            result.append(s)

    return " ".join(result)


# %%
get_id_from_filepath("C:\\temp\\122718-OGUNPOLA-1-ADEDAYO OGUNPOLA'S CV.pdf")

# %%a
get_name_from_filepath("C:\\temp\\122718-OGUNPOLA-1-ADEDAYO OGUNPOLA'S CV.pdf")

# %%


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
    filepath: str
    pages_text: dict[int, PageText]


def get_pdf_text(filepath: str,
                 tesseract_executable_path=r"C:\Users\alombardi\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
                 poppler_bin_path=r'C:\Users\alombardi\Desktop\Software\poppler-23.11.0\Library\bin'
                 ) -> PdfText:
    import PyPDF2
    import re
    import numpy as np
    import cv2
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r"C:\Users\alombardi\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
    import re
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
            pdf_text.pages_text[i] = PageText(i + 1, 100, text)

    if len(pdf_text.pages_text.keys()) < len(reader.pages):
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
            
            pdf_text.pages_text[i] = PageText(i + 1, page_conf, page_text)
        except Exception as e:
            from traceback import print_exc, print_tb
            print(
                f"Could not extract text from page {i} of pdf {pdf_file}. Error: {type(e).__name__} {e.args}")
            continue

    return pdf_text


# %%
root = r"C:\Users\alombardi\Buro Happold\Design & Technology - R&D Wishlist\00488_Machine Learning reprise\Funding\InnovateUK\KTP project\Candidates\Candidates applications 26th january 2024"
all_pdfs = list(str(s) for s in pathlib.Path(root).rglob("*.pdf"))


def print_pages_text(pages_text: PdfText):
    for page_text in pages_text.pages_text.values():
        print(f"Page {page_text.page_num}:\n{page_text.page_text}\n")


def get_text_and_print_pages_text(pdf_path: str):
    pages_text = get_pdf_text(pdf_path)
    print_pages_text(pages_text)


get_text_and_print_pages_text(all_pdfs[0])

# %%

for i in range(len(all_files)):
    file: str = all_files[i]
    candidate_id = get_id_from_filepath(file)

    if (not candidate_id):
        continue

    if "application" in file.lower():
        print(f"Found application for candidate {candidate_id}")

        if (i < len(all_files) - 1) and get_id_from_filepath(all_files[i + 1]) == candidate_id:
            candidate_name: str = get_name_from_filepath(all_files[i + 1])
            print(f"Found CV for candidate {candidate_name}")


# %%
