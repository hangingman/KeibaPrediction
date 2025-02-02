import pandas as pd
import time
import warnings

from Keiba.dataprocess import KeibaProcessing
from Keiba.models import KeibaPrediction

"""
Memo:
numpy配列を加工すると処理が急激に重くなるので(16GB一杯になる)、解決できるまでは主成分分析・クラスター分析
などといったreturnがnumpy配列を返す分析手法であるものは使用不可とする。解決が出来次第処理に追加する。
※現状出ている解決策
・メモリを増やす。
・AWSなどを利用する。
"""


def create_keiba_prediction(csv_data, df_flag=True):
    """
    :param csv_data: 「2013年～収集開始日」のデータを持ってくる。データの中身は以下記事を参照すること。
    [https://kashiwapro.hatenablog.com/entry/2021/10/29/162155　](2021/11/17現在)
    :param df_flag:　前処理終了時のデータをそのまま参照する場合はFalseにする。参照するパターンとしては、
    オッズや人気に変化がなく前処理の時間を省略する場合。
    :return:　dataframe(pandas)
    dfで帰ってくるためdf.to_csvなどで出力すること。
    参考：
    df_flag=Trueにすると平均50分かかる(データの量にもよる)、Falseの場合平均30分かかる。
    パソコンのスペック次第では時間がかかる場合もある。
    """
    # csvデータをmodelに読み込ませるように基礎加工する。
    if df_flag:
        set_data = KeibaProcessing(csv_data)
        df = set_data.create_dataframe()
        df.to_csv('Keiba/datafile/pred_data/csvdataframe.csv', encoding='utf_8_sig', index=False)
    else:
        set_data = KeibaProcessing(csv_data)
        df = pd.read_csv('Keiba/datafile/pred_data/csvdataframe.csv')

    # dfデータをLightGBM,tensorflow・logistics用に加工する
    df_gbm = set_data.data_feature_and_formating(df)
    df_logi_tf = set_data.data_feature_and_formating(df, gbmflag=False)

    # df_layerは特徴量をtensorflow用に加工する。
    df_layer = set_data.df_to_tfdata(df_logi_tf)

    # csvデータをモデルに読み込ませる。
    pred_gbm = KeibaPrediction(df_gbm)
    pred = KeibaPrediction(df_logi_tf)

    # モデルを使って予測する。
    gbm = pred_gbm.gbm_params_keiba()
    tenflow = pred.tensorflow_models(df_layer)

    # 予想したものを組み合わせて出力する。
    df = pred.model_concatenation(gbm, tenflow)

    return df


if __name__ == '__main__':

    warnings.simplefilter('ignore')
    # 2013年～収集開始日
    main_data = 'Keiba/datafile/main.csv'
    # 処理開始
    start = time.time()
    # 処理内容
    prediction = create_keiba_prediction(main_data)
    prediction.to_csv('main_ans.csv', encoding='utf_8_sig')
    # 処理終了
    process_time = time.time() - start
    print('実行時間は：{} でした。'.format(process_time))
