#!/usr/bin/env python3
"""
Llama 3.3 70B Transformer using MLX (Apple Silicon Native)

MLX is Apple's framework optimized for Apple Silicon with unified memory.
This implementation provides an alternative to llama.cpp with potentially
better Metal integration.

Requirements:
    pip install mlx mlx-lm transformers

Note: MLX requires a quantized model that fits in unified memory.
For 16GB RAM, you'll need 4-bit or lower quantization.

Reference: https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct
"""

import sys
from typing import Generator, Optional


def check_mlx():
    """Check if MLX is available."""
    try:
        import mlx.core as mx
        import mlx_lm
        return True
    except ImportError:
        return False


class MLXLlamaTransformer:
    """
    MLX-based Llama 3.3 70B transformer for Apple Silicon.
    
    Uses MLX's unified memory architecture for efficient processing.
    """
    
    # Available MLX quantized models
    MODELS = {
        "4bit": {
            "repo": "mlx-community/Llama-3.3-70B-Instruct-4bit",
            "size_gb": 38,
            "quality": "Good quality, 4-bit quantization",
        },
        "8bit": {
            "repo": "mlx-community/Llama-3.3-70B-Instruct-8bit",
            "size_gb": 70,
            "quality": "High quality, requires 64GB+ RAM",
        },
        "3bit": {
            "repo": "mlx-community/Llama-3.3-70B-Instruct-3bit",
            "size_gb": 28,
            "quality": "Lower quality, fits 32GB RAM",
        },
    }
    
    def __init__(
        self,
        model_name: str = "4bit",
        max_tokens: int = 2048,
        verbose: bool = True,
    ):
        """
        Initialize MLX Llama transformer.
        
        Args:
            model_name: Model variant (4bit, 8bit, 3bit)
            max_tokens: Maximum context length
            verbose: Print loading progress
        """
        if not check_mlx():
            print("Error: MLX not installed.")
            print("Install with: pip install mlx mlx-lm transformers")
            sys.exit(1)
        
        import mlx.core as mx
        from mlx_lm import load, generate
        
        self.mx = mx
        self.generate_fn = generate
        self.verbose = verbose
        
        if model_name not in self.MODELS:
            raise ValueError(f"Unknown model: {model_name}. Options: {list(self.MODELS.keys())}")
        
        model_info = self.MODELS[model_name]
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"MLX Llama 3.3 70B Instruct - {model_name}")
            print(f"{'='*60}")
            print(f"Repository: {model_info['repo']}")
            print(f"Size: ~{model_info['size_gb']}GB")
            print(f"Quality: {model_info['quality']}")
            print(f"{'='*60}\n")
            
            if model_info['size_gb'] > 16:
                print("⚠️  Warning: This model may not fit in 16GB RAM!")
                print("   Consider using llama_transformer.py with GGUF models instead.")
                print("   GGUF supports streaming from disk with mmap.\n")
        
        if verbose:
            print(f"Loading model from: {model_info['repo']}")
            print("This may take several minutes on first download...")
        
        self.model, self.tokenizer = load(model_info['repo'])
        
        if verbose:
            print("\n✓ Model loaded successfully!")
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: Input text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling threshold
            
        Returns:
            Generated text
        """
        from mlx_lm import generate
        
        response = generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            temp=temperature,
            top_p=top_p,
            verbose=self.verbose,
        )
        
        return response
    
    def chat(
        self,
        messages: list[dict],
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str:
        """
        Chat completion with Llama 3.3 format.
        
        Args:
            messages: List of {"role": "user/assistant/system", "content": "..."}
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Assistant response
        """
        # Apply chat template
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        
        return self.generate(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    
    def stream_generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """
        Stream tokens as they're generated.
        
        Args:
            prompt: Input text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Yields:
            Generated tokens one at a time
        """
        from mlx_lm import stream_generate as mlx_stream
        
        for token in mlx_stream(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            temp=temperature,
        ):
            yield token


def main():
    """Example usage of MLX Llama transformer."""
    print("\n⚠️  Note: For 16GB RAM, MLX may struggle with 70B models.")
    print("   The recommended approach is llama_transformer.py with GGUF models")
    print("   which supports mmap for streaming from disk.\n")
    
    print("If you have 32GB+ unified memory, you can try:")
    print("  python mlx_transformer.py\n")
    
    # Only run if explicitly confirmed
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true", help="Confirm you have enough RAM")
    args = parser.parse_args()
    
    if not args.confirm:
        print("Run with --confirm if you have 32GB+ RAM to proceed.")
        print("For 16GB RAM, use the main llama_transformer.py instead.")
        return
    
    transformer = MLXLlamaTransformer(model_name="4bit")
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"}
    ]
    
    response = transformer.chat(messages)
    print(f"\nResponse: {response}")


if __name__ == "__main__":
    main()
