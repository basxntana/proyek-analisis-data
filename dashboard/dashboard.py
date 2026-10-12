from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

sns.set_theme(style='white')
BASE = Path(__file__).parent

st.set_page_config(page_title='E-Commerce Dashboard', page_icon='🛒', layout='wide')


@st.cache_data
def load_data():
    df = pd.read_csv(BASE / 'main_data.csv', parse_dates=['order_purchase_timestamp'])
    geo = pd.read_csv(BASE / 'state_geo.csv')
    df['year'] = df['order_purchase_timestamp'].dt.year
    df['month'] = df['order_purchase_timestamp'].dt.month
    return df, geo


df, geo = load_data()

# ---------------- Sidebar filter ----------------
st.sidebar.header('Filter')
min_d, max_d = df['order_purchase_timestamp'].dt.date.min(), df['order_purchase_timestamp'].dt.date.max()
date_range = st.sidebar.date_input('Rentang tanggal pembelian', (min_d, max_d), min_value=min_d, max_value=max_d)
states = sorted(df['customer_state'].unique())
sel_states = st.sidebar.multiselect('State pelanggan', states, default=states)

if len(date_range) != 2:
    st.info('Pilih tanggal awal dan akhir.')
    st.stop()
start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]) + pd.Timedelta(days=1)
fdf = df[(df['order_purchase_timestamp'] >= start) & (df['order_purchase_timestamp'] < end) & df['customer_state'].isin(sel_states)]
if fdf.empty:
    st.warning('Tidak ada data untuk filter yang dipilih.')
    st.stop()
orders = fdf.drop_duplicates('order_id')

# ---------------- Header & KPI ----------------
st.title('🛒 E-Commerce Public Dataset Dashboard')
st.caption('Pesanan berstatus delivered, Januari 2017 - Agustus 2018')
c1, c2, c3, c4 = st.columns(4)
c1.metric('Total Revenue', f"R$ {fdf['price'].sum() / 1e6:,.2f} jt")
c2.metric('Jumlah Pesanan', f"{orders['order_id'].nunique():,}")
c3.metric('Pesanan Terlambat', f"{orders['is_late'].mean() * 100:.1f}%")
c4.metric('Rata-rata Review', f"{orders['review_score'].mean():.2f}")

tab1, tab2, tab3 = st.tabs(['Revenue Kategori', 'Pengiriman per State', 'Analisis Lanjutan (RFM & Geospatial)'])

# ---------------- Tab 1: Pertanyaan 1 ----------------
with tab1:
    st.subheader('Kategori dengan revenue tertinggi dan pertumbuhannya')
    top_n = st.slider('Jumlah kategori', 3, 15, 5)
    cmp_df = fdf[fdf['month'] <= 8]
    pv = cmp_df.pivot_table(index='category', columns='year', values='price', aggfunc='sum', fill_value=0)
    for y in (2017, 2018):
        if y not in pv.columns:
            pv[y] = 0
    pv['growth_pct'] = (pv[2018] - pv[2017]) / pv[2017].replace(0, np.nan) * 100
    pv['avg_review'] = cmp_df[cmp_df['year'] == 2018].groupby('category')['review_score'].mean()
    top = pv.sort_values(2018, ascending=False).head(top_n)

    col_a, col_b = st.columns([1.7, 1])
    with col_a:
        plot_df = top[[2017, 2018]].reset_index().melt(id_vars='category', var_name='tahun', value_name='revenue')
        plot_df['revenue'] /= 1000
        fig, ax = plt.subplots(figsize=(8, 0.9 * top_n + 1.5))
        sns.barplot(data=plot_df, y='category', x='revenue', hue='tahun',
                    palette={2017: '#BFC5CC', 2018: '#1f77b4'}, ax=ax)
        ax.set_title('Revenue Jan-Agu 2018 vs Jan-Agu 2017', loc='left')
        ax.set_xlabel('Revenue (ribu BRL)'); ax.set_ylabel('')
        ax.legend(title='Periode', frameon=False); sns.despine(); plt.tight_layout()
        st.pyplot(fig)
    with col_b:
        fig, ax = plt.subplots(figsize=(5, 0.9 * top_n + 1.5))
        sns.barplot(x=top['avg_review'], y=top.index, color='#1f77b4', ax=ax)
        ax.set_xlim(0, 5); ax.set_title('Rata-rata Review Score 2018', loc='left')
        ax.set_xlabel('Review score (skala 1-5)'); ax.set_ylabel(''); ax.set_yticklabels([])
        for c in ax.containers:
            ax.bar_label(c, fmt='%.2f', label_type='center', color='white', fontsize=9)
        sns.despine(); plt.tight_layout()
        st.pyplot(fig)
    st.caption('Perbandingan memakai periode Jan-Agu pada kedua tahun agar adil; hanya data yang lolos filter di sidebar.')
    st.dataframe(top.rename(columns={2017: 'revenue_2017', 2018: 'revenue_2018'}).round(2))

# ---------------- Tab 2: Pertanyaan 2 ----------------
with tab2:
    st.subheader('Waktu pengiriman, keterlambatan, dan dampaknya pada review')
    min_orders = st.slider('Minimal jumlah pesanan per state', 1, 1000, 300, step=10)
    perf = (orders.groupby('customer_state')
            .agg(orders=('order_id', 'count'), avg_delivery_days=('delivery_days', 'mean'),
                 late_pct=('is_late', 'mean'), avg_review=('review_score', 'mean')))
    perf['late_pct'] *= 100
    perf = perf[perf['orders'] >= min_orders].sort_values('avg_delivery_days', ascending=False)

    col_a, col_b = st.columns(2)
    with col_a:
        slow = perf.head(10)
        if slow.empty:
            st.info('Tidak ada state yang memenuhi minimal pesanan.')
        else:
            fig, ax = plt.subplots(figsize=(7, 5))
            colors = ['#d62728' if i < 3 else '#BFC5CC' for i in range(len(slow))]
            sns.barplot(x=slow['avg_delivery_days'], y=slow.index, palette=colors, hue=slow.index, legend=False, ax=ax)
            ax.axvline(orders['delivery_days'].mean(), color='#333', ls='--', lw=1, label='rata-rata nasional')
            ax.set_title('10 State dengan Pengiriman Terlama', loc='left')
            ax.set_xlabel('Rata-rata hari (pembelian -> diterima)'); ax.set_ylabel('')
            for c in ax.containers:
                ax.bar_label(c, fmt='%.1f', padding=3, fontsize=8)
            ax.legend(frameon=False); sns.despine(); plt.tight_layout()
            st.pyplot(fig)
    with col_b:
        lr = orders.groupby('is_late')['review_score'].mean().rename({False: 'Tepat waktu', True: 'Terlambat'})
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.barplot(x=lr.index, y=lr.values, palette=['#BFC5CC', '#d62728'][:len(lr)], hue=lr.index, legend=False, ax=ax)
        ax.set_ylim(0, 5); ax.set_title('Review Score: Tepat Waktu vs Terlambat', loc='left')
        ax.set_xlabel(''); ax.set_ylabel('Rata-rata review score')
        for c in ax.containers:
            ax.bar_label(c, fmt='%.2f', padding=3)
        sns.despine(); plt.tight_layout()
        st.pyplot(fig)
    st.dataframe(perf.round(2))

# ---------------- Tab 3: Analisis lanjutan ----------------
with tab3:
    st.subheader('RFM Analysis (manual grouping)')
    snapshot = fdf['order_purchase_timestamp'].max() + pd.Timedelta(days=1)
    rfm = (fdf.groupby('customer_unique_id')
           .agg(last=('order_purchase_timestamp', 'max'), frequency=('order_id', 'nunique'), monetary=('price', 'sum'))
           .reset_index())
    rfm['recency'] = (snapshot - rfm['last']).dt.days

    def segment(r):
        if r['frequency'] >= 2 and r['recency'] <= 180:
            return 'Loyal'
        if r['frequency'] >= 2:
            return 'Repeat (tidak aktif)'
        if r['recency'] <= 90:
            return 'Baru (<=90 hari)'
        if r['recency'] <= 270:
            return 'Berisiko'
        return 'Hilang (>270 hari)'

    rfm['segment'] = rfm.apply(segment, axis=1)
    seg = (rfm.groupby('segment').agg(pelanggan=('customer_unique_id', 'count'), avg_recency=('recency', 'mean'),
                                      avg_monetary=('monetary', 'mean')).round(1)
           .sort_values('pelanggan', ascending=False))
    seg['pct_pelanggan'] = (seg['pelanggan'] / seg['pelanggan'].sum() * 100).round(1)

    col_a, col_b = st.columns([1, 1])
    with col_a:
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(x=seg['pct_pelanggan'], y=seg.index, color='#1f77b4', ax=ax)
        for c in ax.containers:
            ax.bar_label(c, fmt='%.1f%%', padding=3)
        ax.set_xlabel('% pelanggan'); ax.set_ylabel(''); ax.set_title('Segmen Pelanggan', loc='left')
        sns.despine(); plt.tight_layout()
        st.pyplot(fig)
    with col_b:
        st.dataframe(seg)
        st.caption('Loyal: >=2 pesanan & aktif <=180 hari. Berisiko: 1 pesanan, terakhir beli 91-270 hari lalu.')

    st.subheader('Geospatial: sebaran pesanan dan keterlambatan per state')
    gp = (orders.groupby('customer_state').agg(orders=('order_id', 'count'), late_pct=('is_late', 'mean'))
          .reset_index().rename(columns={'customer_state': 'state'}).merge(geo, on='state'))
    gp['late_pct'] *= 100
    fig, ax = plt.subplots(figsize=(8, 7))
    sc = ax.scatter(gp['lng'], gp['lat'], s=gp['orders'] / 12, c=gp['late_pct'], cmap='YlOrRd',
                    edgecolor='#333', linewidth=.6, alpha=.85)
    for _, r in gp.iterrows():
        ax.annotate(r['state'], (r['lng'], r['lat']), ha='center', va='center', fontsize=7)
    plt.colorbar(sc, label='% pesanan terlambat')
    ax.set_title('Ukuran = jumlah pesanan, warna = % terlambat', loc='left')
    ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude'); ax.set_aspect('equal')
    sns.despine(); plt.tight_layout()
    st.pyplot(fig)
