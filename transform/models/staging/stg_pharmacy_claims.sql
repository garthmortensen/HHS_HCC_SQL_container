select *
from {{ source('edge', 'pharmacyclaims') }}
