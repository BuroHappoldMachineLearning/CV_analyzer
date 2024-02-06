# Questions text
question1 = "1. Please briefly illustrate the nature and scope of your previous experiences and interests, explaining relevant connections to this role (50-150 words) (essential to the job)"
question2 = "2. Please illustrate the reasons why you would like to work in this position and industry, including your personal ambitions for the future (50-150 words) (essential to the job)"
question3 = "3. Describe what algorithmic complexity is. (50-150 words) - Feel free to make examples, including your own experience if relevant. (essential to the job)"
question4 = "4. Please explain what \"Variable scoping\" is, making an example of how it works in one or more programming languages that you know, possibly including Python. (50-150 words) (essential to the job)"
question5 = "5. Please describe what overfitting means in data science/ML. (50-150 words) (essential to the job)"

all_questions = [question1, question2, question3, question4, question5]
all_questions_initial_text = [q[5:20] for q in all_questions]

# Quality-indicative terms
ai_terms : list[str] = ["paramount", "crucial", "essential", "critical", "vital", "indispensable", "integral", "imperative", "ensuring"]
buzzwords: list[str] = ["cutting-edge", "state-of-the-art", "innovative", "revolutionary", "pioneering", "groundbreaking", "leading-edge", "sophisticated", "high-tech", "high-end", "high-quality", "high-performance", "high-impact", "high-value", "high-level", "high-precision"]
