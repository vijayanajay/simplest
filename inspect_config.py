import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def inspect_strategy_config():
    """Inspect the StrategyConfig class and its requirements."""
    try:
        from src.meqsap.config import StrategyConfig
        
        print(f"StrategyConfig class found: {StrategyConfig}")
        print("\nFields and types:")
        
        # Inspect the class fields/annotations
        for field_name, field_type in StrategyConfig.__annotations__.items():
            print(f"  {field_name}: {field_type}")
        
        # Try creating an instance
        print("\nAttempting to create a minimal valid instance...")
        
        # First try with keyword arguments based on the annotations
        try:
            fields = list(StrategyConfig.__annotations__.keys())
            
            # Create a minimal dict of required arguments
            kwargs = {field: "test" for field in fields}
            
            # For special types, provide more appropriate values
            if "params" in kwargs:
                kwargs["params"] = {}
                
            instance = StrategyConfig(**kwargs)
            print(f"Success! Created instance: {instance}")
        except Exception as e:
            print(f"Failed with kwargs: {str(e)}")
            
            # Try with different field names
            print("\nTrying alternate field names...")
            alternate_kwargs = {
                "name": "TestStrategy",
                "strategy_name": "TestStrategy",
                "strategy_type": "TestStrategy",
                "params": {}
            }
            
            for key, value in alternate_kwargs.items():
                try:
                    instance = StrategyConfig(**{key: value})
                    print(f"Field '{key}' worked!")
                except Exception as e:
                    print(f"Field '{key}' failed: {str(e)}")
        
        return "Inspection complete"
    
    except ImportError as e:
        print(f"Import error: {str(e)}")
        return "Import failed"
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return "Inspection failed"

if __name__ == "__main__":
    print("Starting StrategyConfig inspection...")
    result = inspect_strategy_config()
    print(f"\nResult: {result}")
