* for RES potentials, data from ENSPRESO_ref
	* exception: Belgium data from Belgian version of ESTD


* adding PV_utility and PV_rooftop + WIND_ONSHORE and WIND_OFFSHORE
	* data from danish energy agency technology catalogue, making linear regression between 2030 and 2040 (https://ens.dk/en/our-services/projections-and-models/technology-data/technology-data-generation-electricity-and)
		* no data in this db for CSP, TIDAL and HYDRO techs
		* sparse data on WAVE, not updated
	* put into €_2015 -> see eq 43 of ES doc
		with CEPCI_2020 = 596.2 (https://toweringskills.com/financial-analysis/cost-indices/)
		with CEPCI_2015 = 556.3
		USD_2020/€_2020 = 1.14 (https://www.macrotrends.net/2548/euro-dollar-exchange-rate-historical-chart
		€_2015/USD_2015 = 1/1.11
		-> conversion factor = 1.14*556.3/596.2*1/1.11 = 0.958294