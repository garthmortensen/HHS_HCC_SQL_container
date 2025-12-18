select *
from {{ source('edge', 'enrollment') }}
