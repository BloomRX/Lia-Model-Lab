"""Exact dense Qwen3.5-0.8B profile, derived from official config and architecture.

No Torch import or tensor allocation. The only production profile is config at
Qwen/Qwen3.5-0.8B revision 2fc06364715b967f1860aea9cf38778875588b17.
MTP is included in the inventory/budget, never silently discarded.
"""
import hashlib
from .io import canonical

MODEL_REVISION = '2fc06364715b967f1860aea9cf38778875588b17'
CONFIG_SHA256 = '7755fa7f94c366b1bc8db482e9a3c56721093ece9ed6a8234560e443b13168d1'


def layout(config):
    """Architecture equations; production callers first require the exact profile.

    Also exercised independently with scaled synthetic fixtures in tests.
    """
    t, v = config['text_config'], config['vision_config']
    h, vocab, mid = t['hidden_size'], t['vocab_size'], t['intermediate_size']
    heads, kv, d = t['num_attention_heads'], t['num_key_value_heads'], t['head_dim']
    shapes = {'model.language_model.embed_tokens.weight': (vocab, h),
              'model.language_model.norm.weight': (h,)}
    def decoder(prefix, kind):
        for key, shape in {'input_layernorm.weight':(h,), 'post_attention_layernorm.weight':(h,),
            'mlp.gate_proj.weight':(mid,h), 'mlp.up_proj.weight':(mid,h), 'mlp.down_proj.weight':(h,mid)}.items():
            shapes[prefix+key] = shape
        if kind == 'full_attention':
            values = {'q_proj.weight':(heads*d*2,h), 'k_proj.weight':(kv*d,h),
                'v_proj.weight':(kv*d,h), 'o_proj.weight':(h,heads*d), 'q_norm.weight':(d,), 'k_norm.weight':(d,)}
            shapes.update({prefix+'self_attn.'+k:s for k,s in values.items()})
        else:
            kdim = t['linear_key_head_dim']*t['linear_num_key_heads']
            vdim = t['linear_value_head_dim']*t['linear_num_value_heads']
            conv = kdim*2+vdim
            values = {'A_log':(t['linear_num_value_heads'],), 'dt_bias':(t['linear_num_value_heads'],),
                'conv1d.weight':(conv,1,t['linear_conv_kernel_dim']), 'in_proj_qkv.weight':(conv,h),
                'in_proj_z.weight':(vdim,h), 'in_proj_b.weight':(t['linear_num_value_heads'],h),
                'in_proj_a.weight':(t['linear_num_value_heads'],h), 'norm.weight':(t['linear_value_head_dim'],),
                'out_proj.weight':(h,vdim)}
            shapes.update({prefix+'linear_attn.'+k:s for k,s in values.items()})
    for i, kind in enumerate(t['layer_types']):
        decoder(f'model.language_model.layers.{i}.', kind)
    vh, vmid = v['hidden_size'], v['intermediate_size']
    shapes.update({'model.visual.patch_embed.proj.weight':(vh,v['in_channels'],v['temporal_patch_size'],v['patch_size'],v['patch_size']),
        'model.visual.patch_embed.proj.bias':(vh,), 'model.visual.pos_embed.weight':(v['num_position_embeddings'],vh)})
    for i in range(v['depth']):
        p=f'model.visual.blocks.{i}.'
        values = {'norm1.weight':(vh,), 'norm1.bias':(vh,), 'norm2.weight':(vh,), 'norm2.bias':(vh,),
            'attn.qkv.weight':(vh*3,vh), 'attn.qkv.bias':(vh*3,), 'attn.proj.weight':(vh,vh), 'attn.proj.bias':(vh,),
            'mlp.linear_fc1.weight':(vmid,vh), 'mlp.linear_fc1.bias':(vmid,),
            'mlp.linear_fc2.weight':(vh,vmid), 'mlp.linear_fc2.bias':(vh,)}
        shapes.update({p+k:s for k,s in values.items()})
    merged = vh*v['spatial_merge_size']**2
    values = {'norm.weight':(vh,), 'norm.bias':(vh,), 'linear_fc1.weight':(merged,merged),
        'linear_fc1.bias':(merged,), 'linear_fc2.weight':(v['out_hidden_size'],merged), 'linear_fc2.bias':(v['out_hidden_size'],)}
    shapes.update({'model.visual.merger.'+k:s for k,s in values.items()})
    decoder('mtp.layers.0.', 'full_attention')
    shapes.update({'mtp.fc.weight':(h,h*2), 'mtp.norm.weight':(h,),
        'mtp.pre_fc_norm_embedding.weight':(h,), 'mtp.pre_fc_norm_hidden.weight':(h,)})
    return shapes


def shapes(config):
    if not isinstance(config, dict) or hashlib.sha256(canonical(config).encode()).hexdigest() != CONFIG_SHA256:
        return None
    return layout(config)


def dtype_for(name):
    return 'F32' if '.linear_attn.' in name and name.endswith(('A_log', 'norm.weight')) else 'BF16'
