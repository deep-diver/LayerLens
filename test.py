import gradio as gr

def main():
    with gr.Blocks() as demo:
        gr.HTML(open("requests_nla-pyvis.html", "r").read())
    demo.launch()

if __name__ == "__main__":
    main()