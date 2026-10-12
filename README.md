# Proyek Analisis Data: E-Commerce Public Dataset ✨

Analisis data transaksi marketplace Olist (Brasil, Januari 2017 - Agustus 2018) beserta dashboard interaktif Streamlit.

**Pertanyaan bisnis**
1. Kategori produk dengan revenue tertinggi pada Jan-Agu 2018, pertumbuhannya dibanding Jan-Agu 2017, dan review score-nya.
2. State dengan waktu pengiriman terlama / keterlambatan tertinggi dan dampak keterlambatan terhadap review score.

Analisis lanjutan: RFM Analysis, Geospatial Analysis, dan Binning.

## Struktur Direktori
```
final
├───dashboard
|   ├───main_data.csv
|   ├───state_geo.csv
|   └───dashboard.py
├───data
|   └───*.csv (dataset asli)
├───notebook.ipynb
├───README.md
├───requirements.txt
└───url.txt
```

## Setup Environment - Anaconda
```
conda create --name main-ds python=3.9
conda activate main-ds
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal
```
mkdir proyek_analisis_data
cd proyek_analisis_data
pipenv install
pipenv shell
pip install -r requirements.txt
```

## Run Streamlit App
```
cd dashboard
streamlit run dashboard.py
```
