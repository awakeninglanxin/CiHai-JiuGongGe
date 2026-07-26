
# 慈海九宫格 v1-v18 风格迭代历史

## v1-v5: 早期基础风格 (2026-06-11 ~ 2026-07-12)
- **脚本**: gen_individual_portraits.py / gen_individual_v2.py / gen_missing_deities*.py
- **特点**: 每个 code 使用 NODE_PROMPTS 字典中的模板句作为 base prompt
- **格式**: 长句描述 + 唯一后缀（cosmic destiny / quantum signature / astral aura 等）
- **最终合成**: "{base_prompt}, {suffix}, ultra detailed digital art, cinematic lighting, divine portrait"
- **分辨率**: 1024x1024
- **输出**: 输出到 generated-images/individual/ 目录
- **优点**: 简洁优雅，每个 code 都有独特描述
- **缺点**: 缺少正面特写（portrait）、光线细节、眼睛描述

## v6: 第一批肖像升级 (2026-07-12)
- **脚本**: gen_style_upgrade_v7.py → v8 → v9
- **升级**: 加入更多视觉关键词（dramatic, epic, masterpiece）
- **保持**: NODE_PROMPTS 模板不变

## v7-v9: 自动化批量生成 (2026-07-13)
- **脚本**: gen_v9_auto.py, gen_v9_loop.py
- **变化**: 统一生成格式，批量处理
- **风格**: 延续 v1-v6 的长句描述风格

## v10-v13: 并发优化 + 提示词打磨 (2026-07-13)
- **脚本**: gen_v10_concurrent.py → v11 → v12 → v13
- **变化**: 引入并发生成，提升速度
- **风格**: 继续使用长句描述 + 后缀

## v14-v15: 重大改版 — Portrait 特写 (2026-07-14~15)
- **脚本**: gen_v14.py, gen_v15.py, gen_v15_regen.py
- **变化**: 从全景全身像改为半身特写肖像（portrait of...）
- **新风格**: 强调面部细节、眼睛、光影、材质感
- **关键字**: "masterpiece, best quality, 8k ultra detailed, sharp focus"
- **结构**: 角色描述 + 配饰 + 服装 + 姿态 + 背景 + 通用后缀

## v16: 全量重生成 (2026-07-16)
- **脚本**: gen_v16_all_regen.py
- **变化**: 对所有 799 张图重新生成，统一风格
- **风格**: portrait 特写 + 8k 画质 + 戏剧性光线

## v17: 质量管控 + 问题检测 (2026-07-15~16)
- **脚本**: check_quality.py, check_quality_all.py
- **变化**: 引入 AI 质检，检测眼睛不对称、模糊、皮肤质感、手势对称性等
- **结果**: 生成 quality_scan_v17.json，识别 713 张问题图

## v18: 9种族差异化风格 (2026-07-17)
- **脚本**: gen_v18_starstyle_regen.py
- **变化**: 每个节点（1-9）对应一个星际种族，各有独立 prompt 风格
  - Node 1: 灰人联邦 Grey — 硅基晶体、银肤
  - Node 2: 艾莎莎尼 — 完美对称、中性美
  - Node 3: 天狼星 — 古埃及、深蓝
  - Node 4: 猎户座 — 伏羲女娲风格（Chinese deity）
  - Node 5: 雅耶奥 — 量子态、虹彩
  - Node 6: 昴宿星 — 水晶自然光、蝴蝶翼
  - Node 7: 阿努纳奇 — 壮硕黄金、美索不达米亚
  - Node 8: 地球/盖亚 — 大地藤蔓
  - Node 9: 大角星 — 几何蓝紫
- **问题**: 138 张用户明确表示不喜欢的图

## 总结
- v1-v9: 长句描述 + 后缀（全身像）
- v14-v16: Portrait 特写 + 8k 画质
- v17: 质量管控
- v18: 9种族差异化（当前）

用户现在要回退到 v1 的早期风格。
