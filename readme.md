# Black Widow - Blackbox Data-Driven Web Scanning (replicated + SQL attack vector)

## Setup 
---
1. Setup python virtual enviroment
2. Install dependency form requirement.txt
3. Download and install Google Chrome driver 
4. Setup path for Google Chrome
    - `PATH=$PATH:.`

## Run the scanner
---
`python3 main.py --url http://www.example.com --single True --sql|xss True`

- `--single` No web crawling recursive
- `--sql|xss` Select the attack vectors

## Web app docker 
---
[[Docker](https://gitlab.com/kostasdrk/rescanApps/-/tree/main)