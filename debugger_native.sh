#!/bin/bash

## Phase I: Generate debugging prompts
first_prompt=$(cat <<'EOF'
## SYSTEM INSTRUCTION:
You are a dataset generator. You will be given context for what kind of data you want to generate. Your goal is to generate the dataset with the goal of it being used within a fine-tune.\n 

## USER INSTRUCTION:
I want you to generate a detailed example of a realistic programmatic debugging scenario that may occur in beginner to intermediate level applications. This scenario should involve issues related to simple programming constructs or common libraries. The error should be one that can occur in the context of learning or developing simple applications. Please choose from a wide array of programming languages, but focus on common or simple errors that arise due to misuse of programming constructs, incorrect usage of libraries, or misunderstanding of language semantics. You should also include an example of the terminal output that may be encountered during this issue, as well as one detailed example script that produces the error. This script should be a simple implementation, imitating realistic scenarios from beginner-level projects, and should be confined to a single file for debugging simplicity. This will be used as a user prompt feature where the user passes the request to our LLM for a debugging request, so we need it for a dataset that will be used to fine-tune a large language model to be a beginner-level debugging expert. Therefore, I expect you to follow a very strict output format where first you provide only an explanation of the error you are encountering, then you provide the code contents which may be a basic script as an example, remember it should be one file as the input for this dataset is just providing the file where the error originates from, and finally, you should provide a terminal output showing the full error message. It is imperative in your output you only generate what I specified and the solution or explanation of the solution. Your answer should always indicate first the error nature as well as language in this format: '**Error Nature and Language:** The error is a 'error_type' in 'programming_language', before explaining the context.  Your examples should reflect the diversity and complexity of real-world software development. 
EOF
)

assistant_prompt=$(cat <<'EOF'
**Error Nature and Language:**
EOF
)

python3 prompting.py -output_json debugging_native_prompted -first_prompt "$first_prompt" -assistant_prompt "$assistant_prompt"
python3 threaded_askgpt.py -input_json debugging_native_prompted.json -output_json debugging_native_asked.json -resume -temperature 0.7 -debugging_history -max_threads 50 -num_responses 1500 -model gpt-4
python3 sort_response.py -input_json debugging_native_asked.json -output_json debugging_native_sorted.json 
python3 trim_response.py -input_json debugging_native_sorted.json -output_json debugging_native_trimmed.json -trim_blanks
python3 split_response.py -input_json debugging_native_trimmed.json -output_json debugging_native_split.json -new_key "debugging_prompt"