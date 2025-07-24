# Overview

### Steps to run the project
1. latest version of trafilatura didn't have lxml clean so had to `pip install lxml_html_clean`
2. Setup minio using docker:
    1. Create a local directory for volume: `mkdir -p ${HOME}/minio/data`
    2. ```docker run \
        -p 9090:9000 \
        -p 9091:9091 \
        --user $(id -u):$(id -g) \
        --name minio1 \
        -e "MINIO_ROOT_USER=root" \
        -e "MINIO_ROOT_PASSWORD=password" \
        -v ${HOME}/minio/data:/data \
        quay.io/minio/minio server /data --console-address ":9091"```

### Challenges solved
- Batcher and worker:
    - Add Prometheus counters that track how many documents we are filtering at every stage. This can be done both in the batcher and in the worker. ✅
- Worker:
    - Write the extracted and filtered document content to an object store. It should be possible to pass the address of the object store bucket to the worker. If you don't already have an object store bucket lying around, you can spin up a minio/minio container for that and pass the object store address to the worker. Which file format would you use to store the entries on the object store? ✅
        - File format used: parquet. For efficient storage, structured schema, better for future data analysis.
        - However, JSONL could be a good decision too if the data is being streamed directly to train a model, however here we are just storing it in minio.
    - Add tokenization so that we already have tokenized data ready for training on the object store. The Huggingface tokenizers library might be a good starting point. ✅
        - Used gpt2 tokenizer, as quick research suggests that its good for english (which is a filter in the worker).
    - Add some metrics so that we know how much data we are currently downloading and how many batches we have already processed and how many documents we have already processed. ✅
        - Added prometheus counters for each.
    - (Rust only) Can performance be improved by leveraging the tokio async runtime, maybe even using multiple threads if necessary? ❌
    - Add a filter that makes sure that documents are at least 500 characters long and at most 1,000,000 characters long. ✅
- Batcher:
    - Make it possible to pass the version of the crawl as an argument. Currently, it is hardcoded to CC-MAIN-2024-30. ❌
    - (Rust only) Can we get rid of the collect in the batcher that collects the filtered CdxEntrys? ❌
    - Put in some error handling when publishing a batch to RabbitMQ. Can we recover from network issues or timeouts? ✅
        - Added retry with backoff, and batcher skips index if retry exceeds max.
    - Add some monitoring for the batcher so that we know which percentage of the cluster.idx file has already been processed and so that we know how many batches have already been pushed. ❌
    - Allow support for providing multiple crawls that can be processed by the batcher. This feature allows us to collect more data than would be available from a single crawl. But notice that this feature is only useful if we can make sure that we only download the content of every URL only once. Notice that a URL might show up in multiple crawls over time. 🟠❓
        - A potential solution would be to pass a list of cluster files through command line, and keep a check of seen_urls so as to avoid repeating.
