"""
Multi-model configuration and management for different AI providers
"""
import os
import openai
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Configuration for a specific model and provider"""
    provider: str
    model_name: str
    api_key: str
    base_url: str
    extra_body: Optional[Dict[str, Any]] = None
    
    def create_client(self) -> openai.OpenAI:
        """Create an OpenAI-compatible client for this model"""
        return openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def get_chat_completion_kwargs(self) -> Dict[str, Any]:
        """Get additional kwargs for chat completion requests"""
        kwargs = {}
        if self.extra_body:
            kwargs["extra_body"] = self.extra_body
        return kwargs


class ModelManager:
    """Manages multiple AI model configurations"""
    
    # Supported providers and their models
    PROVIDER_MODELS = {
        "openai": ["gpt-5"],
        "deepseek": ["deepseek-chat"],
        "moonshot": ["kimi-k2-0711-preview", "kimi-k2-thinking-turbo"],
        "zhipuai": ["glm-4.5"],
        "anthropic": ["anthropic/claude-sonnet-4"],
        "google": ["gemini-2.5-pro", "gemini-2.5-flash"],
        "volcengine": ["doubao-seed-1.6-250615", "deepseek-r1-250528", "deepseek-v3-1-250821"],
        "stepfun": ["step-3"],
        "openrouter": ["qwen/qwen3-235b-a22b-thinking-2507"]
    }
    
    def __init__(self):
        """Initialize model manager from environment variables"""
        self.configs = self._load_configurations()
    
    def _load_configurations(self) -> Dict[str, ModelConfig]:
        """Load all available model configurations from environment"""
        configs = {}
        
        for provider in self.PROVIDER_MODELS.keys():
            api_key = os.getenv(f"{provider.upper()}_API_KEY")
            base_url = os.getenv(f"{provider.upper()}_BASE_URL")
            
            if api_key and base_url:
                configs[provider] = {
                    "api_key": api_key,
                    "base_url": base_url
                }
        
        return configs
    
    def get_model_config(self, provider: str, model_name: str) -> ModelConfig:
        """Get configuration for a specific provider and model"""
        if provider not in self.configs:
            raise ValueError(f"Provider '{provider}' not configured. Available: {list(self.configs.keys())}")
        
        if model_name not in self.PROVIDER_MODELS.get(provider, []):
            available_models = self.PROVIDER_MODELS.get(provider, [])
            raise ValueError(f"Model '{model_name}' not supported for provider '{provider}'. Available: {available_models}")
        
        config_data = self.configs[provider]
        
        # Handle provider-specific extra configurations
        extra_body = None
        if provider == "openrouter":
            extra_body = {
                "provider": {
                    "order": ["novita"],
                    "allow_fallbacks": False
                }
            }
        
        return ModelConfig(
            provider=provider,
            model_name=model_name,
            api_key=config_data["api_key"],
            base_url=config_data["base_url"],
            extra_body=extra_body
        )
    
    def get_player_config(self, stone_color: str) -> ModelConfig:
        """Get model configuration for a player based on stone color"""
        if stone_color == "B":
            provider = os.getenv("BLACK_MODEL_PROVIDER", "openai")
            model_name = os.getenv("BLACK_MODEL_NAME", "gpt-5")
        elif stone_color == "W":
            provider = os.getenv("WHITE_MODEL_PROVIDER", "deepseek")
            model_name = os.getenv("WHITE_MODEL_NAME", "deepseek-chat")
        else:
            raise ValueError(f"Invalid stone color: {stone_color}. Must be 'B' or 'W'")
        
        return self.get_model_config(provider, model_name)
    
    def list_available_providers(self) -> list:
        """List all configured providers"""
        return list(self.configs.keys())
    
    def list_available_models(self, provider: str) -> list:
        """List all available models for a provider"""
        return self.PROVIDER_MODELS.get(provider, [])
    
    def find_provider_for_model(self, model_name: str) -> str:
        """Find the provider for a given model name"""
        for provider, models in self.PROVIDER_MODELS.items():
            if model_name in models:
                return provider
        raise ValueError(f"Model '{model_name}' not found in any provider")
    
    def get_model_config_by_name(self, model_name: str) -> ModelConfig:
        """Get model configuration by model name (automatically finds provider)"""
        provider = self.find_provider_for_model(model_name)
        return self.get_model_config(provider, model_name)
    
    def list_all_available_models(self) -> list:
        """List all available model names across all providers"""
        all_models = []
        for models in self.PROVIDER_MODELS.values():
            all_models.extend(models)
        return sorted(all_models)
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration and return status"""
        status = {
            "configured_providers": list(self.configs.keys()),
            "total_providers": len(self.PROVIDER_MODELS),
            "black_player": {
                "provider": os.getenv("BLACK_MODEL_PROVIDER", "openai"),
                "model": os.getenv("BLACK_MODEL_NAME", "gpt-5"),
                "configured": False
            },
            "white_player": {
                "provider": os.getenv("WHITE_MODEL_PROVIDER", "deepseek"), 
                "model": os.getenv("WHITE_MODEL_NAME", "deepseek-chat"),
                "configured": False
            }
        }
        
        # Check if black player is configured
        try:
            self.get_player_config("B")
            status["black_player"]["configured"] = True
        except ValueError:
            pass
        
        # Check if white player is configured  
        try:
            self.get_player_config("W")
            status["white_player"]["configured"] = True
        except ValueError:
            pass
        
        return status


def get_model_display_name(provider: str, model_name: str) -> str:
    """Get a human-readable display name for a model"""
    display_names = {
        "openai": {
            "gpt-5": "GPT-5"
        },
        "deepseek": {
            "deepseek-chat": "DeepSeek V3.1"
        },
        "moonshot": {
            "kimi-k2-0711-preview": "Kimi K2"
        },
        "zhipuai": {
            "glm-4.5": "GLM-4.5"
        },
        "anthropic": {
            "anthropic/claude-sonnet-4": "Claude Sonnet 4"
        },
        "google": {
            "gemini-2.5-pro": "Gemini 2.5 Pro",
            "gemini-2.5-flash": "Gemini 2.5 Flash"
        },
        "volcengine": {
            "doubao-seed-1.6-250615": "Doubao Seed 1.6",
            "deepseek-r1-250528": "DeepSeek R1 (Volce)",
            "deepseek-v3-1-250821": "DeepSeek V3.1 (Volce)"
        },
        "stepfun": {
            "step-3": "Step-3"
        },
        "openrouter": {
            "qwen/qwen3-235b-a22b-thinking-2507": "Qwen3 235B Thinking"
        }
    }
    
    return display_names.get(provider, {}).get(model_name, f"{provider}/{model_name}")
