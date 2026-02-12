
# 測試配置
# 禁用 TensorFlow 以避免 CPU 指令集不兼容問題
import os
os.environ['DISABLE_TENSORFLOW'] = 'true'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
