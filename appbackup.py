from flask import Flask, render_template, request
from google import genai
from dotenv import load_dotenv
import os
import markdown

from PIL import Image
from pypdf import PdfReader


load_dotenv()


app = Flask(__name__)


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)



def generate_ai_response(contents):

    models = [
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash"
    ]


    for model in models:

        try:

            response = client.models.generate_content(
                model=model,
                contents=contents
            )

            return response.text


        except Exception as e:

            print(
                f"{model} failed:",
                e
            )


    return """
## BridgeAI is temporarily unavailable

The AI service is currently experiencing high traffic.

Please try again in a few moments.
"""




@app.route("/")
def landing():

    return render_template(
        "landing.html"
    )




@app.route("/app", methods=["GET", "POST"])
def home():


    result = ""



    if request.method == "POST":


        text = request.form.get(
            "text",
            ""
        )


        audience = request.form.get(
            "audience",
            "General public"
        )


        uploaded_file = request.files.get(
            "file"
        )


        content = ""



        # TEXT INPUT

        if text.strip():

            content += text





        # FILE INPUT

        if uploaded_file and uploaded_file.filename:


            filename = uploaded_file.filename.lower()



            # PDF

            if filename.endswith(".pdf"):


                reader = PdfReader(
                    uploaded_file
                )


                pdf_text = ""


                for page in reader.pages:

                    pdf_text += (
                        page.extract_text()
                        or ""
                    )


                content += "\n\n" + pdf_text





            # IMAGE

            elif filename.endswith(
                (
                    ".png",
                    ".jpg",
                    ".jpeg"
                )
            ):


                image = Image.open(
                    uploaded_file
                )



                prompt = f"""

You are BridgeAI, an accessibility assistant.

Analyze this document image.

Audience:
{audience}


Provide:

## Simple Explanation

## Key Points

## Important Actions

"""



                ai_text = generate_ai_response(
                    [
                        prompt,
                        image
                    ]
                )



                result = markdown.markdown(
                    ai_text
                )


                return render_template(
                    "index.html",
                    result=result
                )





        if not content.strip():


            result = """
<p>Please upload a PDF, image, or paste text first.</p>
"""



        else:



            prompt = f"""

You are BridgeAI, an accessibility assistant.

Simplify the information below.

Audience:
{audience}


Give:

## Simple Explanation

Explain it clearly.

## Key Points

Important information.

## Important Actions

What the user should do.


Information:

{content}

"""



            ai_text = generate_ai_response(
                prompt
            )


            result = markdown.markdown(
                ai_text
            )




    return render_template(
        "index.html",
        result=result
    )





if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=True
    )