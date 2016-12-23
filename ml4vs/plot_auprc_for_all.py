import os
import numpy as np
import sys
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from sklearn import decomposition
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.preprocessing import Imputer
from sklearn.preprocessing import StandardScaler

# NN
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.constraints import maxnorm
from keras.optimizers import SGD
from keras import callbacks
from keras.wrappers.scikit_learn import KerasClassifier
from sklearn.svm import SVC

from data_load import load_data
from plotting import plot_cv_pr


# Function that transforms some features
def log_axis(X_, names=None):
    X = X_.copy()
    tr_names = ['clipped_sigma', 'weighted_sigma', 'RoMS', 'rCh2', 'Vp2p',
                'Ex', 'inv_eta', 'S_B']
    for name in tr_names:
        try:
            # print "Log-Transforming {}".format(name)
            i = names.index(name)
            X[:, i] = np.log(X[:, i])
        except ValueError:
            print "No {} in predictors".format(name)
            pass
    return X


# Load data
data_dir = '/home/ilya/code/ml4vs/data/LMC_SC20__corrected_list_of_variables/raw_index_values'
file_1 = 'vast_lightcurve_statistics_variables_only.log'
file_0 = 'vast_lightcurve_statistics_constant_only.log'
file_0 = os.path.join(data_dir, file_0)
file_1 = os.path.join(data_dir, file_1)
names = ['Magnitude', 'clipped_sigma', 'meaningless_1', 'meaningless_2',
         'star_ID', 'weighted_sigma', 'skew', 'kurt', 'I', 'J', 'K', 'L',
         'Npts', 'MAD', 'lag1', 'RoMS', 'rCh2', 'Isgn', 'Vp2p', 'Jclp', 'Lclp',
         'Jtim', 'Ltim', 'CSSD', 'Ex', 'inv_eta', 'E_A', 'S_B', 'NXS', 'IQR']
names_to_delete = ['meaningless_1', 'meaningless_2', 'star_ID',
                   'Npts', 'CSSD', 'clipped_sigma', 'lag1', 'L', 'Lclp', 'Jclp',
                   'MAD', 'Ltim']
X, y, df, feature_names, delta = load_data([file_0, file_1], names,
                                           names_to_delete)
target = 'variable'
predictors = list(df)
predictors.remove(target)


# Create model for NN
def create_baseline():
    model = Sequential()
    model.add(Dense(18, input_dim=18, init='normal', activation='relu',
                    W_constraint=maxnorm(9.388)))
    model.add(Dropout(0.04))
    model.add(Dense(13, init='normal', activation='relu',
                    W_constraint=maxnorm(2.72)))
    # model.add(Activation(space['Activation']))
    model.add(Dropout(0.09))
    model.add(Dense(1, init='normal', activation='sigmoid'))

    # Compile model
    learning_rate = 0.213
    decay_rate = 0.001
    momentum = 0.9
    sgd = SGD(lr=learning_rate, decay=decay_rate, momentum=momentum,
              nesterov=False)
    model.compile(loss='binary_crossentropy', optimizer=sgd,
                  metrics=['accuracy'])
    return model

earlyStopping = callbacks.EarlyStopping(monitor='val_loss', patience=50,
                                        verbose=1, mode='auto')

estimators = list()
estimators.append(('imputer', Imputer(missing_values='NaN', strategy='median',
                                      axis=0, verbose=2)))
estimators.append(('scaler', StandardScaler()))
estimators.append(('mlp', KerasClassifier(build_fn=create_baseline,
                                          nb_epoch=200,
                                          batch_size=1024,
                                          verbose=2)))
pipeline_nn = Pipeline(estimators)


# Create model for GB
sys.path.append('/home/ilya/xgboost/xgboost/python-package/')
import xgboost as xgb
clf = xgb.XGBClassifier(n_estimators=85, learning_rate=0.111,
                        max_depth=6,
                        min_child_weight=2,
                        subsample=0.275,
                        colsample_bytree=0.85,
                        colsample_bylevel=0.55,
                        gamma=3.14,
                        scale_pos_weight=6,
                        max_delta_step=7)
estimators = list()
estimators.append(('imputer', Imputer(missing_values='NaN', strategy='median',
                                      axis=0, verbose=2)))
estimators.append(('clf', clf))
pipeline_xgb = Pipeline(estimators)


# Create model for RF
clf = RandomForestClassifier(n_estimators=1200,
                             max_depth=17,
                             max_features=3,
                             min_samples_split=2,
                             min_samples_leaf=3,
                             class_weight='balanced_subsample',
                             verbose=1, random_state=1, n_jobs=4)
estimators = list()
estimators.append(('imputer', Imputer(missing_values='NaN', strategy='median',
                                      axis=0, verbose=2)))
estimators.append(('clf', clf))
pipeline_rf = Pipeline(estimators)


# Create model for LR
clf = LogisticRegression(C=1.29, class_weight={0: 1, 1: 2},
                         random_state=1, max_iter=300, n_jobs=1,
                         tol=10.**(-5))
pca = decomposition.PCA(n_components=16, random_state=1)
estimators = list()
estimators.append(('imputer', Imputer(missing_values='NaN', strategy='median',
                                      axis=0, verbose=2)))
estimators.append(('func', FunctionTransformer(log_axis, kw_args={'names':
                                                                  predictors})))
estimators.append(('scaler', StandardScaler()))
estimators.append(('pca', pca))
estimators.append(('clf', clf))
pipeline_lr = Pipeline(estimators)


# Create model for SVM
clf = SVC(C=37.286, class_weight={0: 1, 1: 3}, probability=True,
          gamma=0.01258, random_state=1)
estimators = list()
estimators.append(('imputer', Imputer(missing_values='NaN', strategy='median',
                                      axis=0, verbose=2)))
estimators.append(('scaler', StandardScaler()))
estimators.append(('clf', clf))
pipeline_svm = Pipeline(estimators)


# Create model for KNN
clf = KNeighborsClassifier(n_neighbors=6,
                           weights='distance', n_jobs=2)
estimators = list()
estimators.append(('imputer', Imputer(missing_values='NaN', strategy='median',
                                      axis=0, verbose=2)))
estimators.append(('scaler', StandardScaler()))
estimators.append(('clf', clf))
pipeline_knn = Pipeline(estimators)


fig = None
colors_dict = {pipeline_lr: 'lime', pipeline_rf: 'blue',
               pipeline_xgb: 'black', pipeline_nn: 'red',
               pipeline_knn: 'orange', pipeline_svm: 'magenta'}
labels_dict = {pipeline_rf: 'RF', pipeline_nn: 'NN', pipeline_xgb: 'GB',
            pipeline_lr: 'LR', pipeline_knn: 'kNN', pipeline_svm: 'SVM'}
pipelines = [pipeline_lr, pipeline_rf, pipeline_xgb, pipeline_nn, pipeline_knn,
             pipeline_svm]

for i, pipeline in enumerate(pipelines):

    fig = plot_cv_pr(pipeline, X, y, seeds=range(1, 97, 8),
                     plot_color=colors_dict[pipeline],
                     fig=fig, label=labels_dict[pipeline])

patches = list()
for pipeline in pipelines:
    patches.append(mpatches.Patch(color=colors_dict[pipeline],
                                  label=labels_dict[pipeline]))
plt.legend(handles=patches, loc="lower left")
plt.show()


