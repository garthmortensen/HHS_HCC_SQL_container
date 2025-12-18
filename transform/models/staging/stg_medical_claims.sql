select *
from {{ source('edge', 'medicalclaims') }}
