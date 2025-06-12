# BuyAndHoldParams implementation for Story 8: Baseline Comparison & Advanced Reporting Framework
# This file implements the parameter class for Buy & Hold strategy to complete baseline functionality

from pydantic import BaseModel
from .config import BaseStrategyParams

class BuyAndHoldParams(BaseStrategyParams):
    """Parameters for the Buy & Hold strategy.
    
    Buy & Hold strategy requires no parameters - it simply buys on the first day
    and holds forever. This class serves as a placeholder to maintain consistency
    with the strategy parameter framework.
    """
    
    def get_required_data_coverage_bars(self) -> int:
        """Return minimum data requirement for Buy & Hold strategy.
        
        Buy & Hold only needs one day of data to execute, but we return 1
        to satisfy the abstract method requirement.
        """
        return 1