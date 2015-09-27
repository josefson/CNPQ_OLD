# CNPQ
Captcha Negated by Python reQuests - For the CNPq lattes database.

The Lattes database was intended to be of public access, however it's managers 2 captchas in the way of getting an open data. With that problem in mind, this software was created to download the curriculums in a xml format one by one in an automated way.
The problem was broken into 3 parts, which are necessary for getting the final object: a xml file.
1. Through a blank search we get all the results existent. Then we will iterate over its pagination getting what i call of short_ids inside the hmtl attributes.
2. Once we have the short_ids, we will iterate over them requesting the curriculum visualization. This will result in a captcha page, which the software will solve, get the visualzation page and scrap the long_id out of its html attributes.
3. Only with a long_id we can get the downlaod links for each curriculum. Here a new captcha will be presented and the software will take care of it to.

## Requirements
Python 2.7.X

Python libraries necessary:
* requests
* BeautifulSoup
* lxml
* Pillow
* fake-useragent

## Installation
### OSX
```
pip install requests beautifulsoup4 lxml Pillow fake-useragent
```
### Ubuntu
```
sudo apt-get install python-dev python-pip python-lxml gcc libjpeg-dev zlib1g-dev
sudo pip install requests beautifulsoup4 faker-useragent
sudo pip install Pillow -U
```

## Usage
Once all the pre-requirements are met just run it and wait:
1st We scrap all shortIDs saving them in the output file.
```
usage: search_short_ids.py [-h] -w CORES -o SHORT_ID_FILE

optional arguments:
  -h, --help            show this help message and exit
  -w CORES, --worker CORES
                        number of workers to split the task.
  -o SHORT_ID_FILE, --output SHORT_ID_FILE
                        ShortIDs output file.

python search_short_ids.py -w 2 -o short_ids.csv
Total of registers: 4315593
Process-1- 2015-08-24 20:07:20
Process-2- 2015-08-24 20:07:20
Process-1- Scrapping from 0 to 1000 registers
Process-2- Scrapping from 2158000 to 2159000 registers
Process-2- Scrapping from 2159000 to 2160000 registers
Process-1- Scrapping from 1000 to 2000 registers
Process-2- Scrapping from 2160000 to 2161000 registers
Process-1- Scrapping from 2000 to 3000 registers
...
```
Then longid_download.py -w WORKERS -i SHORT_ID_FILE -o LONG_ID_FILE
```
python longid_download.py -h/--help for more information
usage: longid_download.py [-h] -w CORES -i SHORT_ID_FILE -o LONG_ID_FILE [-v]
optional arguments:
    -h, --help          show this help message and exit
    -w CORES, --worker CORES
                        Required: Number of workers to split the task into
                        processes. This is done in order to get a higher cpu
                        time.
    -i SHORT_ID_FILE, --input SHORT_ID_FILE
                        Required: A input file filled with short_ids separated
                        by new-line-characters.
    -o LONG_ID_FILE, --output LONG_ID_FILE
                        Required: A output file to be writen with long_idsa.
                        Since long_ids are the Primary Keys, those could be
                        useful in the future.
    -v, --verbose       Optional: Allow you to see the scrap/download
                        progress.
    -n, --nice          Optional: This sets the workers with the highest 
                        niceness/cpu-priiority possible.

python longid_download.py -v -w 2 -i my_shortID_file.csv -o my_longID_output.csv
Process-1-[2/50]=> short_id: K4130902J7  |  long_id: 2253022128647589
Process-2-[2/50]=> short_id: K4133392U6  |  long_id: 0449582690670596
Process-1-[3/50]=> short_id: K4130301E5  |  long_id: 7397201484989375
Process-2-[3/50]=> short_id: K4131812T0  |  long_id: 2222910728338238
Process-1-[4/50]=> short_id: K4138503E6  |  long_id: 1156552473591486
...
see zips in xmls folder
```

=======
python longid_download.py -h/--help for more information
usage: longid_download.py [-h] -w CORES -i SHORT_ID_FILE -o LONG_ID_FILE [-v]
optional arguments:
    -h, --help          show this help message and exit
    -w CORES, --worker CORES
                        Required: Number of workers to split the task into
                        processes. This is done in order to get a higher cpu
                        time.
    -i SHORT_ID_FILE, --input SHORT_ID_FILE
                        Required: A input file filled with short_ids separated
                        by new-line-characters.
    -o LONG_ID_FILE, --output LONG_ID_FILE
                        Required: A output file to be writen with long_idsa.
                        Since long_ids are the Primary Keys, those could be
                        useful in the future.
    -v, --verbose       Optional: Allow you to see the scrap/download
                        progress.
    -n, --nice          Optional: This sets the workers with the highest 
                        niceness/cpu-priiority possible.

python longid_download.py -v -w 2 -i my_shortID_file.csv -o my_longID_output.csv
Process-1-[2/50]=> short_id: K4130902J7  |  long_id: 2253022128647589
Process-2-[2/50]=> short_id: K4133392U6  |  long_id: 0449582690670596
Process-1-[3/50]=> short_id: K4130301E5  |  long_id: 7397201484989375
Process-2-[3/50]=> short_id: K4131812T0  |  long_id: 2222910728338238
Process-1-[4/50]=> short_id: K4138503E6  |  long_id: 1156552473591486
...
see zips in xmls folder
```

## Nice
With performance in mind, code was added in order to set maximum cpu priority
to the workers. Unfortunatly, it requires the script to be runned with sudo
privileges. It uses the nice() feature of UNIX-like systems in order to achieve that.

Now, because it can be a sensitive question, a flag (-n/--nice) was added to let
the user decide what he/she wants. Now, bare in mind there is a log.txt file 
which if once created with sudo privileges, it will break next runs without sudo. 
Appart from that everything seems ok.
Also, you should feel free to inspect the code and decide for yourself if you 
trust it or not, since i am not to be held responsible for whatever may occour 
in your enviroment.

## To Do
* Find a way to set niceness without sudo privileges.
* Port to Windows.

## Thanks
Special thanks to my friend Bruno Duarte that guided me in the way how images work.

### Sponsors

No sponsors yet! Will you be the first?

[![PayPayl donate button](https://img.shields.io/badge/paypal-donate-yellow.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=WA7DVSWHPZLBE "Donate to this project using Paypal")


## To Do
* Do the download step with the requests library if possible.


## LICENSE
Copyright (c) 2015 Josefson Fraga Souza

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
