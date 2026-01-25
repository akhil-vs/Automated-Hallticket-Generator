"""
Configuration file loader for school details.
Supports JSON and YAML configuration files.
"""
import json
from pathlib import Path
from typing import Optional
from config import SchoolConfig


def load_config_from_file(config_path: str) -> Optional[SchoolConfig]:
    """
    Load school configuration from a JSON or YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        SchoolConfig object if successful, None otherwise
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        return None
    
    try:
        if config_file.suffix.lower() == '.json':
            with open(config_file, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            return SchoolConfig.from_dict(config_dict)
        
        elif config_file.suffix.lower() in ['.yaml', '.yml']:
            try:
                import yaml
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_dict = yaml.safe_load(f)
                return SchoolConfig.from_dict(config_dict)
            except ImportError:
                raise ImportError("PyYAML is required for YAML config files. Install with: pip install pyyaml")
        
        else:
            # Try JSON first
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                return SchoolConfig.from_dict(config_dict)
            except json.JSONDecodeError:
                # Try YAML
                try:
                    import yaml
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_dict = yaml.safe_load(f)
                    return SchoolConfig.from_dict(config_dict)
                except ImportError:
                    raise ImportError("PyYAML is required for YAML config files. Install with: pip install pyyaml")
    
    except Exception as e:
        raise ValueError(f"Error loading config file: {str(e)}")


def create_sample_config(output_path: str = "school_config.json"):
    """
    Create a sample configuration file.
    
    Args:
        output_path: Path where to save the sample config file
    """
    sample_config = {
        "school_name": "Your School Name",
        "school_address": "123 School Street, City, State, ZIP",
        "logo_path": "assets/school_logo.png",
        "signature_path": "assets/principal_signature.png"
    }
    
    config_file = Path(output_path)
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=2, ensure_ascii=False)
    
    print(f"Sample configuration file created: {config_file}")
    print("Edit this file with your school details and use --config-file option")
