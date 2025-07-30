# As of 2025-04-09, amaranth-soc#58 adding annotations to memory maps and CSRs is still not merged,
# so we monkeypatch in the proposed annotations from `4cd6f94` with some changes.

from . import amaranth_soc_memory
from . import amaranth_soc_csr_bus
