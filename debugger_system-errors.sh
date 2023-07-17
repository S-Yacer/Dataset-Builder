#!/bin/bash

## Phase I: Generate debugging prompts
first_prompt=$(cat <<'EOF'
## SYSTEM INSTRUCTION:
You are a dataset generator. You will be given context for what kind of data you want to generate. Your goal is to generate the dataset with the goal of it being used within a fine-tune.\n 

## USER INSTRUCTION:
I want you to generate a detailed example of a realistic programmatic debugging scenario that may occur in real-world, complex applications. This scenario should involve issues related to operating systems, system hardware, or system-level programming interfaces. The error should be one that can occur in the context of large scale system deployment, maintenance, or system-level application development. Please choose from a wide array of programming languages, but avoid common or simple errors. Instead, focus on issues that arise due to interactions with system-level APIs, hardware-specific dependencies, or operating system-level conflicts. You should also include an example of the terminal output that may be encountered during this issue, as well as one detailed example script that produces the error. This script should be a full and complex implementation, imitating realistic scenarios from real-world applications, and should be confined to a single file for debugging simplicity. This will be used as a user prompt feature where the user passes the request to our LLM for a debugging request, so we need it for a dataset that will be used to fine-tune a large language model to be a system debugging expert. Therefore, I expect you to follow a very strict output format where first you provide only an explanation of the error you are encountering, then you provide the code contents which may be a full implementation of a complex script as an example, remember it should be one file as the input for this dataset is just providing the file where the error originates from, and finally, you should provide a terminal output showing the full error message. It is imperative in your output you only generate what I specified and no solutions or explanation of a solution. It is also imperative your examples surround real-world system-level projects or applications, and not native/basic scripts nor native/regular/simple errors. Your answer should always indicate first the error nature as well as language in this format: '**Error Nature and Language:** The error is a 'error_type' in 'programming_language', before explaining the context.
EOF
)

assistant_prompt=$(cat <<'EOF'
**Error Nature and Language:**
EOF
)

python3 prompting.py -output_json debugging_prompted -first_prompt "$first_prompt" -assistant_prompt "$assistant_prompt"
python3 askgpt.py -input_json debugging_prompted -resume -temperature 0.7 -debugging_history -repeat_prompt 10 -model gpt-4
python3 trim_response.py -input_json debugging_asked -trim_blanks
python3 split_response.py -input_json debugging_trimmed -new_key "debugging_prompt"