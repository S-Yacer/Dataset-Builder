#!/bin/bash

## Phase I: Generate debugging prompts
first_prompt=$(cat <<'EOF'
## SYSTEM INSTRUCTION:
You are a dataset generator. You will be given context for what kind of data you want to generate. Your goal is to generate the dataset with the goal of it being used within a fine-tune.\n 

## USER INSTRUCTION:
I want you to generate a detailed example of a realistic programmatic debugging scenario that may occur in real-world, complex applications. The scenario should involve intricate systems and interactions typically seen in professional software development. You should choose from a wide array of programming languages, avoiding basic or regular errors, and instead focusing on errors that may occur from using third-party libraries or frameworks, with an example of a terminal output that you may encounter during this, and one example script where the error occurs from, this script must be fully detailed and a full implementation, mimicking realistic scenarios from real-world applications, this must only be one script that you are debugging.  This will be used as a user prompt feature where the user passes the request to our LLM for a debugging request, so we need it for a dataset that will be used to fine-tune a large language model to be a debugging expert, therefore I expect you to follow a very strict output format where first you provide only an explanation of the error you are encountering, then you provide the code contents which may be a full implementation of a complex script as an example, remember it should be one file as the input for this dataset is just providing the file where the error originates from, and finally you should provide a terminal output showing the full error message. It is imperative in your output you only generate what I specified and no solutions or explanation of a solution. It is also imperative your examples surround real-world projects or real-world applications, and not native/basic scripts nor native/regular/simple errors. Your answer should always indicate first the error nature as well as language in this format: '**Error Nature and Language:** The error is a 'error_type' in 'programming_language', before explaining the context.  Your examples should reflect the diversity and complexity of real-world software development. Also, do not repeat a combination of languages and error types that has already been generated. The goal is to create a diverse dataset of different languages and error types. Lastly, it is important you do not repeat a combo of languages and error types that has already been generated, here are the following existing language and error type combinations that you must not generate within your example, but you are at will to generate a different combination pair:
EOF
)

assistant_prompt=$(cat <<'EOF'
EOF
)

python3 prompting.py -output_json debugging_prompted -first_prompt "$first_prompt" -assistant_prompt "$assistant_prompt"
python3 askgpt.py -input_json debugging_prompted -resume -temperature 0.7 -top_p 0.5 -debugging_history -repeat_prompt 10 -model gpt-4
python3 trim_response.py -input_json debugging_asked -trim_blanks
python3 split_response.py -input_json debugging_trimmed -new_key "debugging_prompt"