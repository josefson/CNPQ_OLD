# CNPQ
Captcha Negated by Python reQuests - For the CNPq lattes database.

The Lattes database was intended to be of public access, however it's managers 2 captchas in the way of getting an open data. With that problem in mind, this software was created to download the curriculums in a xml format one by one in an automated way.
The problem was broken into 3 parts, which are necessary for getting the final object: a xml file.
1. Through a blank search we get all the results existent. Then we will iterate over its pagination getting what i call of short_ids inside the hmtl attributes.
2. Once we have the short_ids, we will iterate over them requesting the curriculum visualization. This will result in a captcha page, which the software will solve, get the visualzation page and scrap the long_id out of its html attributes.
3. Only with a long_id we can get the downlaod links for each curriculum. Here a new captcha will be presented and the software will take care of it to.

## Requirements
Python 2.7.X, Mozilla Firefox

Install python libraries by using the requirements.txt
```
pip install -r requirements.txt
```

## How to use it
Open the search_short_ids.py and the longid_download.py and set the proper parameters at its ifmain section at the bottom of the file. For example, you could change  the core numbers, or the short_id_file.
```
if __name__ == '__main__':
    CORES = 2  # Number of cores
    SHORT_ID_FILE = 'data.csv'  # Input file with short_ids
    short_id_list = short_ids(SHORT_ID_FILE)
    splited_lists = split_list(short_id_list[0:100], CORES)
    for splited_list in range(len(splited_lists)):
        temp = (splited_lists[splited_list],)
        process = Process(target=worker, args=temp)
        process.start()
```
Once you think all the pre-requirements are met just run it and wait:
```
python search_short_ids.py
431550                     Total of results
2015-08-24 15:04:24        process1 Starting at
getting 2158000-2159000... process1
2015-08-24 15:04:24        process2 Starting at
getting 0-1000...          process2
getting 1000-2000...       ...
getting 2159000-2160000... ...
```
or
```
python longid_download.py
Process-1-[2/50]=> short_id: K4130902J7  |  long_id: 2253022128647589
Process-2-[2/50]=> short_id: K4133392U6  |  long_id: 0449582690670596
Process-1-[3/50]=> short_id: K4130301E5  |  long_id: 7397201484989375
Process-2-[3/50]=> short_id: K4131812T0  |  long_id: 2222910728338238
Process-1-[4/50]=> short_id: K4138503E6  |  long_id: 1156552473591486
...
see zips in project folder
```

##To Do
* Pass arguments through commandline.
* Do the download step with the requests library if possible.
* Improve the output of the search_short_ids.py script (multiprocessed output).
* Download zips to a download folder.


Copyright (c) <2015> <Josefson Fraga Souza>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
