# %%
from collections import defaultdict
from dataclasses import dataclass
import pathlib
import os
from typing import Optional

from rich.progress import track
from file_processing import get_name_from_filepath
from pdf_processing import PdfText, read_pdf
from text_processing import get_answers_from_text
from text_processing import count_buzzwords
from file_processing import get_pdfs_per_id


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
        text_lower = text.lower()

        self.mentions_pytorch |= "pytorch" in text_lower
        self.mentions_tensorflow |= "tensorflow" in text_lower
        self.mentions_csharp |= "c#" in text_lower
        self.mentions_computervision |= "computer vision" in text_lower
        self.mentions_azure |= "azure" in text_lower
        self.mentions_aws |= "aws" in text_lower

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

    def set_data_from_cv(self, cv_filepath : str):
        if self is None or cv_filepath is None:
            return

        self.cv_filepath = cv_filepath

        candidate_name: str = get_name_from_filepath(self.cv_filepath)
        self.fullname = candidate_name

        print(f"\tFound CV for candidate {self.candidate_id}, whose name is {candidate_name}.")
        cv_text : PdfText = read_pdf(self.cv_filepath)

        all_cv_text = cv_text.get_all_text()

        # Set nice-to-have skills from the cv
        self.set_nice_to_haves(all_cv_text)

        # Check for buzzwords in the cv
        self.buzzword_count += count_buzzwords(all_cv_text)


# %%
def get_all_candidate_applications(folder_path: str) -> list[CandidateApplication]:
    pdfs_per_id = get_pdfs_per_id(folder_path)
    print(f"Found {len(pdfs_per_id)} candidates with applications.")
    
    result_dict: defaultdict[int, CandidateApplication] = defaultdict(CandidateApplication)

    for candidate_id, pdfs_paths in track(pdfs_per_id.items()):
        print(f"Candidate {candidate_id} has {len(pdfs_paths)} pdfs.")
        cand_app: CandidateApplication = result_dict[candidate_id]
        cand_app.candidate_id = candidate_id

        for pdf_path in pdfs_paths:
            filename : str = pathlib.Path(pdf_path).stem
            try:
                if "application" in filename.lower():
                    print(f"\tFound application for candidate {candidate_id}")
                    cand_app.application_filepath = pdf_path
                    application_text : PdfText = read_pdf(pdf_path)

                    if not application_text:
                        cand_app.has_processing_errors = True
                        continue
                    
                    all_application_text = application_text.get_all_text()
                    
                    # Set nice-to-have skills in the application
                    cand_app.set_nice_to_haves(all_application_text)
                    
                    # Check for buzzwords in the application
                    cand_app.buzzword_count += count_buzzwords(all_application_text)
                    
                    answers = get_answers_from_text(application_text.get_all_text())
                    if not answers:
                        cand_app.has_processing_errors = True
                        continue
                        
                    cand_app.answer1 = answers[1]
                    cand_app.answer2 = answers[2]
                    cand_app.answer3 = answers[3]
                    cand_app.answer4 = answers[4]
                    cand_app.answer5 = answers[5]
                    
                elif "cv" in filename.lower() or "resume" in filename.lower() or "curriculum" in filename.lower():
                    cand_app.set_data_from_cv(pdf_path)

            except Exception as e:
                print(f"Error processing file {pathlib.Path(pdf_path).name}. Error: {type(e).__name__} {e.args}")
                if (cand_app):
                    cand_app.has_processing_errors = True
                    

        # Final processing
        for cand_app in result_dict.values():
            # If no CV was found, try searching with different terms.
            alternative_cv_terms = ["scientist", "research", "curriculum", "analyst", "engineer", "science"]
            if cand_app.cv_filepath is None:
                possible_cv_files = [f for f in pdfs_per_id[cand_app.candidate_id] if any(t for t in alternative_cv_terms if t in pathlib.Path(f).stem.lower())]
                if len(possible_cv_files) == 1:
                    try:
                        cand_app.set_data_from_cv(possible_cv_files[0])

                    except Exception as e:
                        print(f"Error processing file {pathlib.Path(possible_cv_files[0]).name}. Error: {type(e).__name__} {e.args}")
                        if (cand_app):
                            cand_app.has_processing_errors = True
                        continue
                    
            if cand_app.cv_filepath == "" and cand_app.application_filepath == "":
                print(f"Could not find application or CV for candidate {cand_app.candidate_id}.")
                cand_app.has_processing_errors = True
            
            cand_app.set_rating() # necessary to serialize dataclass, can't use @property decorator.
    
    print(f"Processed {len(result_dict)} candidate applications.")
    return list(result_dict.values())



# %%

if __name__ == "__main__":
    root = r"C:\Users\alombardi\Buro Happold\Design & Technology - R&D Wishlist\00488_Machine Learning reprise\Funding\InnovateUK\KTP project\Candidates\Upto 20240211 closing date"
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
