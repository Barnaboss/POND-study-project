#foreach($line in Get-Content "infeasible_remaining.txt") { py strongPONDsolver.py "benchmarks-pond\$line" "infeasible-nocrn-30.log" 30 NOOUT NOOUT cro cra pfs pss }
foreach($line in Get-Content "first-resp.txt") { py strongPONDsolver.py "benchmarks-pond\$line" "first-resp-3h.log" 180 }
