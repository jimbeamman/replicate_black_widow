# Black Widow - Blackbox Data-Driven Web Scanning (replicated + SQL attack vector)
We have created a learning repository to replicate Black Widow's black box scanning technique. In our work, we have added an SQL injection module to identify 1st and 2nd order injections, which works well on error reflection-based detections. However, further improvements are required to detect time-based or boolean-based errors.

## Setup 
1. Setup python virtual enviroment
2. Install dependency form requirement.txt
3. Download and install Google Chrome driver 
4. Setup path for Google Chrome
    - `PATH=$PATH:.`

## Run the scanner
`python3 main.py --url http://www.example.com --single True --sql|xss True`

- `--single` No web crawling recursive - check for GET method
- `--sql|xss` Select the attack vectors

## Proof of Concept for SQL injection
- `python3 test/sql_test.py`

## Web app docker 
[ReScan dockers](https://gitlab.com/kostasdrk/rescanApps/-/tree/main)