# My Business Card Website

This project provides two ways to generate a business card: a static HTML page and a dynamic generator using a Python backend.

## Features

- **Static Business Card:** A single HTML file (`index.html`) that can be customized and used directly.
- **Dynamic Business Card Generator:** A web form (`generator.html`) that allows you to enter your details and generate a business card.
- **FastAPI Backend:** The dynamic generator is powered by a FastAPI backend that handles form submissions and renders the business card template.

## Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/namecard.git
   cd namecard
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r rqms.txt
   ```

## Running the Application

To run the dynamic business card generator, start the FastAPI application using `uvicorn`:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8888
```

You can then access the generator by opening your web browser and navigating to `http://localhost:8888`.

## Usage

### Static Business Card

To use the static business card, simply open the `index.html` file in your web browser. You can customize the card by editing the HTML directly.

### Dynamic Business Card Generator

To use the dynamic generator, run the application as described above and open `http://localhost:8888` in your browser. Fill out the form with your details and click "Generate Card". A new tab will open with your customized business card.
