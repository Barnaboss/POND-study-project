$options_list = @(
	'cro cra pfs pss'
	'crn     pfs pss'
	'cro     pfs pss'
	'cra     pfs pss'
	'pfs pss'
	'cro cra pfs'
	'cro cra pss'
	'cro cra'
)

foreach ( $option in $options_list ) { py strongPONDsolver.py "benchmarks-pond\fr-p_1_1.sas" "fr11-iter-options.log" 30 NOOUT NOOUT $option }
