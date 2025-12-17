select *
from {{ source('edge', 'PharmacyClaims') }}
