from dataclasses import dataclass, field
import PyPDF2
import cv2
import pytesseract
from stopit import threading_timeoutable as timeoutable
import pathlib


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

    def get_all_text(self) -> str:
        return " ".join([page_text.page_text for page_text in self.text_per_page.values()])

    def print_pages_text(self) -> None:
        for page_text in self.text_per_page.values():
            print(f"Page {page_text.page_num}:\n{page_text.page_text}\n")


@timeoutable(30)
def read_pdf(filepath: str,
                 tesseract_executable_path=r"C:\Users\alombardi\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
                 poppler_bin_path=r'C:\Users\alombardi\Desktop\Software\poppler-23.11.0\Library\bin') -> PdfText:
    import PyPDF2
    import cv2
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = tesseract_executable_path
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