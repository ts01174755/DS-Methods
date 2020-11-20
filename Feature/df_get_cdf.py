import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import copy
from collections import deque
from pandas.core.frame import DataFrame
from sklearn import metrics
import scipy.stats as st
from collections import defaultdict

def df_get_cdf(df,X,Y,ascending=True):
    def zero():
        return 0
    # df sort 
    df_sort = df.sort_values(by=[X],ascending=ascending).reset_index(drop=True)
    arr_len = df_sort.shape[0]
    
    # Y_arrary
    Y_arr = np.array(df_sort[Y])
    PY_arr = np.zeros(arr_len,dtype=float)

    tmp_N = defaultdict(zero)
    for ind_,val_ in enumerate(Y_arr):
        PY_arr[ind_] = tmp_N[val_] + 1
        tmp_N[val_] += 1
    for ind_,val_ in enumerate(Y_arr):
        PY_arr[ind_] = PY_arr[ind_] / tmp_N[val_]

    df_cdf = pd.concat([df_sort,pd.DataFrame(PY_arr,columns=["%s_cdf"%Y])],axis=1)
    
    return df_cdf.sort_values(by=[X],ascending=True).reset_index(drop=True)

def df_get_cdf_(df,X,Y,ascending=True):
    def zero():
        return 0
    # df sort 
    df_sort = df.sort_values(by=[X],ascending=ascending).reset_index(drop=True)
    arr_len = df_sort.shape[0]
    feat_N = df_sort[Y].unique()
    
    # Y_arrary
    Y_arr = np.array(df_sort[Y])
    PY_arr = np.zeros((arr_len,feat_N.shape[0]),dtype=float)
    columns = ["cdf(%s=%s)" %(Y,v) for i,v in enumerate(feat_N)]

    tmp_N = defaultdict(zero)
    for ind_,val_ in enumerate(Y_arr):
        for fi_,fv_ in enumerate(feat_N):
            if val_ == fv_:
                tmp_N[fv_] += 1
                PY_arr[ind_,fi_] = tmp_N[fv_]
            else:
                PY_arr[ind_,fi_] = tmp_N[fv_]
                
    for fi_,fv_ in enumerate(feat_N):
        PY_arr[:,fi_] = PY_arr[:,fi_] / tmp_N[fv_]

    df_cdf = pd.concat([df_sort,pd.DataFrame(PY_arr,columns=columns)],axis=1)
    
    return df_cdf.sort_values(by=[X],ascending=True).reset_index(drop=True)
#%%
if __name__ == "__main__":
    mu, sigma = 10, 5
    s1 = st.norm(mu, sigma).rvs(100000)
    s2 = st.norm(mu-4, sigma+4).rvs(10000)

    df_1 = pd.DataFrame(s1,columns=["feat"]  )
    df_1['Y'] = 0
    df_2 = pd.DataFrame(s2,columns=["feat"]  )
    df_2['Y'] = 1
    
    df = pd.concat([df_1,df_2],axis=0).reset_index(drop=True)
    df_cdf = df_get_cdf(df, X="feat", Y="Y", ascending=True)
    df_cdf_ = df_get_cdf_(df, X="feat", Y="Y", ascending=True)
    df_cdf_["InfoGain_Y=1"] = df_cdf_["cdf(Y=1)"]*np.log2(df_cdf_["cdf(Y=1)"])
    df_cdf_["InfoGain_Y=0"] = df_cdf_["cdf(Y=0)"]*np.log2(df_cdf_["cdf(Y=0)"])
    df_cdf_["InfoGain_Y=0"] = df_cdf_["InfoGain_Y=0"].fillna(0)
    
    sns.pairplot(df_cdf_.sample(n=1000),hue="Y")
    
#%% xgb
import xgboost as xgb
param = {'max_depth': 8,
         'learning_rate ': 0.02,
         'silent': 1,
         'objective': 'binary:logistic',
         "eval_metric":"auc"
         #"scale_pos_weight":10,
         #"subsample":0.9,
         #"min_child_weight":5,
          }

x_col=['feat','pdf_diff_feat','cdf_div_feat']
train_X = df[x_col]

y_col=['Y']
train_Y = df[y_col]

dtrain = xgb.DMatrix(train_X,label=train_Y)

cv_res= xgb.cv(param,
               dtrain,
               num_boost_round=1000,#830
               early_stopping_rounds=10,
               nfold=3, metrics='logloss',show_stdv=True)

print(cv_res)

#cv_res.shape[0]為最佳迭代次?
bst = xgb.train(param,dtrain,num_boost_round=cv_res.shape[0])
bst.get_score(importance_type='gain')

