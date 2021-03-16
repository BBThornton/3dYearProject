import json
from ftplib import FTP
import os
from os import path
from pymongoClient import dbClient
# TODO Some sort of check if a file already exists

class ftpDownloader:
    def __init__(self):
        self.URL = None
        self.file_location = None
        self.file = None
        self.output_dir = None

    def update_url(self, url):
        seperation = self.seperateURL(url)

        if seperation[0] != self.URL:
            print("Root URL changed")
            self.URL = seperation[0]
            self.connect()

        file = seperation[1].rsplit('/', 1)
        self.file_location = file[0]
        self.file = file[1]

    def update_output_dir(self, output_dir):
        self.output_dir = output_dir

    def seperateURL(self, URL):
        sections = URL.split("/", 1)
        return sections

    def connect(self):
        print("Connecting to ftp server")
        self.connection = FTP(self.URL, timeout=60)
        self.connection.login('anonymous', '')

    def download(self):
        # Restore directory to root
        self.connection.cwd("~")
        self.connection.cwd(self.file_location)
        self.connection.retrbinary("RETR " + self.file, open(os.path.join(self.output_dir, self.file), 'wb').write)

    def close(self):
        self.connection.close()


class retrieveFromTable:
    def __init__(self, jsonTable, outputDir):
        self.data = self.parseTable(jsonTable)
        self.outputDir = "./" + outputDir
        self.dbClient = dbClient()
        self.downloadProcess()
        self.dbClient.close()

    def checkExists(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def parseTable(self, jsonTable):
        try:
            exists = path.exists(jsonTable)
            with open(jsonTable, "r") as f:
                return json.loads(f.read())
        except:
            return json.loads(jsonTable)

    def downloadProcess(self):
        print("Starting Download Process for " + str(len(self.data)), "Samples")
        ftp = ftpDownloader()
        for sample in self.data:
            path = os.path.join(self.outputDir, sample['run_accession'])
            self.checkExists(path)
            ftp.update_url(sample['fastq_ftp'])
            ftp.update_output_dir(path)
            ftp.download()
            self.insertDB(sample, path)
            print("Sample", str(self.data.index(sample)), "Downloaded")
        ftp.close()

    def insertDB(self, sampleData, path):
        if sampleData['sample_alias'] != sampleData['study_accession']:
            try:
                sampleData['sample_alias'] = sampleData['sample_alias'].split('.')[1]


            except:
                print("Sample Alias of atypical type.")
                print("Sample has been discounted from the system but can be added via manual review"+
                      " or by changing the alias in the provided json file")
        sampleData['file_location'] = path

        if self.dbClient.check_doc_exists({"run_accession": sampleData['run_accession']}, "samples"):
            print("study_accession " + sampleData['run_accession'] + " already exists, ignored the additional instances")
            print("Ensure that there are no repeating instances of the same file")
        else:
            self.dbClient.insert_one(sampleData, "samples")


if __name__ == '__main__':
    ena_json_table = os.getenv('JSON_FILE')
    output_dir = os.getenv('OUTPUT_DIR')
    table = retrieveFromTable(ena_json_table, output_dir)
    # "filereport_read_run_PRJNA82111_json.txt"
    # "/data/morgan/samples"
