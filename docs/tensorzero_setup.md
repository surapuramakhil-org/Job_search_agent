# TensorZero Gateway Configuration Guide

## Overview
TensorZero provides a unified gateway for connecting to various LLM providers. It handles authentication, rate limiting, and model management.

For official TensorZero documentation, see:  
[TensorZero Documentation](https://www.tensorzero.com/docs)

## Configuration Steps

1. Edit the configuration file at `tensorzero_config/tensorzero.toml`:

```toml
# Define a function for your LLM tasks
[functions.generate_response]
type = "chat"  # The type of task

# Define model variants for this function
[functions.generate_response.variants.default]
type = "chat_completion"
model = "openai::gpt-4o-mini"  # Format: provider::model-name
```

2. Supported Model Providers:
   - OpenAI (format: `openai::model-name`)
   - Anthropic (format: `anthropic::model-name`)
   - Google (format: `google::model-name`)
   - Local models (format: `local::model-name`)

3. Defining Multiple Variants:
```toml
[functions.generate_response.variants.fast]
type = "chat_completion"
model = "anthropic::claude-instant"
max_tokens = 256

[functions.generate_response.variants.quality]
type = "chat_completion" 
model = "anthropic::claude-2"
max_tokens = 1024
```

4. Additional Configuration Options:
   - `temperature`: Controls randomness (0-1)
   - `max_tokens`: Maximum response length
   - `top_p`: Nucleus sampling threshold

## API Key Configuration in Docker

Set your provider API keys in the Docker Compose environment:

```yaml
# docker-compose-tensorzero.yml
services:
  tensorzero:
    environment:
      # For OpenAI
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      
      # For Anthropic  
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      
      # For Google
      GOOGLE_API_KEY: ${GOOGLE_API_KEY}
```

Add these to your `.env` file:
```bash
# .env
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key  
GOOGLE_API_KEY=your_google_key
```

## Migrating from Direct LLM Configuration  
1. Remove old LLM settings from:
   - `config.py` (LLM_MODEL_TYPE, LLM_MODEL, LLM_API_URL)
   - `secrets.yaml` (llm_api_key)

2. Convert your existing configuration to TensorZero format:
   - Old: `LLM_MODEL_TYPE = "openai"` → New: `model = "openai::gpt-4"`
   - Old: `LLM_MODEL_TYPE = "anthropic"` → New: `model = "anthropic::claude-2"`

3. Test your new configuration with existing workflows
