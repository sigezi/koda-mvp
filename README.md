# Koda · AI 宠物伙伴

Koda 是一个融合 AI 对话、情绪共感、宠物健康记录与成长图谱的多宠物陪伴系统。作为用户与宠物之间的 AI 桥梁，Koda 具备温柔、成长型人格，支持每日对话、自动日志识别、宠物资料管理、图表展示、情绪理解与行为建议。

## 功能特点

- 🤖 AI 对话：与 Koda 进行自然语言交流，获取宠物相关的建议和 insights
- 📝 宠物档案：管理多个宠物的基本信息，包括品种、年龄、体重等
- 📊 成长记录：记录和追踪宠物的健康、饮食和情绪状态
- 📈 数据可视化：通过图表直观展示宠物的成长轨迹
- 🎯 智能分析：基于 AI 的日志分析和行为建议

## 技术栈

- Frontend: Streamlit
- Backend: Python
- AI: OpenAI API
- Database: Supabase
- Data Visualization: Plotly

## 安装与运行

1. 克隆项目
```bash
git clone https://github.com/yourusername/koda-mvp.git
cd koda-mvp
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
创建 `.env` 文件并添加以下配置：
```
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
USER_ID=your_user_id
```

4. 运行应用
```bash
streamlit run app.py
```

## 项目结构

```
koda-mvp/
├── app.py              # 主应用入口
├── components/         # UI 组件
│   ├── chat.py        # 聊天界面
│   ├── log_display.py # 日志显示
│   └── pet_profile.py # 宠物档案
├── utils/             # 工具函数
│   ├── connection.py  # 数据库连接
│   ├── errors.py      # 错误处理
│   └── types.py       # 类型定义
├── requirements.txt   # 项目依赖
└── README.md         # 项目文档
```

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。在提交 PR 之前，请确保：

1. 代码符合 PEP 8 规范
2. 添加了必要的测试
3. 更新了相关文档

## 许可证

MIT License 