# slider-captcha-solver

[English](README.md) | [中文](README.zh-CN.md)

一个**滑块验证码自动化**研究工具库——OCR 缺口定位、类人拖动轨迹生成、网络抓包解析、受控对照实验。沉淀自一次针对某商业滑块验证码厂商的真实、端到端逆向实践。

> **免责声明**：本项目仅用于合法的安全研究、逆向工程学习与自动化技术交流。所有可定位目标的细节（站点域名、厂商名称、OCR 凭证、CSS 类名、API 路径）均已脱敏，仅保留可复用的算法结论。**请勿对未获授权的任何目标使用本项目。**

## 为什么做这个

大多数滑块验证码的文章，止步于"找到了缺口、拖一下"。真正决定成败、也是本仓库想展示的，是两件容易被忽略的事：

1. **拖动距离 ≠ 缺口左边缘。** 需要一个标定过的偏移修正（本例为 `+10px`），而且它是"每目标实测"的经验常数，不是协议里读出来的值。
2. **轨迹形态比距离更关键。** 一条对称的"缓入缓出"曲线、带过冲回弹和 y 轴抖动的"拟人"轨迹，会在 `check` 请求发出前就被前端丢弃；而真实人类"快冲、慢调"的曲线反而被接受。

本仓库把**可复用的机制**（缺口定位、轨迹生成/分析、拖动执行、抓包解析、受控实验）抽成与站点无关的通用库，把**站点特定的结论**（协议、标定 offset、采集到的轨迹）收敛进脱敏的案例文档。

## 特性

- **`track`** — 把一段真人拖动缩放到任意距离；按三分段统计速度、停顿点与 y 轴噪声。
- **`ocr`** — 可插拔的缺口定位，适配任何"传 base64、返回框坐标"的 OCR 接口。
- **`drag`** — 通过 CDP 鼠标事件（Playwright `page.mouse`）驱动滑块。
- **`capture`** — 收集 JSONP 包裹的响应并按正则提取字段。
- **`trace_recorder`** — 从页面采集真人拖动，且不怕页面导航清空。
- **`probe`** — "一次只变一个变量"的 session vs IP 受控实验。
- **`dom`** — 导出滑块几何信息，判断背景图是否为原始像素尺寸。

## 快速开始

```bash
pip install -e .
# 或带上测试依赖：
pip install -e ".[dev]"
pytest
```

先启动一个开启远程调试的浏览器：

```bash
msedge --remote-debugging-port=9222
```

然后跑端到端 demo（先填好 `examples/profile_slider_vendor.py` 里的脱敏占位）：

```bash
python examples/solve_demo.py
```

## 架构

```
slider_solver/            # 与站点无关的通用库（零厂商硬编码）
  track.py                # 轨迹缩放 + 分析（纯逻辑，有测试）
  ocr.py                  # 可插拔缺口定位
  capture.py              # JSONP 解包 + 字段提取
  drag.py                 # CDP 鼠标拖动
  trace_recorder.py       # 页面内轨迹采集（导航安全）
  probe.py                # session vs IP 受控实验
  dom.py                  # 滑块几何导出
  cli.py                  # analyze / trace / probe / solve 入口
examples/                 # 站点特定、已脱敏
  profile_slider_vendor.py  # 脱敏的目标配置 + 保留的算法结论
  solve_demo.py             # 端到端装配
tests/                    # 纯逻辑测试
docs/
  case-study.md           # 完整复盘（英文）
  case-study.zh-CN.md     # 完整复盘（中文）
```

## 工作原理（闭环）

```
抓取挑战响应        ->  提取背景图 URL
下载背景图          ->  OCR 定位缺口左边缘 x1
拖动距离 = x1 + 偏移 ->  缩放采集到的轨迹
page.mouse 驱动滑块 ->  前端 check -> 服务端 verify
```

## 诚实边界

- 这是**前端事件模拟**，不是算法级破解：厂商前端的 `validate` 由它自己计算，我们并未伪造。
- `+10` 偏移与采集轨迹是**针对某一目标、某一时刻标定的快照**，厂商一换挑战样式就可能失效，需按目标重新标定（见案例文档）。
- 缺口定位依赖**第三方 OCR 服务**，本仓库不含自研检测器。
- 服务端 `verify` 是**间接确认**的（页面跳转到完整内容），因为站点到厂商的 verify 调用浏览器不可见。
- 只有纯逻辑部分（`track`、`capture`）有测试覆盖；浏览器路径需要真实的、已授权的目标。

完整时间线、失败经历、以及 offset 和轨迹是如何标定的，见 `docs/case-study.zh-CN.md`。

## License

MIT — 见 [LICENSE](LICENSE)。
