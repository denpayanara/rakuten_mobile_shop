import requests

import pandas as pd

res = requests.get('https://network.mobile.rakuten.co.jp/shopmaster-public/v1/shops/')

data = res.json()

df0 = pd.json_normalize(data)

df1 = df0[['code', 'name', 'location.prefecture', 'location.city', 'location.address', 'location.building_name',  'contact_info.phone', 'regular_timings.open_time', 'regular_timings.end_time', 'start_date', 'location.latitude', 'location.longitude',]].copy()

df1.rename(columns={'location.latitude': 'lat', 'location.longitude': 'lng'}, inplace=True)

import geopandas as gpd
import shutil

shutil.unpack_archive('N03-20220101_GML_simple.zip', 'data')

# シェープファイル読込
gdf0 = gpd.read_file('data/N03-20220101_GML_simple') # 全国

df_pt = gpd.GeoDataFrame(
    df1,
    geometry = gpd.points_from_xy(df1.lng, df1.lat),
    crs = 'EPSG:6668'
)

# 空間結合
spj = gpd.sjoin(df_pt, gdf0, how="inner", predicate='intersects')

df2 = spj[['code', 'name', 'N03_007', 'location.prefecture', 'location.city', 'location.address', 'location.building_name',  'contact_info.phone', 'regular_timings.open_time', 'regular_timings.end_time', 'start_date', 'lat', 'lng']].copy().sort_values(['N03_007', 'name']).reset_index(drop=True)

df_nara = df2[df2['location.prefecture'] == '奈良県'].reset_index(drop=True)

# 前回データ
df_nara_before = pd.read_csv('shops_nara.csv')

# 差分
df_diff = df_nara[~df_nara['name'].isin(df_nara_before['name'])]

if len(df_diff) > 0:

    import os

    from linebot import LineBotApi
    from linebot.models import TextSendMessage
    import tweepy

    message = f'奈良県にて{len(df_diff)}件の楽天モバイルショップがオープンしました。\n\n'

    for i, shop in df_diff.iterrows():

        message += f'市区町村名: {shop["location.city"]}\n店舗名: {shop["name"]}\n\n'

    message += 'https://network.mobile.rakuten.co.jp/shop/search/?prefecture=%E5%A5%88%E8%89%AF%E7%9C%8C&city=\n'

    message += '#bot'

    print(message)

    # LINE
    line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
    # 送信
    line_bot_api.broadcast(messages = [TextSendMessage(text = message)])

    # Twitter
    api_key = os.environ["API_KEY"]
    api_secret = os.environ["API_SECRET_KEY"]
    access_token = os.environ["ACCESS_TOKEN"]
    access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]
    auth = tweepy.OAuthHandler(api_key, api_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    # 送信
    api.update_status(status = message)

    df_diff.to_csv('shops_nara.csv', index=False, encoding='utf_8_sig')

