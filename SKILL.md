---
name: ai-video-production
description: 制作剧情视频及人物、场景和镜头参考图，分析视频参考，编排分镜、生成审片，完成剪辑与声音字幕交付。按任务选择可用工具及模型。
metadata:
  short-description: AI视频制作、连续性与审片工作流
---

# AI视频制作工作流

从用户的任务、素材、预算和已授权工具出发，按需完成参考图、分镜、镜头生成、剪辑、声音和交付。用户当前要求优先；不要把示例中的平台、型号、价格或个人偏好当成通用规则。

## 按任务读取

- 写提示词、评审分镜：[提示词与参考素材](references/prompts-and-references.md)。
- 人物、场景、镜头参考图：[参考图制作](references/reference-images.md)。
- 视频参考与动作/运镜复刻：[视频参考](references/video-references.md)。
- 跨镜连续性与资产状态：[制作记录](references/production-records.md)。
- 从剧情制作影片：[制作流程](references/production.md)。
- 剪辑与声音：[后期与验收](references/post-production.md)；涉及对白和字幕切点时另读[剪辑证据](references/edit-evidence.md)。
- 平台和模型适配：[平台适配](references/provider-adaptation.md)。
- 按反馈返修：[内容审片与迭代](references/review-and-iteration.md)。

## 关键约定

1. 区分角色身份图、造型图、场景参考、普通参考与真实首尾帧。先核验目标模型的实际字段和参考能力，不把其他平台功能直接迁移。
2. 维护人物、服装、空间、道具、光线和镜头的连续性；只对受影响的部分返修。
3. 使用用户指定的视觉、声音和图像尺寸要求；以实际输出和内容验收，不把提示词中的“4K”当作输出规格。
4. 在授权预算内记录预留、实际收费、退款、任务ID和状态。提交结果不明时先查询任务或账单，避免重复创建收费任务。
5. 声音优先保留用户认可的原声；对白、音效和音乐分别处理。自动转写是辅助证据，不能代替实际听审。
6. 技术解码通过不等于人物、表演、镜头和对白都正确。完整观察并记录可确认的证据，明确未验证的范围。
7. 提示词是否使用时间轴由用户和目标模型决定。预检脚本默认禁止提示词正文中的时间轴；需要时在计划中显式设置 `allow_prompt_timeline=true`。
8. 视频或图片生成、第三方上传和付费操作应处于用户授权范围；不记录密钥，不把用户的私人素材或项目记录当成示例分发。

## 工具与限制

- `scripts/preflight.py` 离线检查制作计划、素材与预算。`scripts/model_profiles.json` 是历史示例，不代表当前报价或能力，使用前须核对并替换为自己的配置。
- `scripts/production_audit.py` 离线检查资产依赖、节拍覆盖和剪辑映射。
- `scripts/media_audit.py` 完整解码本地视频并检查规格及音轨，不代替视听审片。
- `scripts/refresh_models.py` 只读查询兼容接口的模型目录；不会生成视频。凭据仅通过环境变量传入。
- 各脚本、格式及约束见[计划格式与工具](references/plans-and-tools.md)。
- 本仓库不提供视频生成后端、账号、模型权重或API密钥。实际模型、客户端与接口能力以对应平台当前资料和实际返回为准。
- 方法参考及取舍见[融合来源](references/fusion-sources.md)和[参考图研究来源](references/reference-image-sources.md)。第三方项目各自的许可证独立适用。
