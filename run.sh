#!/bin/bash

## Phase I: Generate coding questions
python3 prompting.py -output_json coding_questions_prompted -list_size 10 \
    -first_prompt "Please generate {list_size} unique and interesting coding questions that span a variety of topics." \
    -assistant_prompt "1. " 
python3 askgpt.py -input_json coding_questions_prompted -resume -temperature 0 -model gpt-3.5-turbo
python3 trim_response.py -input_json coding_questions_asked -trim_blanks
python3 split_response.py -input_json coding_questions_trimmed -new_key "question"

## Phase II: Generate GPT answers for the coding questions
first_prompt=$(cat <<'EOF'

## SYSTEM INSTRUCTION:
You are an AI assistant. User will you give you a task. Your goal is to complete the task as faithfully as you can. While performing the task think step-by-step and justify your steps.

## USER INSTRUCTION:
Here is a coding question: '{question}'. How would you solve it? Describe the process in step by step reasoning.
EOF
)

assistant_prompt=$(cat <<'EOF'
EOF
)
python3 prompting.py -input_json coding_questions_split -output_json coding_answers_prompted -list_size 10 -first_prompt "$first_prompt" -assistant_prompt "$assistant_prompt"
python3 askgpt.py -input_json coding_answers_prompted -resume -temperature 0 -model gpt-3.5-turbo -resume 
python3 trim_response.py -input_json coding_answers_asked -trim_blanks -trim_assistant_prompt

## Phase III: Create datasets
python3 formatting.py -input_json coding_answers_trimmed -format Alpaca
python3 formatting.py -input_json coding_answers_trimmed -format ShareGPT
python3 formatting.py -input_json coding_answers_trimmed -format Oasst