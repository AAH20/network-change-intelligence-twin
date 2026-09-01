package netchange.change

default allow := false

allow if {
  input.twin.all_intents_pass == true
  input.failures.all_scenarios_pass == true
  input.change.reviewed == true
  input.change.rollback_tested == true
  input.canary.blast_radius_pct <= 5
  input.evidence.complete == true
}

deny contains "Network intent regression" if input.twin.all_intents_pass != true
deny contains "Failure replay regression" if input.failures.all_scenarios_pass != true
deny contains "Missing rollback evidence" if input.change.rollback_tested != true
