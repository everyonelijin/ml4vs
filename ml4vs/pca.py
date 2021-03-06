import os
import matplotlib.pyplot as plt
from sklearn import decomposition
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import Imputer
from sklearn.preprocessing import StandardScaler
from data_load import load_data


data_dir = '/home/ilya/code/ml4vs/data/dataset_OGLE/indexes_normalized'
file_1 = 'vast_lightcurve_statistics_normalized_variables_only.log'
file_0 = 'vast_lightcurve_statistics_normalized_constant_only.log'
file_0 = os.path.join(data_dir, file_0)
file_1 = os.path.join(data_dir, file_1)
names = ['Magnitude', 'clipped_sigma', 'meaningless_1', 'meaningless_2',
         'star_ID', 'weighted_sigma', 'skew', 'kurt', 'I', 'J', 'K', 'L',
         'Npts', 'MAD', 'lag1', 'RoMS', 'rCh2', 'Isgn', 'Vp2p', 'Jclp', 'Lclp',
         'Jtim', 'Ltim', 'CSSD', 'Ex', 'inv_eta', 'E_A', 'S_B', 'NXS', 'IQR']
names_to_delete = ['Magnitude', 'meaningless_1', 'meaningless_2', 'star_ID',
                   'Npts', 'CSSD']
X, y, df, feature_names, delta = load_data([file_0, file_1], names, names_to_delete)


rpca = decomposition.RandomizedPCA()
imp = Imputer(missing_values='NaN', strategy='median', axis=0, verbose=2)
rpca_pipe = Pipeline(steps=[('imputation', imp),
                            ('scaling', StandardScaler()),
                            ('pca', rpca)])
rpca_pipe.fit(X)


pca = decomposition.PCA()
imp = Imputer(missing_values='NaN', strategy='median', axis=0, verbose=2)
pca_pipe = Pipeline(steps=[('imputation', imp),
                           ('scaling', StandardScaler()),
                           ('pca', pca)])
pca_pipe.fit(X)

plt.figure(1, figsize=(4, 3))
plt.clf()
plt.axes([.2, .2, .7, .7])
plt.plot(pca.explained_variance_ratio_, linewidth=2, color='b')
plt.legend()
plt.axis('tight')
plt.xlabel(u'number of components')
plt.ylabel(u'explained variance, $\%$')
plt.show()
plt.savefig('PCA.png', bbox_inches='tight', dpi=200)

