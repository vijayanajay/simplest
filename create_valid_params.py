import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def create_valid_params():
    """Attempt to create valid strategy parameters."""
    try:
        from src.meqsap.config import StrategyConfig, MovingAverageCrossoverParams
        
        print("Testing MovingAverageCrossoverParams creation...")
        
        # Attempt to create valid MovingAverageCrossoverParams
        try:
            ma_params = MovingAverageCrossoverParams(
                fast_ma=5,
                slow_ma=20,
                stop_loss=0.05,
                take_profit=0.1,
                trailing_stop=0.02,
                position_size=1.0
            )
            print(f"MovingAverageCrossoverParams created: {ma_params}")
        except Exception as e:
            print(f"MovingAverageCrossoverParams creation failed: {str(e)}")
            
            # Try with minimal params
            try:
                print("Trying minimal params...")
                ma_params = MovingAverageCrossoverParams()
                print(f"Minimal params worked: {ma_params}")
            except Exception as e:
                print(f"Minimal params failed: {str(e)}")
                
                # Get field info
                print("\nField information:")
                for field, type_hint in MovingAverageCrossoverParams.__annotations__.items():
                    print(f"  {field}: {type_hint}")
        
        print("\nTesting StrategyConfig creation...")
        
        # Try different combinations for StrategyConfig
        param_combinations = [
            {"name": "MovingAverageCrossover", "params": ma_params if 'ma_params' in locals() else {}},
            {"strategy_name": "MovingAverageCrossover", "params": ma_params if 'ma_params' in locals() else {}},
            {"type": "MovingAverageCrossover", "params": ma_params if 'ma_params' in locals() else {}}
        ]
        
        for i, params in enumerate(param_combinations):
            try:
                print(f"\nAttempt {i+1} with params: {params}")
                config = StrategyConfig(**params)
                print(f"Success! StrategyConfig created: {config}")
                
                # Print the actual attributes
                print("Attributes:")
                for attr in dir(config):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(config, attr)
                            if not callable(value):
                                print(f"  {attr}: {value}")
                        except Exception:
                            pass
                
                return config
            except Exception as e:
                print(f"Failed: {str(e)}")
        
        return "All attempts failed"
        
    except ImportError as e:
        print(f"Import error: {str(e)}")
        return "Import failed"
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return "Creation failed"

if __name__ == "__main__":
    print("Starting parameter creation test...")
    result = create_valid_params()
    print(f"\nFinal result: {result}")
