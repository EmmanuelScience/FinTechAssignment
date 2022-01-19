import requests
import os
import random
from linereader import copen
import csv
from bs4 import BeautifulSoup
import pandas as pd
from matplotlib import pyplot

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


def download_master_files(start_year: int, end_year: int):
    """Function used to download all the required master.idx files.
    It gets the start and end year as input and download the master.idx file for
    each quarter of all the years in the given range"""
    download_path = create_dir('master')  # creates folder to store the master.idx filess
    for year in range(start_year, end_year + 1):
        for qtr in range(1, 5):  # downloads the master file of all quarter
            current_url = f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{qtr}/master.idx"
            # calls the above created download_file function and downloads the files
            download_file(current_url, download_path, f'{year}_{qtr}_master.idx')


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
    download_path = create_dir('8-K_Filings')  # creates a directory to store the 8-k filings
    directory = 'master'
    # creates the csv file that's comma seperated
    out = csv.writer(open("CIK_date.csv", "w", newline=""), delimiter=',', quoting=csv.QUOTE_ALL)
    out.writerow(['Date', 'CIK', 'Score'])
    for file in os.listdir(directory):  # loops through the master directory
        f = os.path.join(directory, file)  # gets the file
        if os.path.isfile(f):
            file = copen(f)  # opens the file in a special way for it to be read easily. (from linereader package)
            lines = file.count('\n')  # counts the number of lines
            for i in range(10):
                random_line = file.getline(random.randint(2, lines)).strip()  # gets a random line from the file
                name = random_line.split('|')[3] + '_' + random_line.split('|')[0] + '_' + random_line.split('/')[-1]
                # print(name)
                # gets the CIK and date from the line and stores them in  a list to be added to the csv file
                data = [random_line.split('|')[3], random_line.split('|')[0], '']
                # writes the above data to the csv
                out.writerow(data)
                # extract to link to download the 8-K filings
                random_line = random_line.split('|')[-1].strip()
                current_url = f"https://www.sec.gov/Archives/{random_line}"
                download_file(current_url, download_path, name)


def remove_space(lis: list):
    return [value for value in lis if value != '']


def remove_HTML(data_set: dict):
    """This function uses the beautiful soup package to remove html tags from the 8-k filings.
    After these files have been cleaned, the strings are stored in a dictionary, and the name
    of the files are the keys.
    Note: some 8k filings can't be cleaned because they have no useful information."""
    directory = '8-K_Filings'
    for file in os.listdir(directory):  # loops through the master directory
        f = os.path.join(directory, file)  # gets the file
        if os.path.isfile(f):
            with open(f) as f_out:
                try:
                    soup = BeautifulSoup(f_out.read(), "html.parser")
                except:
                    print('error')
                word_list = list(soup.get_text().upper().split(" "))
                word_list = remove_space(word_list)
                data_set[file] = word_list


def extract_sentiment(positive: list, negative: list):
    """This function loops through  the dictionary and extracts all the words that are negative
    and positive and stores them in a list. This is done so that when checking the dictionary we
    will not have to traverse the whole thing."""
    with open('LoughranMcDonald_MasterDictionary_2020.csv', newline='', encoding='utf-8') as csv_file:
        words = csv.DictReader(csv_file, delimiter=',')
        for row in words:
            if row['Negative'] != '0':  # all rows that are not '0' are Negative
                negative.append(row['Word'])
            elif row['Positive'] != '0':  # all rows that are not '0' are Negative
                positive.append(row['Word'])


def binarySearch(arr: list, x: str):
    """This is an auxiliary binary search, that is used to check if a word would be negative or positive.
    It reduces the time complexity dramatically"""
    l = 0
    r = len(arr) - 1
    while l <= r:
        m = (l + r) // 2
        if arr[m] == x:
            return True
        elif arr[m] < x:
            l = m + 1
        else:
            r = m - 1
    return False  # If element is not found  then it will return False


def calculate_sentiment_score(data_set: dict, positive: list, negative: list):
    """This function calculates the difference between the number of positive and
    negative words and scales the differences."""
    # creates a csv file to store the CIK, Date, Sentiment score and year
    out = csv.writer(open("8-k_filings_sentiment_score.csv", "w", newline=""), delimiter=',', quoting=csv.QUOTE_ALL)
    out.writerow(['CIK', 'Date', 'Score', 'Year'])  # first column to describe the data
    for key in data_set:
        # loops through the data set dictionary, and checks all the words of a file
        # using the binarySearch
        num_neg = 0
        num_pos = 0
        for word in data_set[key]:
            if binarySearch(positive, word):
                num_pos += 1
            elif binarySearch(negative, word):
                num_neg += 1
        total_words = len(data_set[key])
        # calculates sentiment score
        sentiment_score = (num_pos - num_neg) / total_words
        # sets data and adds it to the csv file
        data = [key.split('_')[1], key.split('_')[0], sentiment_score, key[:4]]
        out.writerow(data)


def generate_descriptive_analysis():
    """Used to generate descriptive analysis.
     First drops the first two columns because they are not needed."""
    csvData = pd.read_csv("8-k_filings_sentiment_score.csv")
    csvData.drop('Date', inplace=True, axis=1)
    csvData.drop('CIK', inplace=True, axis=1)
    # use the panda package describe() function to generate this data.
    # It's grouped by the year
    descriptive_data = csvData.groupby(['Year']).describe()
    # generates a csv file that will be used to plot the time series
    descriptive_data.to_csv('descriptive_stat.csv', encoding='utf-8')
    csvData = pd.read_csv("descriptive_stat.csv")
    csvData.drop([0, 1], inplace=True, axis=0)  # drops the first rows, not useful
    # generates data to plot the series
    csvData.to_csv('time_series_plot.csv', encoding='utf-8', index=False,
                   header=['Year', 'count', 'mean', 'std', 'var', 'median', ' 50%', '75%', 'max'])


def plot_time_series():
    """plots the time series"""
    series = pd.read_csv('time_series_plot.csv', header=0, index_col=0, usecols=[0, 2])
    pyplot.plot(series)
    pyplot.show()
    # pyplot.savefig('time_series.png')


def main():
    # downloads all the master.idx files from 1995 to 2021
    download_master_files(1995, 2021)
    clean_master_files()  # cleans the master files first
    # downloads the 8-K filings
    download_8ks()
    # used to store the file names and the words associated with them
    data_set = {}
    # removes the html tags from the data set
    remove_HTML(data_set)
    # variables to store positive and negative words
    negative_words = []
    positive_words = []
    extract_sentiment(positive_words, negative_words)
    calculate_sentiment_score(data_set, positive_words, negative_words)
    generate_descriptive_analysis()
    plot_time_series()


if __name__ == "__main__":
    main()
