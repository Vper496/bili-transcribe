# bili-transcribe / B站视频转录工具

[English](README_EN.md)

[![GitHub Stars](https://img.shields.io/github/stars/Vper496/bili-transcribe?style=flat)](https://github.com/Vper496/bili-transcribe/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/Vper496/bili-transcribe?style=flat)](https://github.com/Vper496/bili-transcribe/issues)
[![License](https://img.shields.io/github/license/Vper496/bili-transcribe?style=flat)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/Vper496/bili-transcribe?style=flat)](https://github.com/Vper496/bili-transcribe/commits/master)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat)](https://www.python.org/)

下载 B站视频音频，通过 faster-whisper 转录为 markdown。BV号进去，markdown 出来。

## 功能

- **一个 BV 号全自动**：B站 API 下载音频 + Whisper 转录，一步到位
- **CDN 自动降级**：高码率 CDN 节点被墙时自动尝试低码率流，无需手动切换
- **纯 CPU 运行**：faster-whisper small 模型 + int8 量化，无需显卡（模型 ~500MB，首次下载后缓存）
- **~4.7 倍实时**：15 分钟视频约 3 分钟处理完

## 环境要求

- Python 3.10+
- ffmpeg（通过 `imageio-ffmpeg` 内置，无需系统安装）

## 安装

```bash
pip install -r requirements.txt
```

首次运行会下载 Whisper 模型（约 500MB）。如果 HuggingFace 被墙：

```bash
# Windows (PowerShell)
$env:HF_ENDPOINT = "https://hf-mirror.com"

# Linux / macOS
export HF_ENDPOINT=https://hf-mirror.com
```

## 使用方法

两步走，顺序执行：

```bash
# 第一步：下载音频（B站 API → WAV）
python download_audio.py BV1s4411C7hk

# 第二步：转录（WAV → markdown + 纯文本）
python transcribe_audio.py \
  "scripts/transcripts/BV1s4411C7hk_audio.wav" \
  "视频标题" \
  "BV1s4411C7hk" \
  "935"
```

输出文件：
- `{bvid}.md` — 带 frontmatter 元数据的 markdown（标题、来源、作者、时长）
- `{bvid}.txt` — 纯文本

## 原理

```
Video(bvid) → B站 API → DASH 音频 URL（按码率升序排列）
                          ↓
                    逐个尝试不同码率直到下载成功
                    （不同码率走不同 CDN，低码率可达性最好）
                          ↓
                    下载 .m4s → 转换为 16kHz 单声道 WAV
                          ↓
                    faster-whisper small（中文，beam=5，VAD 过滤）
                          ↓
                    .md + .txt
```

## 常见问题

| 现象 | 原因 | 解决 |
|------|------|------|
| `python: command not found`（Windows）| Windows App Installer 的重定向器被拦截 | 用 Python 的完整路径执行 |
| HuggingFace 下载超时 | hf.co 被墙 | `export HF_ENDPOINT=https://hf-mirror.com` |
| 412 Precondition Failed | B站 API 需要 WBI 签名 | `bilibili-api-python` 库自动处理 |
| CDN 超时（`mcdn.bilivideo.cn`）| 高码率音频走被墙的 CDN 节点 | 脚本自动降级到低码率（不同 CDN） |
| 视频无 CC 字幕 | 上传者未提供字幕 | 语音识别（faster-whisper）兜底 |

## 踩坑备忘

这些是开发过程中实际遇到并解决的问题，供参考：

1. **Windows Python 路径**：Windows 下 `python` 命令可能指向 Microsoft Store 重定向器（exit code 49），必须用实际安装路径
2. **HuggingFace 被墙**：国内需通过 `hf-mirror.com` 镜像下载模型，否则连接超时
3. **B站 CDN 分线路**：不同码率的音频流走不同 CDN 节点（`mcdn.bilivideo.cn` vs `upos-sz-mirrorcos.bilivideo.com`），高码率走被墙节点，低码率走可用节点
4. **音频码率足够**：43kbps 的低码率对 Whisper 语音识别完全够用，不必追求高音质
5. **ffmpeg 无需系统安装**：`imageio-ffmpeg` 自带 ffmpeg 二进制，省去环境配置
6. **WAV 文件很大**：15 分钟视频的 WAV 约 30MB，转录后自动清理
7. **VAD 节省时间**：开启 VAD 过滤后实际转录时长约为视频时长的 92%（跳过静音段）

## 备注

- 默认下载最低码率音频（43-46kbps），对 Whisper 足够且 CDN 可达性最好
- WAV 文件转录后自动删除
- small 模型首次下载后本地缓存，后续直接使用

## 许可证

MIT
