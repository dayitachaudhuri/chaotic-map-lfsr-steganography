# Audio and Video Steganography Using Chaotic Map and LFSR

### Directory Tree

├───client
│   ├───modes
│   │   ├───image
│   │   │   ├───static
│   │   │   ├───templates
│   │   │   └───__pycache__
│   │   └───video
│   └───templates
└───Code
    ├───assets
    └───outputs
        ├───image_steg
        │   └───histograms
        └───video_steg
            ├───frames
            └───histograms

### Steps to Run the code locally

1. Clone the repository into your local system

   ```
   git clone https://github.com/dayitachaudhuri/chaotic-map-lfsr-steganography
   ```
2. Create virtual environment

   *For Linux/Mac*

   ```
   sudo apt-get install python3.6-venv
   python3 -m venv env
   source env/bin/activate
   ```

* For Windows*

```
pip install virtualenv
python -m venv env
.\env\Scripts\activate

```

3. Download requirements

   ```
   pip install -r requirements.txt
   ```
4. Run Program

   ```
   cd client
   python app.py
   ```
