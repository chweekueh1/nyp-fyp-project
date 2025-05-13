# NYP FYP CNC Chatbot

## Installation and Set-up

1. Git Clone the repository (Branch: **main**)

2. Install [Python Version 3.11.9](https://www.python.org/downloads/release/python-3119/)

   1. Open the installer and ensure to check the box (add to PATH) on the bottom of the installer screen.


3. Once done, open the cloned GitHub repository (in VS Code)
   
   1. Press Ctrl + Shift + P and search 'Python: Select Interpreter'.
   2. Find and select Python 3.11.9

4. Install the library dotenv

   Open a terminal ( Command Prompt )

``` bash

  pip install dotenv

```

5. Run the setup.py

``` bash

  python setup.py

```
6. Activate the virtual enviroment

``` bash

  .venv\Scripts\activate

```

7. Install the library libmagic

``` bash

  pip install python-magic
  pip install python-magic-bin

```


## Running the Model Interface (Frontend & Backend)

Run app.py and streamlit_app.py

```bash

python app.py
streamlit run streamlit_app.py

```

## Environment Variables

To run this project, you will need to add the following environment variable to your .env file

`OPENAI_API_KEY`
