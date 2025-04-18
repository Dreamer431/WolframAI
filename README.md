# Wolfram Alpha 知识引擎问答系统

一个基于 Wolfram Alpha 和 DeepSeek 的智能问答系统，支持中英文自动翻译、复杂问题拆解和答案优化。

![系统界面](https://i.imgur.com/example.png)

## 🌟 功能特点

- **双语支持**：支持中英文输入，自动检测语言并翻译
- **智能问题拆解**：自动将复杂问题分解为 Wolfram Alpha 能理解的子问题
- **答案整合**：将子问题答案智能整合成完整回答
- **回答优化**：利用 DeepSeek 将专业术语转换为通俗易懂的语言
- **可视化界面**：基于 Gradio 的直观交互界面
- **两种查询模式**：
  - 原始查询：直接返回 Wolfram Alpha 的结果
  - 增强查询：拆解复杂问题，整合答案，优化表达

## 🔧 技术架构

- **知识引擎**：Wolfram Alpha API
- **大语言模型**：DeepSeek API
- **Web 界面**：Gradio
- **语言处理**：LangChain
- **环境管理**：python-dotenv

## 📋 安装步骤

### 1. 克隆代码库

```bash
git clone <仓库地址>
cd wolfram-alpha-qa-system
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API 密钥

创建 `.env` 文件，添加以下内容：

```
WOLFRAM_ALPHA_APPID=你的Wolfram_Alpha_AppID
DEEPSEEK_API_KEY=你的DeepSeek_API_Key
```

- [获取 Wolfram Alpha AppID](https://developer.wolframalpha.com/portal/myapps/)
- [获取 DeepSeek API Key](https://platform.deepseek.com/)

## 🚀 运行系统

```bash
python main.py
```

启动后，在浏览器访问 `http://localhost:7860` 即可使用系统。

## 💡 使用指南

### 基本使用

1. 在输入框中输入你的问题
2. 选择"原始查询"或"增强查询"选项卡
3. 点击"查询"按钮获取答案

### 功能说明

- **原始查询**：适合简单、直接的问题（如"地球的质量"）
- **增强查询**：适合复杂问题（如"比较不同国家的经济增长与人口变化关系"）
- **翻译开关**：可关闭自动翻译功能，直接使用英文交互

### 示例问题

- 太阳的质量
- 地球到月球的距离
- COVID-19的R0值
- y = x^2 的导数
- 法国总统的年龄
- 比较GDP和人口增长的关系

## 📝 系统优势

1. **跨越语言障碍**：即使 Wolfram Alpha 不支持中文，本系统通过自动翻译实现中文交互
2. **突破能力边界**：通过问题拆解，解决 Wolfram Alpha 无法直接回答的复杂问题
3. **优化理解体验**：将专业、技术性的回答转化为更易理解的表述
4. **灵活配置**：可根据需要开关翻译功能，适应不同用户习惯

## 📄 许可证

MIT License

## 👨‍💻 开发者

请在此处添加您的联系信息

---

**注意**：本系统需要有效的 Wolfram Alpha AppID 和 DeepSeek API Key 才能正常运行。这些 API 可能有免费使用限额，请合理使用。 