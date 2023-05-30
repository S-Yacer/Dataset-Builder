import torch
from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer


app = Flask(__name__)

tokenizer = AutoTokenizer.from_pretrained('mosaicml/mpt-7b')
model_1 = AutoModelForCausalLM.from_pretrained('mosaicml/mpt-7b', torch_dtype=torch.bfloat16, trust_remote_code=True)
model_2 = AutoModelForCausalLM.from_pretrained('mosaicml/mpt-7b-chat', torch_dtype=torch.bfloat16, trust_remote_code=True)


def generate_response(tokenizer, model, input_text):
    input_tokens = tokenizer.encode(input_text, return_tensors="pt")
    output_tokens = model.generate(input_tokens, max_length=50, pad_token_id=tokenizer.eos_token_id)
    output_text = tokenizer.decode(output_tokens[:, input_tokens.shape[-1]:][0], skip_special_tokens=True)
    return output_text


@app.route("http://127.0.0.1:5000/generate-responses", methods=["POST"])
def process_request():
    input_text = request.json.get("input_text")
    response_model_1 = generate_response(tokenizer, model_1, input_text)
    response_model_2 = generate_response(tokenizer, model_2, input_text)

    return jsonify({"model_1": response_model_1, "model_2": response_model_2})


if __name__ == "__main__":
    app.run()