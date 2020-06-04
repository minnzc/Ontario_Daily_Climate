*This do file cleans 2019 population estimates by 2016 Census subdivisions

*Author:       Minnie Cui
*Date written: 2 June 2020
*Last updated: ---

********************************************************************************
*SET PROJECT DIRECTORY 
global MAIN "C:\Users\minni\Research\COVID_ON\AVG_CLIMATE\DATA\subdivisions_pop"
cd "$MAIN"

*SET FILE NAME 
global INPUT "17100142.csv"

********************************************************************************
*Import data
import delimited using $INPUT, varn(1) bindq(strict) encoding(utf-8) clear

*Only keep data from 2019
drop if ref_date < 2019

*Only keep Ontario data
keep if substr(dguid, strpos(dguid, "5") + 1, 2) == "35"

*Generate Census divisions and subdivisions code
gen cduid = substr(dguid, strpos(dguid, "5") + 1, 4)
gen csduid = substr(dguid, strpos(dguid, "5") + 1, .)
destring *uid, replace

*Keep only relevant variables
rename geo csdname
rename value pop
keep cd* csd* pop
order cd* csd*
label variable pop ""
label variable csdname "" 

*Save
export delimited using subdivisions_pop.csv, q replace
