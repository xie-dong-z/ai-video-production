# AI 视频制作 Skill

一个面向 AI 视频创作的 Agent Skill，覆盖参考素材、分镜、跨镜连续性、视频参考、镜头审片、声音剪辑和交付检查。适用于 Codex 等支持 `SKILL.md` 的环境；实际生成能力取决于所连接的工具和服务。

## 安装

将本仓库克隆到 Agent 的技能目录，例如 Codex 的 `~/.codex/skills/ai-video-production`，然后在新会话中使用 `$ai-video-production`。Claude 或其他客户端请按各自的 Skill 导入方式使用。

```bash
git clone https://github.com/xie-dong-z/ai-video-production.git ~/.codex/skills/ai-video-production
```

## 包含什么

- `SKILL.md`：任务入口与工作原则；`references/`：按需查阅的制作方法及来源。
- `scripts/preflight.py`：离线计划与预算检查。
- `scripts/production_audit.py`：资产、节拍及剪辑映射检查。
- `scripts/media_audit.py`：本地视频解码与规格检查。
- `scripts/refresh_models.py`：只读查询兼容接口的模型目录，不创建生成任务。

脚本使用 Python 3.10+；预检需要 Pillow，媒体检查还需 numpy、opencv-python、imageio-ffmpeg。按需安装 `pip install -r requirements.txt`。示例计划和价格配置仅作格式演示，**不是实时价格或平台能力保证**；正式使用前应建立自己的配置并核对当前接口。

```bash
python scripts/preflight.py scripts/example_plan.json
python scripts/production_audit.py --help
python scripts/media_audit.py --help
```

本项目不包含生成模型、托管服务、API 密钥或私人素材；不会仅凭安装 Skill 获得视频生成能力。自动识别与技术检查不能代替人工视听审片。

## 许可与致谢

本仓库自身内容采用 MIT 许可证，见 [LICENSE](LICENSE)。参考过的第三方项目及采用范围见 [融合来源](references/fusion-sources.md) 和 [参考图研究来源](references/reference-image-sources.md)；它们各自的代码、资源与许可证不因本仓库的 MIT 许可而改变。
