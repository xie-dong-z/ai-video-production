# 参考图方法来源与取舍

2026-10-06查阅。这里保存可复核的来源与采用范围，不是模型质量排名。制作读取 [参考图制作](reference-images.md) 即可，不要求每次重新搜全平台。外部文件作为研究资料，不安装其工具或执行其代码；已安装imagegen承担内置图像执行。

## 用户当前选择优先

图片生成路线、型号及分辨率由用户要求与当前可用工具决定。视频通常在Seedance 2.0、Seedance 2.5和MiniMax H3中按情况和预算选择。社区的多模型路由、CLI、训练、默认重试与收费服务不随方法一并采用。

本会话内置imagegen工具可接收提示、引用图和透明背景，但没有暴露model/size/quality选择字段；实际型号未披露时不能声称已锁2.5或某子型号。此为本次工具接口观察，新会话重新核实际参数。

## 官方资料

- [OpenAI 图像提示指南](https://developers.openai.com/api/docs/guides/image-prompting)：参考角色、保留与变化分离、局部编辑与实际输出复核。API参数与当前客户端可选参数需分别核对。
- [OpenAI图像工具说明](https://developers.openai.com/api/docs/guides/tools-image-generation)：API图像工具的model选择与本会话内置工具schema是不同层级。不能据API文档宣称桌面内置入口已支持同样控制。
- [Runway人物参考指南](https://help.runwayml.com/hc/en-us/articles/40042718905875-Creating-with-Gen-4-Image-References)：采用中性表情、均匀照明、分项迭代。引用数量、@标签与平台功能不迁移为GPT参数。
- [Runway高级参考案例](https://help.runwayml.com/hc/en-us/articles/41170686463635-Advanced-References-Use-Cases)：采用布局草图区分构图与视线、主体/道具/场景分工。标注只作辅助，生成并检查无标注最终镜头图。案例方法应用到GPT仍需实图验证。
- [Runway图生视频指南](https://help.runwayml.com/hc/en-us/articles/48324313115155-Image-to-Video-Prompting-Guide)：输入图的模糊脸与手部瑕疵可能在视频中加强；画面隐含动作应与文本一致。其首帧语义不推广到所有普通参考入口。
- [BytePlus Seedance 2.0提示指南](https://docs.byteplus.com/vi/docs/modelark/seedance-2-0-prompt-guide)：官方站检索返回正文的身份漂移排查建议独立单人照片，并指出多视图可能被当成多主体。动态页open未完整提取正文，未将它记为全文精读。采用该模型的人物输入建议，不禁止所有模型/人工规划使用角色总览。
- [Adobe构图参考说明](https://helpx.adobe.com/firefly/web/work-with-images/generate-images/match-image-composition-to-reference-image.html) 与 [风格参考说明](https://helpx.adobe.com/firefly/web/work-with-images/generate-images/reference-images-for-styling.html)：采用结构/深度与视觉风格分离的职责，不迁移Firefly滑块或权重。
- [Google Flow素材建议](https://support.google.com/flow/answer/16353334?co=GENIE.Platform%3DDesktop&hl=en)：采用干净主体背景、场景/风格图避免多余人物、参考与文字不冲突。只借素材准备方法，不切换Google模型或继承其角色库/账号能力。

## Skill资料

- [OpenAI imagegen](https://github.com/openai/skills/blob/main/skills/.system/imagegen/SKILL.md) 及 [prompting](https://github.com/openai/skills/blob/main/skills/.system/imagegen/references/prompting.md)：采用用途/参考角色、局部编辑保留项、结果检查和另存版本。遵循用户明确选定的工具与型号。
- [Emily2040 Nano Banana Image Skill](https://github.com/Emily2040/nano-banana-image-skill)：查读入口、orchestrator及reference-binding、preservation、edit-delta、continuity、composition-camera、lighting-materials、slop-scrubber、evidence-discipline。采用具体摄影/光影和固定项/允许变化，改为GPT自然语言；不继承Nano Banana选型、专属JSON、陌生接口参数或宣传效果。
- [Skill Atlas image-generation-enhanced](https://github.com/skillatlas/skills/blob/main/skills/image-generation-enhanced/SKILL.md)：采用参考职责、图像视觉层次、逐图检查与针对性修改。不继承OpenRouter前置条件、其他模型推荐或每次返修确认；JSON只是整理格式之一，不作为改善质量的已证实因果。
- [Baoyu image-gen](https://github.com/JimLiu/baoyu-skills/blob/main/skills/baoyu-image-gen/SKILL.md) 与 [角色定义模板](https://github.com/JimLiu/baoyu-skills/blob/main/skills/baoyu-comic/references/character-template.md)：采用认可身份原图、避免泛化五官重设计，以及身份/造型/表情分工。漫画多格总览不默认传入Seedance，不复制其CLI/压缩/重试/模型配置。
- [Genielabs character-consistency](https://github.com/GenielabsOpenSource/style-consistency-ai/blob/main/skills/character-consistency/SKILL.md)，重点 [最近参考](https://github.com/GenielabsOpenSource/style-consistency-ai/blob/main/skills/character-consistency/references/approach-2-references.md) 与 [分步流程](https://github.com/GenielabsOpenSource/style-consistency-ai/blob/main/skills/character-consistency/references/approach-4-pipelines-routing.md)：采用按目标姿态/角度选最近认可图、身份/复杂场景按需拆分和追溯中间漂移。两步遵循已授权GPT图片路线，不自动多模型切换、训练LoRA或构建十几张数据集，且不把作者效果判断当本项目实测。
- [bqcl character-image-prompt](https://github.com/bqcl/character-image-prompt)：查读core、consistency、reference-image-analysis。采用身份/造型/场景/风格分离、现有卡按最新要求调用与变化范围明确。记录融入现有项目，不强制每次分析报告后等批准，也不强制英文关键词、固定seed或十一个模板段落。
- [Nanoleava directing-image-prompts](https://github.com/Nanoleava/directing-image-prompts)，重点 [visual-mechanisms](https://github.com/Nanoleava/directing-image-prompts/blob/main/references/visual-mechanisms.md)：采用把情绪转成可见机位、占比、空间、光线和材料机制，保留用户真实审美目标。不固定某组视觉机制为唯一表达，不执行外部提示词lint脚本。

## 分歧处理与验证边界

部分资料支持以上轮生成图继续编辑，另一些强调避免派生身份漂移；本Skill采用“认可原始身份源持续锚定 + 已检查派生图作为编辑底图”。多视角总览可用于人工设计或经验证入口，Seedance 2.0视频人物输入优先独立单人。

外部接口能力、社区经验、用户约定与项目实测分别记。镜头图目标2048×1152等尺寸只是制作目标，内置工具真实返回及视频通道传输仍需核实。结构/引用/离线预检通过不证明新图片、真人声纹、视频动作或新会话端到端已通过。
