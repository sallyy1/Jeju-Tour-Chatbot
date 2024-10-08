# Jeju-Tour-Chatbot
Jeju Tour Chatbot using Solar LLM model of Upstage.

This is my project for **Global AI Week - AI Hackathon** (Upstage, August 2024)

## 🚀 DEMO video: [Here](https://drive.google.com/file/d/19nnUcPvbLEtMi8Mlivcx5SfTswKpog0M/view?usp=drive_link)

## 1. Prepare Your Virtual Environment

1. **Create a new virtual environment:**

   ```bash
   python3.10 -m venv new_jeju_upstage

2. **Activate the virtual environment:**

   ```bash
   source new_jeju_upstage/bin/activate

3. **Install libraries:**
   
   ```bash
   pip install -r requirements.txt

## 2. Run Streamlit python code for the web page
   ```bash
   run streamlit_run.sh
```
## 3. Enter in the website link

## 4. Chat with Solar model and have fun!

## The sections where Upstage API
- Where Upstage API is used: **solar_predibase_0818_final.ipynb** (for fine-tuning Solar model) and **streamlit_jeju_multi-turn-final.py** (for generate using fine-tuned Solar model & base Solar model)



### References list
- How to preprocess the source dataset: **source_dataset_make_1st.ipynb**
- How to fine-tune Solar model on multi-turn conversation task: **solar_predibase_0818_final.ipynb**
- Where to get my own Google Maps API: **[Google Cloud Platform](https://console.cloud.google.com/)**
