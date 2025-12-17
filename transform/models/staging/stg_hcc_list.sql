select
  id,
  mbr_id,
  eff_date,
  exp_date,
  metal,
  hios,
  csr,
  dob,
  sex,
  state,
  ratingarea,
  market,
  risk_score,
  risk_score_no_demog,
  catastrophic_risk_score,
  bronze_risk_score,
  silver_risk_score,
  gold_risk_score,
  platinum_risk_score
from {{ source('edge', 'hcc_list') }}

