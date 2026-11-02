# 计划格式与工具范围

Python3脚本。预检需要Pillow，媒体审计需要OpenCV、NumPy、imageio-ffmpeg及可用FFmpeg。缺依赖先查现有项目环境，不声称运行成功，不默认下载重型模型。

## 离线预检

preflight.py输入影片计划与项目模型配置；默认同目录model_profiles.json是2026-10-03保守快照，正式调用前刷新项目配置并用--profiles指定。

```json
{
  "project_id": "demo",
  "budget_cny": 6,
  "known_extra_cost_cny": 0,
  "premium_models_allowed": [],
  "clips": [{
    "id": "scene-a",
    "model": "lec-minimax-h3-768p",
    "seconds": 12,
    "resolution": "768P",
    "max_attempts": 2,
    "prompt": "镜头1｜中景固定。成年朋友站在路灯下，望向画外，轻声说：‘明天见。’说完自然落稳。",
    "dialogues": [{"speaker": "朋友", "text": "明天见。"}],
    "references": [],
    "visible_text": []
  }]
}
```

参考包含kind、role和file或url。kind=image/video/audio；role=reference_image/reference_video/reference_audio或真实图片边界first_frame/last_frame。相对file按计划目录解析，远程可读与角色绑定由实际接入确认。

模型配置包含family、unit（second/request）、price_cny、resolution_ratios、seconds_options或min/max_seconds、planning_reference_limits（未知null），可选max_total_refs、premium、frame_reference_policy、max_prompt_characters。native_mutually_exclusive只代表明确采用的原厂规划约束。

配置currency必须是CNY；其他平台按不同币种报价时先核对当期汇率，将price_cny显式换算并记录来源/日期，不能直接把美元数字当人民币。读取公示价格不自动证明计费单位已经辨清。

--report保存结果，退出2表示计划问题。始终ready_for_paid_submission=false，不提交任务。脚本不验证剧情、素材传输或真实扣费。example_plan.json是离线示例，不是生成授权。

参考图执行与验收另按 [参考图制作](reference-images.md)。当前预检不验证GPT内置工具的实际型号、静态人物/手部正确性、视频对参考的采用效果，也不实施新的图片路线控制；这些由agent按Skill主入口核对。脚本示例价格/型号不是当前生图或视频默认选择。

用户明确要求正文允许时间轴时才可在计划设allow_prompt_timeline=true；预检脚本默认不允许时间轴，用户或目标模型需要时应显式配置。对白/画面文字的数字保留。

## 信息刷新

refresh_models.py --api-base URL --out FILE读取标准兼容目录。--api-key-env AI_VIDEO_API_KEY从进程环境读Key；仅保存id/object/owned_by，名称不证明真实原厂。

--provider simplefuture仅在simplefuture.zone地址附匿名公示价格；可选--hours 24 168及重复--model查询公开性能。只读、无私人历史、无生成，不自动改预检配置。新平台不兼容目录时按正常文档建立适配，不盲试各种路径。

partial/HTTP错误保留为缺口，不当成模型不存在。禁止Key出现在参数值、文件或日志；脚本拒绝自动重定向。

## 媒体检查

media_audit.py VIDEO --report REPORT完整解码，需要音轨加--require-audio；报告不能覆盖原件。它不检查对白、表情和剧情。

调用路径按当前技能安装目录和项目解析，不依赖旧聊天work目录。检查退出状态和报告；结构、计划、技术、内容分别报告。

## 可选制作记录检查

`python scripts/production_audit.py PROJECT_PLAN.json --report REPORT.json` 仅需Python标准库。按 [制作记录](production-records.md) 加入可选assets/beats/shots；剪辑字段按 [剪辑与审片证据](edit-evidence.md)。报告列当前指纹、过期状态和计算的字幕时间，不修改输入，不获取远程素材、不提交生成。

preflight.py发现这些字段时调用同样的结构检查，并从asset_id解析素材路径/种类、从节拍派生对白，再继续原预算/模型检查。旧计划无新增字段仍可用。引用须声明runtime、allowed_use及该镜use；未知/过期/越权引用阻止通过。仅保留在库内的过期资产会标记stale，不阻止使用无关且有效的分支。

词时间映射只覆盖按顺序拼接、正恒速、不重叠的片段。转场重叠/变速曲线等使用编辑器导出的真实映射。文件/spec指纹与覆盖检查可确定执行；画面身份、场景接触、剧情效果和音轨转写仍需实际审查。报告不能覆盖计划、配置或源素材，退出2代表检查发现问题，异常退出不算通过。
