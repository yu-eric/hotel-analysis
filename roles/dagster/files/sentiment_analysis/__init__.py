from dagster import asset, Config, ConfigurableResource, Definitions, Output, MetadataValue, op
from dask.distributed import Client
from transformers import Pipeline
from sqlalchemy import Engine

import dask.dataframe as dd
import pandas as pd
import sqlalchemy as sa
import transformers as t

class DaskResource(ConfigurableResource):
    def get_client() -> Client:
        return Client("127.0.0.1:8786")

class PostgresResource(ConfigurableResource):
    def get_engine() -> Engine:
         return sa.create_engine("postgresql+psycopg:///dagster")
    
class InputConfig(Config):
    filename: str = "Hotel_Reviews.csv"
    
@asset(description="The name of the file uploaded to the dask bucket for processing")
def input_file(config: InputConfig) -> str:
    return config.filename


@asset(compute_kind="csv", description="Load input CSV")
def hotel_reviews(input_file: str) -> dd.DataFrame:
    s3_url = "s3://dask/" + input_file
    # Update this endpoint URL to match your S3-compatible storage endpoint
    s3_config = {"anon": True, "client_kwargs": {"endpoint_url": "https://your-s3-endpoint.example.com"}}
    df = dd.read_csv(s3_url, storage_options=s3_config)
    df = df.repartition(npartitions=128)
    return df

@asset(compute_kind="huggingface", description="Load sentiment analysis pipeline")
def sentiment_analysis_model() -> Pipeline:
    sentiment_model = t.pipeline(
        "sentiment-analysis",
        model="cardiffnlp/twitter-roberta-base-sentiment-latest",
        return_all_scores=True,
        max_length=512,
        truncation=True
        )
    return sentiment_model

@op
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


@asset(compute_kind="dask", description="Scores hotel reviews using sentiment analysis")
def scored_reviews(hotel_reviews: dd.DataFrame, sentiment_analysis_model: Pipeline, dask_cluster: DaskResource):
    client = dask_cluster.get_client()
    s3_url = "s3://dask/output/"
    # Update this endpoint URL to match your S3-compatible storage endpoint
    config = {"anon": True, "client_kwargs": {"endpoint_url": "https://your-s3-endpoint.example.com"}}

    meta = pd.DataFrame({
        'Positive_Score': pd.Series(dtype='float64'),
        'Negative_Score': pd.Series(dtype='float64')
    })

    scored_partitions = hotel_reviews.map_partitions(score_partition, sentiment_analysis_model, meta=meta)

    scored_ddf = hotel_reviews.assign(
        Positive_Score=scored_partitions['Positive_Score'],
        Negative_Score=scored_partitions['Negative_Score']
    )

    scored_ddf.to_parquet(
        s3_url,
        engine='pyarrow',
        write_index=False,
        compute=True,
        storage_options=config
    )

@asset(compute_kind="postgresql", description="Save results to Postgres")
def save_reviews_db(scored_reviews, engine: PostgresResource):
    # Update this endpoint URL to match your S3-compatible storage endpoint
    config = {"anon": True, "client_kwargs": {"endpoint_url": "https://your-s3-endpoint.example.com"}}
    scored_ddf = pd.read_parquet("s3://dask/output/", storage_options=config)
    con = engine.get_engine()

    scored_ddf.to_sql(
        name='hotel_reviews',
        con=con,
        if_exists='append',
        index=False
    )

@asset(compute_kind="csv", description="Save results to CSV")
def save_reviews_csv(scored_reviews, input_file: str) -> Output[None]:
    csv_path = "s3://dask/scored_" + input_file
    # Update this endpoint URL to match your S3-compatible storage endpoint
    config = {"anon": True, "client_kwargs": {"endpoint_url": "https://your-s3-endpoint.example.com"}}
    data = pd.read_parquet("s3://dask/output/", storage_options=config)

    data.to_csv(csv_path, index=False, storage_options=config)

    return Output(
        value=None,
        metadata={
            "csv_path": MetadataValue.path(csv_path),
            "num_rows": len(data),
            "preview": MetadataValue.md(data.head().to_markdown())
        }
    )


defs = Definitions(
    assets=[
        input_file,
        hotel_reviews,
        sentiment_analysis_model,
        scored_reviews,
        save_reviews_db,
        save_reviews_csv
        ],
    resources={
        "dask_cluster": DaskResource,
        "engine": PostgresResource
        }
    )
