from abc import ABC, abstractmethod
import csv
import gzip
from typing import Generator, List, Optional
import requests
import time


CRAWL_PATH = "cc-index/collections/CC-MAIN-2024-30/indexes"
BASE_URL = "https://data.commoncrawl.org"


class Downloader(ABC):
    @abstractmethod
    def download_and_unzip(self, url: str, start: int, length: int) -> bytes:
        pass


class CCDownloader(Downloader):
    def __init__(self, base_url: str, max_retries: int = 3, backoff_factor: float = 1.0) -> None:
        self.base_url = base_url
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def download_and_unzip(self, url: str, start: int, length: int) -> bytes:
        for attempt in range(1, self.max_retries + 1):
            try:
                headers = {"Range": f"bytes={start}-{start+length-1}"}
                response = requests.get(f"{self.base_url}/{url}", headers=headers)
                response.raise_for_status()
                buffer = response.content
                return gzip.decompress(buffer)
            except (requests.exceptions.RequestException, OSError) as e:
                print(f"Download error (attempt {attempt}/{self.max_retries}): {e}")
                if attempt == self.max_retries:
                    raise
                sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                print(f"Retrying in {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)


class IndexReader(ABC):
    @abstractmethod
    def __iter__(self):
        pass


class CSVIndexReader(IndexReader):
    def __init__(self, filename: str) -> None:
        self.file = open(filename, "r")
        self.reader = csv.reader(self.file, delimiter="\t")

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.reader)

    def __del__(self) -> None:
        self.file.close()


def test_can_read_index(tmp_path):
    filename = tmp_path / "test.csv"
    index = "0,100,22,165)/ 20240722120756	cdx-00000.gz	0	188224	1\n\
101,141,199,66)/robots.txt 20240714155331	cdx-00000.gz	188224	178351	2\n\
104,223,1,100)/ 20240714230020	cdx-00000.gz	366575	178055	3"
    filename.write_text(index)
    reader = CSVIndexReader(filename)
    assert list(reader) == [
        ["0,100,22,165)/ 20240722120756", "cdx-00000.gz", "0", "188224", "1"],
        [
            "101,141,199,66)/robots.txt 20240714155331",
            "cdx-00000.gz",
            "188224",
            "178351",
            "2",
        ],
        ["104,223,1,100)/ 20240714230020", "cdx-00000.gz", "366575", "178055", "3"],
    ]
