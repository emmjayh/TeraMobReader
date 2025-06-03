# Korean XML Search Application

This application allows users to search through XML data sheets (potentially containing Korean and English text) using English queries. It translates search queries and data on the fly to provide results in English.

## Features

*   Parses XML files containing NPC (Non-Player Character) and item drop information.
*   Translates Korean text (NPC names, item names) to English.
*   Allows searching for NPCs based on their names or item names using English queries.
*   Search functionality works for both original English and original Korean names/items.
*   Provides a Tkinter-based Graphical User Interface (GUI).

## Project Structure

```
korean_xml_search_app/
├── data/
│   └── xmls/
│       └── sample.xml  # Sample XML file (add your 400 XMLs here)
├── src/
│   ├── __init__.py
│   ├── xml_parser.py   # Handles XML parsing and initial data extraction
│   ├── translator.py   # Handles language detection and translation
│   ├── indexer.py      # Builds data structures and search indexes
│   ├── search_engine.py# Core search logic
│   └── gui.py          # Tkinter GUI application
├── tests/
│   ├── __init__.py
│   ├── test_data.xml
│   ├── test_xml_parser.py
│   ├── test_translator.py
│   ├── test_indexer.py
│   └── test_search_engine.py
└── README.md
```

## Setup and Installation

1.  **Python:** Ensure you have Python 3.7+ installed.
2.  **Clone the Repository (Example):**
    ```bash
    # git clone <repository_url>
    # cd korean_xml_search_app
    ```
3.  **Create a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
4.  **Install Dependencies:**
    The application requires the following Python libraries:
    *   `googletrans-py==4.0.0rc1` (for translation)
    *   `langdetect` (for language detection)
    *   `Tkinter` (usually included with Python, but may need separate installation on some Linux systems: `sudo apt-get install python3-tk`)

    Install them using pip:
    ```bash
    pip install deep-translator langdetect
    ```
    *(Note: Live translations require an internet connection. `TEST_MODE` in `src/translator.py` can be used for offline development.)*

## Running the Application

1.  **Place XML Files:**
    *   Put your XML data sheets into the `korean_xml_search_app/data/xmls/` directory. The application comes with a `sample.xml`.

2.  **Translator Mode (`src/translator.py`):**
    *   The `translator.py` file has a `TEST_MODE` flag.
    *   **`TEST_MODE = True` (Default for Development/Testing):** Uses placeholder translations (e.g., "en_TEXT") without making live network calls. This is useful for offline development or avoiding API rate limits.
    *   **`TEST_MODE = False` (For Live Translation):** Attempts to use the `googletrans` library to perform actual Korean/English translations via Google Translate. This requires an active internet connection.
    *   **Important:** For initial use, you might want to test with `TEST_MODE = True`. Change it to `False` in `src/translator.py` when you want live translations. Be mindful of potential API usage limits of the underlying Google Translate service if making many requests.

3.  **Run the GUI:**
    Navigate to the `src` directory and run `gui.py`:
    ```bash
    cd src
    python3 gui.py
    ```
    *Note: If you encounter Tkinter import errors on Linux, ensure `python3-tk` is installed (see dependencies).*

## Running Unit Tests

To run the unit tests, navigate to the project root directory (`korean_xml_search_app/`) and run:
```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```
All tests should pass, especially when `translator.TEST_MODE` is `True`.

## How it Works

1.  **XML Parsing (`xml_parser.py`):** Reads XML files, extracts NPC and item names.
2.  **Translation (`translator.py`):** Detects language and translates Korean text to English (and vice-versa for search queries).
3.  **Indexing (`indexer.py`):**
    *   Loads all data from XMLs.
    *   Builds an inverted index from English NPC and item names for fast keyword searching.
4.  **Search (`search_engine.py`):**
    *   Takes an English user query.
    *   Searches the English inverted index.
    *   Translates the English query to Korean and searches original Korean names/items.
    *   Combines results.
5.  **GUI (`gui.py`):** Provides a user interface to input queries and view results.

```
