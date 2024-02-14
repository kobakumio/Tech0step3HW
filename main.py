import streamlit as st # フロントエンドを扱うstreamlitの機能をインポート
import pandas as pd # データフレームを扱う機能をインポート
import requests
from PIL import Image # 画像表示
import altair as alt
import googlemaps
from dotenv import load_dotenv
import os
import numpy as np
load_dotenv()
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

#SERVICE_ACCOUNT& API Key
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
SPREADSHEET_KEY = os.getenv("SPREADSHEET_KEY")
API_KEY = os.getenv("API_KEY")

# タイトル
st.title('物件ウォッチャー') 

#データフレームの準備
# Googleスプレッドシートの認証情報を設定
def authenticate_gspread():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
    return gspread.authorize(creds)

# スプレッドシートからデータを読み込む関数
def load_data_from_sheet(sheet_name):
    client = authenticate_gspread()
    sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(sheet_name)
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Streamlitアプリケーションのメイン関数
def main():
    
    # セレクトボックスの選択肢
    location = st.selectbox("基準となる場所を選択してください", ["東京駅", "羽田空港"])

    # 選択に応じたデータを読み込む
    if location == "東京駅":
        df = load_data_from_sheet("Tokyo2")
    else:
        df = load_data_from_sheet("HN2")
   
    #タクシー代の選択
    maxfares=df["タクシー料金"].unique()
    selected_maxfare=st.selectbox('タクシー代の上限を選択',maxfares,key="maxfare")
    df2 = df[df["タクシー料金"] <= selected_maxfare]
    #st.table(df2)

    #築年数の選択
    chikunens=df2["築年数"].unique()
    selected_chikunen=st.selectbox('築年数の上限を選択',chikunens,key="chikunen")
    df3=df2[df2['築年数']<= selected_chikunen]
    
    #間取りの選択
    madoris=df3["Layout"].unique()
    selected_madoris=st.multiselect('間取りを選択（複数可）',madoris,key="madoris",default=["1LDK"])
    df4=df3[df3['Layout'].isin(selected_madoris)]

    #毎月の費用の選択
    # 文字列を数値型に変換し、NaN値を0で置き換える
    df4['毎月の費用'] = pd.to_numeric(df4['毎月の費用'], errors='coerce').fillna(0)

    # NaN値がないことを確認
    if df4['毎月の費用'].isnull().any():
        st.write("エラー: NaN値が存在します")
    else:
        min_value = df4['毎月の費用'].min()
        max_value = df4['毎月の費用'].max()

        # スライダーで毎月の費用の範囲を指定
        min_price, max_price = st.slider(
            "毎月の費用の範囲を選択",
            min_value=min_value,
            max_value=max_value,
            value=(min_value, max_value)
        )

        # 指定された範囲に基づいてDataFrameをフィルタリング
        df5 = df4[(df4['毎月の費用'] >= min_price) & (df4['毎月の費用'] <= max_price)]    
        #st.dataframe(df5)
    
    # 'Title' 列のユニークなデータの数を計算
    unique_titles_count = df5['Title'].nunique()
     # df5の行数を取得（タイトル行を除く）
    num_rows = df5.shape[0]
    st.write(f"選択された建物の数: {unique_titles_count}")
    st.write(f"選択された物件の数: {num_rows}") 
    # Titleが重複する物件のうち、毎月の費用が最も小さいものを選び、他の重複データを削除
    df6 = df5.sort_values('毎月の費用').groupby('Title', as_index=False).first()
    org_tokyodf= load_data_from_sheet("Tokyo")
    # df6の[Title]と一致するorg_Tokyodfの[緯度]と[経度]を取得
    df66 = pd.merge(df6, org_tokyodf[['Title', '緯度', '経度']], on='Title', how='left')
    df66.rename(columns={'緯度': 'latitude', '経度': 'longitude'}, inplace=True)
    st.map(df66)
    st.dataframe(df6)

    #建物の選択
    buildings=df5["Title"].unique()
    selected_buildings=st.multiselect('建物を選択（複数可）',buildings,key="building")
    df7=df5[df5['Title'].isin(selected_buildings)]
    
    # URLをHTMLリンクとしてフォーマットする関数
    def make_clickable(url):
        return f'<a href="{url}" target="_blank">{url}</a>'
    # Detail URL列をクリック可能なリンクに変換
    df7['Detail URL'] = df7['Detail URL'].apply(make_clickable)
    # DataFrameをHTMLとして表示
    st.write(df7.to_html(escape=False, index=False), unsafe_allow_html=True)   
if __name__ == "__main__":
    main()
