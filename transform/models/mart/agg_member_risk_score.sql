select
  mbr_id,
  min(eff_date) as min_eff_date,
  max(exp_date) as max_exp_date,
  max(risk_score) as risk_score,
  max(risk_score_no_demog) as risk_score_no_demog,
  max(catastrophic_risk_score) as catastrophic_risk_score,
  max(bronze_risk_score) as bronze_risk_score,
  max(silver_risk_score) as silver_risk_score,
  max(gold_risk_score) as gold_risk_score,
  max(platinum_risk_score) as platinum_risk_score
from {{ ref('stg_hcc_list') }}
group by mbr_id
