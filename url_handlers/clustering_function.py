"""
import collections
import pandas as pd
import sklearn.cluster
import sklearn.metrics.pairwise
import sklearn.mixture
import sklearn.preprocessing
import misc.parallel as parallel
import misc.utils as utils
import numpy as np
import modules.load_data_postgre as ps
from sklearn.metrics import silhouette_samples, silhouette_score
import gower

def cluster_numeric_fields(entities, df):
    """
"""
    Cluster the given numeric entities using a DP-GMM.

    Paramters
    ---------
    entities: list of strings
        The names of the numeric entities

    standardize : bool
        Whether to standardize the values before clustering


    Returns
    -------
    df : sklearn.mixture.BayesianGaussianMixture
        The fit mixture model

    cluster_data : dict
        A dictionary mapping from each label to the number of items with that
        label.

    cluster_labels: pd.DataFrame
        The data frame containing entity values for each patient
    """
"""
    import misc.math_utils as math_utils

    df = df.dropna()
    X = df[entities].values
    scaler = sklearn.preprocessing.StandardScaler()
    X = scaler.fit_transform(X)
    df[entities] = X
    X = df[entities].values


    cluster_data = math_utils.fit_bayesian_gaussian_mixture(
        X,
        n_components=5,
        max_iter=1000,
        reg_covar=0,
        mean_precision_prior=0.8,
        weight_concentration_prior_type="dirichlet_process",
        init_params='kmeans',
        seed=8675309
    )

    """
"""
    for n_cluster in range(3,10):
        print(n_cluster)
        cluster_dataa = math_utils.fit_bayesian_gaussian_mixture(
            X,
            n_components=n_cluster,
            max_iter=1000,
            reg_covar=0,
            mean_precision_prior=0.8,
            weight_concentration_prior_type="dirichlet_process",
            init_params='kmeans',
            seed=8675309
        )
        clusterss = cluster_dataa.predict(X)
        silhouette_avg = silhouette_score(X, clusterss)
        print("For n_clusters =", n_cluster,
              "The average silhouette_score is :", silhouette_avg)
    """
"""
    clusters = cluster_data.predict(X)

    df['cluster'] = clusters

    cluster_labels = collections.defaultdict(int)
    for l in clusters:
        cluster_labels[l] += 1

    for i, means in enumerate(cluster_data.means_):
        cluster_data.means_[i] = scaler.inverse_transform(means)

    return cluster_data, cluster_labels, df, None

def _get_patient_categorical_rep(row, categorical_entities):
    ret = {}

    for categorical_entity in categorical_entities:
        vals = row[categorical_entity]

        # make sure this is a list of values, which is what
        # we expect from rwh.get_joined_categorical_values
        #if not utils.is_sequence(vals):
        #    continue


        key = "{}.{}".format(categorical_entity, vals)
        ret[key] = 1

    return ret

# use in clustering
def cluster_categorical_entities(entities,cat_df, eps=0.1, min_samples=5, seed=8675309):
"""
""" Cluster patients based on the given categorical entities using DBSCAN.
    The Jaccard distance is used for clustering.
    Paramters
    ---------
    entities: list of strings
        The names of the numeric entities
    r: redis.StrictRedis
        The redis database connection
    eps: float
        The maximum distance between two samples to clsuter them together.
        Please see sklearn.cluster.DBSCAN for more details.
    min_samples: int
        The minimum number of samples in each cluster
    seed: int
        The random seed
    Returns
    -------
    cluster_category_values: dict
        Mapping from cluster label to the count of each category value observed
        for patients in that cluster
    patient_np: 2-dimensional (binary) np.array
        The indicator matrix of each (entity,value) for each patient
    category_values: list of pairs of strings
        All observed (category,value) pairs
    label_uses : dict
        A dictionary mapping from each label to the number of items with that
        label.
    patient_df: pd.DataFrame
        The data frame containing entity values for each patient
    """
"""
    # pull the values from the database
    ##cat_df, error = rwh.get_joined_categorical_values(entities, r)  # .dropna()
    cat_df=cat_df[:10000]
    # the error is here. cat_rep returns dicts with empty values
    # get the binary representation
    cat_rep = parallel.apply_df_simple(
        cat_df,
        _get_patient_categorical_rep,
        entities
    )

    # convert it to a numpy 2-d array; each row is a patient
    cat_rep_df = pd.DataFrame(cat_rep)

    category_values = sorted(cat_rep_df.columns)
    cat_rep_np = cat_rep_df.fillna(0).values


    # calculate the jaccard distances between all patients
    distance = sklearn.metrics.pairwise.pairwise_distances(
        cat_rep_np,cat_rep_np,
        metric='jaccard',
        n_jobs=10
    )

    # cluster the patients based on the jaccard distances
    db = sklearn.cluster.DBSCAN(
        eps=eps,
        min_samples=min_samples,
        metric='precomputed' \
        )
    db.fit(distance)

    # add the clustering information to the
    cat_df['cluster'] = db.labels_

    # collect the usage information
    unique_labels = set(db.labels_)
    label_uses = {}
    cluster_category_values = {}

    for l in unique_labels:
        m_class = (db.labels_ == l)
        label_uses[l] = np.sum(m_class)
        cluster_category_values[l] = cat_rep_df[m_class].count()

    return distance,cluster_category_values, cat_rep_np, category_values, label_uses, cat_df


# use in clustering
def cluster_mixed_entities(entities,cat_df, eps=0.1, min_samples=5, seed=8675309):
    cat_df = cat_df[:300]
    distance = gower.gower_matrix(cat_df)
    print(distance)

    kmedoids = sklearn.cluster.KMeans(n_clusters=5, precompute_distances=True).fit(
        distance)
    cat_df['cluster'] = kmedoids.labels_
    """
"""
    # cluster the patients based on the jaccard distances
    db = sklearn.cluster.DBSCAN(
        eps=eps,
        min_samples=min_samples,
        metric='precomputed' \
        )
    db.fit(distance)

    # add the clustering information to the
    cat_df['cluster'] = db.labels_
    """
"""
    return distance, cat_df
    
"""