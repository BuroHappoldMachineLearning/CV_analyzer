import requests

sentence     = "All children, except one, grow up. They soon know that they will grow up, and the way Wendy knew was this. One day when she was two years old she was playing in a garden, and she plucked another flower and ran with it to her mother. I suppose she must have looked rather delightful, for Mrs. Darling put her hand to her heart and cried, “Oh, why can’t you remain like this for ever!” This was all that passed between them on the subject, but henceforth Wendy knew that she must grow up. You always know after you are two. Two is the beginning of the end. Of course they lived at 14, and until Wendy came her mother was the chief one. She was a lovely lady, with a romantic mind and such a sweet mocking mouth. Her romantic mind was like the tiny boxes, one within the other, that come from the puzzling East, however many you discover there is always one more; and her sweet mocking mouth had one kiss on it that Wendy could never get, though there it was, perfectly conspicuous in the right-hand corner. The way Mr. Darling won her was this: the many gentlemen who had been boys when she was a girl discovered simultaneously that they loved her, and they all ran to her house to propose to her except Mr. Darling, who took a cab and nipped in first, and so he got her. He got all of her, except the innermost box and the kiss. He never knew about the box, and in time he gave up trying for the kiss. Wendy thought Napoleon could have got it, but I can picture him trying, and then going off in a passion, slamming the door. Mr. Darling used to boast to Wendy that her mother not only loved him but respected him. He was one of those deep ones who know about stocks and shares. Of course no one really knows, but he quite seemed to know, and he often said stocks were up and shares were down in a way that would have made any woman respect him."
bearer_token = 'Bearer sess-rHIIrS3jr16B6JOmqlssov9r38jTfMTHd1Lx1h3l' # see https://medium.com/@mugglestudent/how-to-get-the-openai-session-token-87c93df4a563
bearer_token = "Bearer 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"

header = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
    'Authorization': bearer_token,
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'https://platform.openai.com',
    'Referer': 'https://platform.openai.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}

data = {
    'prompt': sentence + "».\n<|disc_score|>",
    'max_tokens': 1,
    'temperature': 1,
    'top_p': 1,
    'n': 1,
    'logprobs': 5,
    'stop': '\n',
    'stream': False,
    'model': 'gpt-3.5-turbo-0125',
}

response = requests.post('https://api.openai.com/v1/completions', headers=header, json=data)

print(response)           