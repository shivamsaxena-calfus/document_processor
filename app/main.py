from fastapi import FastAPI, UploadFile, File, HTTPException, Query
import google.generativeai as genai
import pathlib
import tqdm
import subprocess
import logging


app = FastAPI()

# Configure the Google Gemini API
genai.configure(api_key="GOOGLE_API_KEY")



@app.post("/summarize")
async def summarize_pdf(
    file: UploadFile = File(...),
    first: int = Query(..., description="First page number to summarize"),
    last: int = Query(..., description="Last page number to summarize")
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF file.")

    # Save the uploaded PDF file
    file_path = pathlib.Path('uploaded_test.pdf')
    with file_path.open("wb") as f:
        f.write(file.file.read())

    # Create directories for extractions if they don't exist
    pdf_extractions_dir = pathlib.Path("pdf_extractions")
    images_dir = pdf_extractions_dir / "images"
    pdf_extractions_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    # Convert PDF pages to images
    subprocess.run(["pdftoppm", str(file_path), "-f", str(first), "-l", str(last), str(images_dir / "images"), "-jpeg"], check=True)

    # Extract text from PDF pages
    for page_number in range(first, last + 1):
        page_number_str = f"{page_number:03d}"
        subprocess.run(["pdftotext", str(file_path), "-f", str(page_number), "-l", str(page_number)], check=True)
        subprocess.run(["mv", "uploaded_test.txt", str(pdf_extractions_dir / f"text-{page_number_str}.txt")], check=True)

    # Upload images to Google Gemini API
    files = []
    image_files = list(images_dir.glob('images-*.jpg'))
    for img in tqdm.tqdm(image_files):
        files.append(genai.upload_file(img))

    # Read the extracted text files
    texts = [t.read_text() for t in pdf_extractions_dir.glob('text-*.txt')]

    # Prepare the textbook content
    textbook = []
    for page, (text, image) in enumerate(zip(texts, files)):
        textbook.append(f'## Page {first + page} ##')
        textbook.append(text)
        textbook.append(image)

    # Initialize the Google Gemini Generative Model
    model = genai.GenerativeModel(model_name='gemini-1.5-flash')

    # Generate the summary
    response = model.generate_content(
        ['# Here is a chapter from a Scala textbook:'] +
        textbook +
        ["[END]\n\nPlease summarize it in sections for a better understanding with appropriate code snippets, and examples from the chapter itself"]
    )

    # Print response to console
    logging.info(response)

    # Save response to a text file
    response_file_path = pdf_extractions_dir / "response.txt"
    with response_file_path.open("w") as f:
        f.write(str(response))

    # Return response file path
    return {"message": "Response saved to file", "file_path": str(response_file_path)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=6002)

