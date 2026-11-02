"""Handwritten tiny dense-layout fixture, ZERO values; not pretrained weights."""
CONFIG = dict(model_type='qwen3', architectures=['Qwen3ForCausalLM'], hidden_size=2,
              vocab_size=3, intermediate_size=4, num_hidden_layers=1,
              num_attention_heads=1, num_key_value_heads=1, head_dim=2,
              attention_bias=False, tie_word_embeddings=False)
SHAPES = {
    'model.embed_tokens.weight': (3, 2), 'model.norm.weight': (2,), 'lm_head.weight': (3, 2),
    'model.layers.0.input_layernorm.weight': (2,), 'model.layers.0.post_attention_layernorm.weight': (2,),
    'model.layers.0.self_attn.q_proj.weight': (2, 2), 'model.layers.0.self_attn.k_proj.weight': (2, 2),
    'model.layers.0.self_attn.v_proj.weight': (2, 2), 'model.layers.0.self_attn.o_proj.weight': (2, 2),
    'model.layers.0.self_attn.q_norm.weight': (2,), 'model.layers.0.self_attn.k_norm.weight': (2,),
    'model.layers.0.mlp.gate_proj.weight': (4, 2), 'model.layers.0.mlp.up_proj.weight': (4, 2),
    'model.layers.0.mlp.down_proj.weight': (2, 4),
}
