"""Authored shape fixtures; zero tensors, not pretrained weights or persona data.

Configuration facts follow official Qwen/Qwen3.5-0.8B revision
2fc06364715b967f1860aea9cf38778875588b17; equations tested at tiny scale.
"""
from copy import deepcopy
import hashlib
import json
import math
import struct
from lia_lab.io import canonical, atomic_json
from lia_lab.qwen35_contract import layout, dtype_for


def official_config():
    return dict(architectures=['Qwen3_5ForConditionalGeneration'],model_type='qwen3_5',image_token_id=248056,
        video_token_id=248057,vision_start_token_id=248053,vision_end_token_id=248054,tie_word_embeddings=True,
        transformers_version='4.57.0.dev0',text_config=dict(attention_bias=False,attention_dropout=0.0,
        attn_output_gate=True,dtype='bfloat16',eos_token_id=248044,full_attention_interval=4,head_dim=256,
        hidden_act='silu',hidden_size=1024,initializer_range=0.02,intermediate_size=3584,
        layer_types=['linear_attention','linear_attention','linear_attention','full_attention']*6,
        linear_conv_kernel_dim=4,linear_key_head_dim=128,linear_num_key_heads=16,linear_num_value_heads=16,
        linear_value_head_dim=128,max_position_embeddings=262144,mlp_only_layers=[],model_type='qwen3_5_text',
        mtp_num_hidden_layers=1,mtp_use_dedicated_embeddings=False,num_attention_heads=8,num_hidden_layers=24,
        num_key_value_heads=2,rms_norm_eps=1e-6,tie_word_embeddings=True,use_cache=True,vocab_size=248320,
        mamba_ssm_dtype='float32',rope_parameters=dict(mrope_interleaved=True,mrope_section=[11,11,10],
        rope_type='default',rope_theta=10000000,partial_rotary_factor=0.25)),vision_config=dict(
        deepstack_visual_indexes=[],depth=12,hidden_act='gelu_pytorch_tanh',hidden_size=768,in_channels=3,
        initializer_range=0.02,intermediate_size=3072,model_type='qwen3_5',num_heads=12,
        num_position_embeddings=2304,out_hidden_size=1024,patch_size=16,spatial_merge_size=2,temporal_patch_size=2))


def tiny_config():
    c=deepcopy(official_config())
    c.update(image_token_id=2,video_token_id=3,vision_start_token_id=4,vision_end_token_id=5)
    c['text_config'].update(hidden_size=8,vocab_size=16,intermediate_size=16,num_hidden_layers=4,
        num_attention_heads=2,num_key_value_heads=1,head_dim=8,linear_conv_kernel_dim=2,
        linear_key_head_dim=2,linear_value_head_dim=2,linear_num_key_heads=1,linear_num_value_heads=1,
        layer_types=['linear_attention']*3+['full_attention'],max_position_embeddings=128,eos_token_id=1,
        rope_parameters=dict(mrope_interleaved=True,mrope_section=[1,0,0],rope_type='default',rope_theta=10000,partial_rotary_factor=0.25))
    c['vision_config'].update(depth=1,hidden_size=4,intermediate_size=8,num_heads=1,
        num_position_embeddings=4,out_hidden_size=8,patch_size=2,spatial_merge_size=1,temporal_patch_size=1)
    return c


def write_zero_shard(path, shapes, dtypes=None):
    header={'__metadata__':{'format':'pt'}};offset=0;payload=[]
    for name,shape in shapes.items():
        dtype=(dtypes or {}).get(name,dtype_for(name));size=math.prod(shape)*(4 if dtype=='F32' else 2)
        assert size<=256*1024, 'fixtures must stay tiny'
        header[name]=dict(dtype=dtype,shape=list(shape),data_offsets=[offset,offset+size])
        offset+=size;payload.append(bytes(size))
    encoded=json.dumps(header,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%8)
    path.write_bytes(struct.pack('<Q',len(encoded))+encoded+b''.join(payload))


def snapshot(root, monkeypatch):
    root.mkdir();c=tiny_config();atomic_json(root/'config.json',c)
    monkeypatch.setattr('lia_lab.qwen35_contract.CONFIG_SHA256',hashlib.sha256(canonical(c).encode()).hexdigest())
    shapes=layout(c);write_zero_shard(root/'model.safetensors',shapes)
    (root/'LICENSE').write_text('SYNTHETIC TEST FIXTURE ONLY',encoding='utf-8')
    atomic_json(root/'tokenizer_config.json',{'chat_template':'synthetic-test-only'})
    write_index(root,shapes)
    return c,shapes


def write_index(root,shapes,dtypes=None):
    size=sum(math.prod(s)*(4 if (dtypes or {}).get(n,dtype_for(n))=='F32' else 2) for n,s in shapes.items())
    atomic_json(root/'model.safetensors.index.json',dict(metadata={'total_size':size},weight_map={n:'model.safetensors' for n in shapes}))
