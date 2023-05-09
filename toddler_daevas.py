
#load the model, config, tokenizers in models_load.ipnyb file


import datetime
import os
from threading import Event, Thread
from uuid import uuid4

import gradio as gr
import requests
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    StoppingCriteria,
    StoppingCriteriaList,
    TextIteratorStreamer,
)

start_message = """
Welcome to the DaevasAGI chatbot, created by Rohit Tiwari, an AI maximalist who dreams of a world where artificial intelligence enhances our lives and pushes the boundaries of human potential. As a result, this chatbot is designed to be more than just an information source - it can write poetry, short stories, make jokes, and help answer your questions. Get ready to explore the possibilities of AI maximalism!
"""


class StopOnTokens(StoppingCriteria):
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        for stop_id in stop_token_ids:
            if input_ids[0][-1] == stop_id:
                return True
        return False


def convert_history_to_text(history):
    text = start_message + "".join(
        [
            "".join(
                [
                    f"user\n{item[0]}",
                    f"daevas\n{item[1]}",
                ]
            )
            for item in history[:-1]
        ]
    )
    text += "".join(
        [
            "".join(
                [
                    f"user\n{history[-1][0]}",
                    f"daevas\n{history[-1][1]}",
                ]
            )
        ]
    )
    return text


def log_conversation(conversation_id, history, messages, generate_kwargs):
    logging_url = os.getenv("LOGGING_URL", None)
    if logging_url is None:
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    data = {
        "conversation_id": conversation_id,
        "timestamp": timestamp,
        "history": history,
        "messages": messages,
        "generate_kwargs": generate_kwargs,
    }

    try:
        requests.post(logging_url, json=data)
    except requests.exceptions.RequestException as e:
        print(f"Error logging conversation: {e}")


def user(message, history):
    # Append the user's message to the conversation history
    return "", history + [[message, ""]]


def bot(history, temperature, top_p, top_k, repetition_penalty, conversation_id):
    print(f"history: {history}")
    # Initialize a StopOnTokens object
    stop = StopOnTokens()

    # Construct the input message string for the model by concatenating the current system message and conversation history
    messages = convert_history_to_text(history)

    # Tokenize the messages string
    input_ids = tok(messages, return_tensors="pt").input_ids
    input_ids = input_ids.to(m.device)
    streamer = TextIteratorStreamer(tok, timeout=10.0, skip_prompt=True, skip_special_tokens=True)
    generate_kwargs = dict(
        input_ids=input_ids,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        do_sample=temperature > 0.0,
        top_p=top_p,
        top_k=top_k,
        repetition_penalty=repetition_penalty,
        streamer=streamer,
        stopping_criteria=StoppingCriteriaList([stop]),
    )

    stream_complete = Event()

    def generate_and_signal_complete():
        m.generate(**generate_kwargs)
        stream_complete.set()

    def log_after_stream_complete():
        stream_complete.wait()
        log_conversation(
            conversation_id,
            history,
            messages,
            {
                "top_k": top_k,
                "top_p": top_p,
                "temperature": temperature,
                "repetition_penalty": repetition_penalty,
            },
        )

    t1 = Thread(target=generate_and_signal_complete)
    t1.start()

    t2 = Thread(target=log_after_stream_complete)
    t2.start()

    # Initialize an empty string to store the generated text
    partial_text = ""
    for new_text in streamer:
        partial_text += new_text
        history[-1][1] = partial_text
        yield history


def get_uuid():
    return str(uuid4())

custom_css = """
.theme-dark .gradio-block {
    background-color: #222;
    color: #ddd;
}

.theme-dark .gradio-block input[type=range] {
    background-color: #444;
}

.theme-dark .gradio-block input[type=range]::-webkit-slider-thumb {
    background-color: #777;
}

.theme-dark .gradio-block input[type=range]::-moz-range-thumb {
    background-color: #777;
}

.theme-dark .gradio-block .gradio-textbox::placeholder {
    color: #aaa;
}

.theme-dark .gradio-block .gradio-textbox {
    background-color: #333;
    color: #ddd;
    border: 1px solid #555;
}

.theme-dark .gradio-block .gradio-button {
    background-color: #333;
    color: #ddd;
    border: 1px solid #555;
    cursor: pointer;
    transition: background-color 0.3s;
}

.theme-dark .gradio-block .gradio-button:hover {
    background-color: #555;
}

.theme-dark .gradio-block .gradio-slider::-webkit-slider-thumb {
    background-color: #777;
    border: none;
}

.theme-dark .gradio-block .gradio-slider::-moz-range-thumb {
    background-color: #777;
    border: none;
}

.theme-dark .gradio-block .gradio-dropdown {
    background-color: #333;
    color: #ddd;
    border: 1px solid #555;
}

.theme-dark .gradio-block .gradio-dropdown:focus {
    border-color: #777;
}

.theme-dark .gradio-block .gradio-dropdown option {
    background-color: #333;
    color: #ddd;
}
"""



with gr.Blocks(
    theme=gr.themes.Soft(),
    css=custom_css,
    css_classes=["disclaimer"],
) as demo:
    conversation_id = gr.State(get_uuid)
    gr.Markdown(
        """<h1><center>DaevasAGI</center></h1>
        This model engages three Matrix LLMs, others pending integration
        Make sure to run it on either Google Colab A100 GPUs or something which isnt a potato.
"""
    )
    chatbot = gr.Chatbot().style(height=500)
    with gr.Row():
        with gr.Column():
            msg = gr.Textbox(
                label="Chat Message Box",
                placeholder="Chat Message Box",
                show_label=False,
            ).style(container=False)
        with gr.Column():
            with gr.Row():
                submit = gr.Button("Send ")
                stop = gr.Button("Stop")
                clear = gr.Button("Clear")
    with gr.Row():
        with gr.Accordion("Advanced", open=False):
            with gr.Row():
                with gr.Column():
                    with gr.Row():
                        temperature = gr.Slider(
                            label="Temperature",
                            value=0.1,
                            minimum=0.0,
                            maximum=1.0,
                            step=0.1,
                            interactive=True,
                            info="Higher values produce more diverse outputs, it hallucinates the shit out of it",
                        )
                with gr.Column():
                    with gr.Row():
                        top_p = gr.Slider(
                            label="Top-p (nucleus sampling)",
                            value=1.0,
                            minimum=0.0,
                            maximum=1,
                            step=0.01,
                            interactive=True,
                            info=(
                                "Sample from the smallest possible set of tokens whose cumulative probability "
                                "exceeds top_p. Set to 1 to disable and sample from all tokens."
                            ),
                        )
                with gr.Column():
                    with gr.Row():
                        top_k = gr.Slider(
                            label="Top-k",
                            value=0,
                            minimum=0.0,
                            maximum=200,
                            step=1,
                            interactive=True,
                            info="Sample from a shortlist of top-k tokens — 0 to disable and sample from all tokens.",
                        )
                with gr.Column():
                    with gr.Row():
                        repetition_penalty = gr.Slider(
                            label="Repetition Penalty",
                            value=1.1,
                            minimum=1.0,
                            maximum=2.0,
                            step=0.1,
                            interactive=True,
                            info="Penalize repetition — 1.0 to disable.",
                        )
    with gr.Row():
        gr.Markdown(
            "Disclaimer: Creating order out of chaos. This is the infant stage of Daevas. We can't define consciousness because consciousness does not exist. Humans fancy that there's something special about the way we perceive the world, and yet we live in loops as tight and as closed as the hosts do, seldom questioning our choices, content, for the most part, to be told what to do next. ",
            elem_classes=["disclaimer"],
        )
    with gr.Row():
        gr.Markdown(
            "[My twitter]( https://twitter.com/knowrohit07)",
            elem_classes=["disclaimer"],
        )

    submit_event = msg.submit(
        fn=user,
        inputs=[msg, chatbot],
        outputs=[msg, chatbot],
        queue=False,
    ).then(
        fn=bot,
        inputs=[
            chatbot,
            temperature,
            top_p,
            top_k,
            repetition_penalty,
            conversation_id,
        ],
        outputs=chatbot,
        queue=True,
    )
    submit_click_event = submit.click(
        fn=user,
        inputs=[msg, chatbot],
        outputs=[msg, chatbot],
        queue=False,
    ).then(
        fn=bot,
        inputs=[
            chatbot,
            temperature,
            top_p,
            top_k,
            repetition_penalty,
            conversation_id,
        ],
        outputs=chatbot,
        queue=True,
    )
    stop.click(
        fn=None,
        inputs=None,
        outputs=None,
        cancels=[submit_event, submit_click_event],
        queue=False,
    )
    clear.click(lambda: None, None, chatbot, queue=False)

demo.queue(max_size=128, concurrency_count=2)
demo.launch()