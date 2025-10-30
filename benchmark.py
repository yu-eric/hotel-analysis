from dask.distributed import Client, LocalCluster
from transformers import Pipeline
import transformers as t
import time

import dask.dataframe as dd
import pandas as pd

def score_partition(df_partition: pd.DataFrame, model: Pipeline) -> pd.DataFrame:
        positive_scores = []
        negative_scores = []

        pos_rev_col = df_partition.get('Positive_Review', pd.Series(dtype='string'))
        neg_rev_col = df_partition.get('Negative_Review', pd.Series(dtype='string'))

        for review in pos_rev_col:
            if review == 'No Positive':
                positive_scores.append(0.0)
            else:
                result = model(review)
                score = result[0][2].get('score')
                positive_scores.append(round(score, 2))

        for review in neg_rev_col:
            if review == 'No Negative':
                negative_scores.append(0.0)
            else:
                result = model(review)
                score = result[0][0].get('score')
                negative_scores.append(round(score, 2))


        return pd.DataFrame({
            'Positive_Score': positive_scores,
            'Negative_Score': negative_scores
        }, index=df_partition.index)

    
if __name__ == '__main__':
    cluster = LocalCluster(n_workers=4, threads_per_worker=2)
    client = Client(cluster)    # replace with Client("127.0.0.1:8786") if testing distributed
    s3_url = "s3://dask/"
    # Update this endpoint URL to match your S3-compatible storage endpoint
    config = {"anon": True, "client_kwargs": {"endpoint_url": "https://your-s3-endpoint.example.com"}}

    df = dd.read_csv(s3_url + "test.csv", storage_options=config) # change path to local path if not using s3, and remove storage_options
    df = df.repartition(npartitions=32)

    sentiment_model = t.pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            return_all_scores=True,
            )

    meta = pd.DataFrame({
            'Positive_Score': pd.Series(dtype='float64'),
            'Negative_Score': pd.Series(dtype='float64')
        })

    scored_partitions = df.map_partitions(score_partition, sentiment_model, meta=meta)

    scored_ddf = df.assign(
        Positive_Score=scored_partitions['Positive_Score'],
        Negative_Score=scored_partitions['Negative_Score']
    )

    start_time = time.perf_counter()

    # actual computation starts here
    scored_ddf.to_parquet(
        s3_url + "output/",
        engine='pyarrow',
        write_index=False,
        compute=True,
        storage_options=config
    )    # change path to local path if not using s3, and remove storage_options

    end_time = time.perf_counter()
    runtime_seconds = end_time - start_time

    print(f"\n--- Statistics ---")
    print(f"Runtime: {runtime_seconds:.4f} seconds")

    time.sleep(10000)