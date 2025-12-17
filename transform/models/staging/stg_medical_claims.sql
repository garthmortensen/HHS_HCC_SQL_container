select *
from {{ source('edge', 'MedicalClaims') }}
