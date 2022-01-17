import requests
import os
import random
from linereader import copen
import csv

# This is used for proper download of the files
heads = {'Host': 'www.sec.gov', 'Connection': 'close',
         'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest',
         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                       ' Chrome/80.0.3987.163 Safari/537.36',
         }


def create_dir(dir_name: str):
    """Function used to create directory in the current working directory
    it takes the name of the new directory as input"""
    dir_ = dir_name
    p_dir = os.getcwd()
    path = os.path.join(p_dir, dir_)
    try:
        os.mkdir(path)
    except OSError as error:
        print(error)
    return path


def download_file(url_: str, path: str, name_: str):
    """Function to download any file type, it takes the url, download path and file name as
    input and download the file of the given url to the given path"""
    r = requests.get(url_, headers=heads)
    with open(os.path.join(path, name_), 'wb') as f:
        f.write(r.content)


def download_master_files(start_year, end_year):
    """Function used to download all the required master.idx files.
    It gets the start and end year as input and download the master.idx file for
    each quarter of all the years in the given range"""
    download_path = create_dir('master')  # creates folder to store the master.idx filess
    for year in range(start_year, end_year + 1):
        for qtr in range(1, 5):  # downloads the master file of all quarter
            current_url = f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{qtr}/master.idx"
            # calls the above created download_file function and downloads the files
            download_file(current_url, download_path, f'{year}_{qtr}_master.idx')


# downloads all the master.idx files from 1995 to 2021
download_master_files(1995, 2021)


def clean_master_files():
    """Loops through the master directory and Cleans the master files.
    Removes the first few lines"""
    directory = 'master'
    for file in os.listdir(directory):
        f = os.path.join(directory, file)  # gets the file in the master folder
        if os.path.isfile(f):  # if it's a file the first lines are removed
            with open(f, 'r') as f_in:
                data = f_in.read().splitlines(True)
            with open(f, 'w') as f_out:
                f_out.writelines(data[9:])


def download_8ks():
    """Loops through all the master files and download 10 random 8-K filings into the 8-k filings folder.
    Also creates a csv file and adds the CIK and dates of the filings to it"""
    clean_master_files()  # cleans the master files first
    download_path = create_dir('8-K_Filings')  # creates a directory to store the 8-k filings
    directory = 'master'

    # creates the csv file that's comma seperated
    out = csv.writer(open("CIK_date.csv", "w", newline=""), delimiter=',', quoting=csv.QUOTE_ALL)
    for file in os.listdir(directory):  # loops through the master directory
        f = os.path.join(directory, file)  # gets the file
        if os.path.isfile(f):
            file = copen(f)  # opens the file in a special way for it to be read easily. (from linereader package)
            lines = file.count('\n')   # counts the number of lines
            for i in range(10):
                random_line = file.getline(random.randint(2, lines))  # gets a random line from the file
                # gets the CIK and date from the line and stores them in  a list to be added to the csv file
                data = [random_line.split('|')[0], random_line.split('|')[3]]
                # writes the above data to the csv
                out.writerow(data)
                # extract to link to download the 8-K filings
                random_line = random_line.split('|')[-1].strip()
                current_url = f"https://www.sec.gov/Archives/{random_line}"
                download_file(current_url, download_path, random_line.split('/')[-1])


# downloads the 8-K filings
download_8ks()
