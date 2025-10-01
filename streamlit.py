import streamlit as st
# import boto3
# from openai import OpenAI
# import pandas as pd
import uuid
from datetime import datetime
# import os

# OpenAIクライアントを生成
version = "1.2025.1001.1810"

SUCCESS_MSG1 = "処理が開始されました。結果をEmailでお知らせします。\n（1分あたり処理件数の目安：10件）"
SUCCESS_MGS2 = "認証メールが送信されました。下記の手順に従って認証を完了してください。"
ERR_MSG1 = "処理中にエラーが発生しました。"
ERR_MSG2 = "CSVファイルとEmailアドレスを両方入力してください。"
ERR_MSG3 = "このメールアドレスは既に登録されています。"
ERR_MSG4 = "Emailアドレスを入力してください。"

def generate_s3_filename():
    generated_uuid = uuid.uuid4()
    # 現在の日時を取得
    now = datetime.now()
    # フォーマットを指定して文字列を生成
    date_string = now.strftime("%Y%m%d%H%M%S")
    return f"{date_string}-{generated_uuid}"

def check_sns_subscription(sns, topic_arn, email_address):
    # トピックに関連するサブスクリプションを取得
    response = sns.list_subscriptions_by_topic(TopicArn=topic_arn)
    
    # メールアドレスが既に登録されているか確認
    is_subscribed = False
    for subscription in response['Subscriptions']:
        if subscription['Endpoint'] == email_address:
            is_subscribed = True
            break
    
    return is_subscribed

# SNSクライアントの作成
# sns_client = boto3.client('sns', region_name='ap-northeast-1')

st.title("まとめて処理アプリ")
st.markdown(
    f'<p style="text-align: right; font-size: 12px;">Ver.{version}</p>',
    unsafe_allow_html=True
)

email_address = st.text_input("Emailアドレスを入力")
st.markdown(
    f'<p style="text-align: left; font-size: 12px;">▼初めてこのEmailアドレスを使う場合のみ、ボタンを押してください▼</p>',
    unsafe_allow_html=True
)

if st.button("認証メールを送信"):
    if email_address:
        is_subscribed = check_sns_subscription(sns_client, TOPIC_ARN, email_address)
        if is_subscribed:
            st.error(ERR_MSG3)
        else:
            # SNSを使用して認証メールを送信
            response = sns_client.subscribe(
                TopicArn=TOPIC_ARN,
                Protocol='email',
                Endpoint=email_address
            )
            if 'SubscriptionArn' in response:
                st.success(SUCCESS_MGS2)
                st.image("mailauth.png")
            else:
                st.error(ERR_MSG1)
    else:
        st.error(ERR_MSG4)
            
st.divider()

# 重い処理の受付
# s3_client = boto3.client('s3', region_name='ap-northeast-1')
# ecs_client = boto3.client('ecs', region_name='ap-northeast-1')


# selectboxのセッション状態をクリア
# for key in ["op_select", "col_select"]:
#     if key in st.session_state and not isinstance(st.session_state[key], int):
#         del st.session_state[key]
# if "op_select" in st.session_state:
#     print(st.session_state["op_select"])

csv_file = st.file_uploader("CSVファイルを選択", type=["csv"])

select_options = ['プロンプトを自由入力', '反社チェック用アプリ']

# コンボボックスを表示
selected_option = st.selectbox("操作を選択してください", select_options, index=0, key="op_select")

# 複数行入力可能なテキストボックス
# text = st.text_area("ここにプロンプトを入力してください", disabled=(selected_option == select_options[1]))
text = st.text_area("プロンプトを入力してください",
    disabled=(selected_option == select_options[1]),
    key="prompt_text",
)

output_column = st.text_area("出力するカラムをカンマ区切りで入力してください",
    disabled=(selected_option == select_options[1]),
    key="output_clm",
)

if csv_file is not None:
    # CSVファイルを読み込む
    df = pd.read_csv(csv_file)
    
    # カラム名を取得
    columns = df.columns.tolist()
    
    # カラム名を表示
    # selected_column = st.selectbox("対象の列名を選択してください", columns, disabled=(selected_option == select_options[1]))
    # columns が変わったら選択状態をリセット
    # if st.session_state.get("prev_columns") != columns:
    #     st.session_state.pop("col_select", None)
    #     st.session_state["prev_columns"] = columns

    selected_column = '声の内容'
    # if columns:
    #     selected_column = st.selectbox(
    #         "対象の列名を選択してください",
    #         columns,
    #         disabled=(st.session_state["op_select"] == select_options[1]),
    #         index=0,
    #         key="col_select",
    #     )
    # else:
    #     st.warning("CSVに列が見つかりませんでした。")

if st.button("処理開始"):
    if csv_file and email_address:
        # ファイルポインタを先頭に戻す
        csv_file.seek(0)
        
        # CSVファイルをS3にアップロード
        s3_file_path = f"uploads/{generate_s3_filename()}-{csv_file.name}"
        s3_client.upload_fileobj(csv_file, 'jrq-batch-app', s3_file_path)
        
        if selected_option == select_options[0]:
            # l_tmp = df[selected_column].tolist()
            # result = process_batch(l_tmp[0:10], text)
            
            # st.success(result)
            # ECSタスクにジョブを送信
            if response['tasks']:
                st.success(SUCCESS_MSG1)
            else:
                st.error(ERR_MSG1)
            
        elif selected_option == select_options[1]:
            # ECSタスクにジョブを送信
            if response['tasks']:
                st.success(SUCCESS_MSG1)
            else:
                st.error(ERR_MSG1)
    else:
        st.error(ERR_MSG2)