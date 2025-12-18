select *
from {{ source('edge', 'supplemental') }}
